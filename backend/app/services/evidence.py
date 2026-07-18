"""Grounded evidence generation — PR-06. Design: docs/AI_DESIGN.md §4.

Pipeline:
1. CODE selects allowed quotes (from profile session) and allowed stats (from market).
2. CODE computes true counterfactual via re-score (matching).
3. Optional LLM verbalizes using only those inputs.
4. CODE validates: quotes belong to session; every digit in market text is in stats;
   fail → deterministic Vietnamese templates.

Never invent salary/demand numbers. Null / low_confidence → omit or disclaimer.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import get_settings
from app.models.schemas import (
    MarketStats,
    Profile,
    Why,
    WhyFromMarket,
    WhyFromYou,
)
from app.prompts.evidence import (
    EVIDENCE_PROMPT_VERSION,
    EVIDENCE_SYSTEM,
    build_evidence_user_payload,
)
from app.services.llm import LLMError, chat_json

log = logging.getLogger("evidence")

# Integer/decimal tokens in generated text (no scientific notation needed for VN UI).
_NUM_RE = re.compile(r"(?<![A-Za-z_])\d+(?:[.,]\d+)?")


class EvidenceLLMOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    from_you: list[WhyFromYou] = Field(default_factory=list)
    from_market: list[WhyFromMarket] = Field(default_factory=list)
    counterfactual: str = ""


# ---------- selection (code authority) ----------


def collect_allowed_quotes(profile: Profile) -> list[str]:
    """Quotes that may appear in why.from_you — must come from this session profile."""
    quotes: list[str] = []
    seen: set[str] = set()

    def add(q: str) -> None:
        t = (q or "").strip()
        if not t or _looks_like_injection(t):
            return
        key = t.lower()
        if key in seen:
            return
        seen.add(key)
        quotes.append(t[:240])

    for eq in profile.evidence_quotes:
        add(eq.quote)
    for s in profile.skills:
        add(s.source_quote)
        if s.name and s.source_quote:
            add(s.name)
    for e in profile.experiences:
        add(e.source_quote)
        add(e.title)
    for interest in profile.interests:
        add(interest)
    if profile.job_goal:
        add(profile.job_goal)
    return quotes


def select_quote_for_career(profile: Profile, career: dict) -> str:
    """Pick the best session quote; prefer skill source_quotes and career skill overlap."""
    allowed = collect_allowed_quotes(profile)
    if not allowed:
        return "hồ sơ hiện tại của bạn"

    # Prefer order: evidence_quotes → skill source_quotes → experience → interests
    preferred: list[str] = []
    for eq in profile.evidence_quotes:
        if eq.quote and not _looks_like_injection(eq.quote):
            preferred.append(eq.quote.strip()[:240])
    for s in profile.skills:
        if s.source_quote and not _looks_like_injection(s.source_quote):
            preferred.append(s.source_quote.strip()[:240])
    for e in profile.experiences:
        if e.source_quote and not _looks_like_injection(e.source_quote):
            preferred.append(e.source_quote.strip()[:240])

    top_skills = [
        str(s).lower() for s in ((career.get("seed_market") or {}).get("top_skills") or []) if s
    ]
    title = (career.get("title") or "").lower()
    candidates = preferred or allowed
    best = candidates[0]
    best_score = -1
    for q in candidates:
        ql = q.lower()
        score = 0
        for sk in top_skills:
            if sk and sk in ql:
                score += 3
        for tok in re.findall(r"[\wÀ-ỹ]{3,}", title):
            if tok in ql:
                score += 1
        # prefer concrete longer quotes over single-word interests
        score += min(3, len(q) // 20)
        if score > best_score:
            best_score = score
            best = q
    return best[:200]


def market_stats_dict(market: MarketStats) -> dict[str, Any]:
    """Flat stats object passed to validator / LLM — only real fields."""
    d: dict[str, Any] = {
        "demand_count_90d": market.demand_count_90d,
        "entry_level_count_90d": market.entry_level_count_90d,
        "window_days": 90,
        "low_confidence": market.low_confidence,
    }
    if market.salary_p25_trieu is not None:
        d["salary_p25_trieu"] = market.salary_p25_trieu
    if market.salary_p50_trieu is not None:
        d["salary_p50_trieu"] = market.salary_p50_trieu
    if market.salary_p75_trieu is not None:
        d["salary_p75_trieu"] = market.salary_p75_trieu
    if market.salary_sample_count:
        d["salary_sample_count"] = market.salary_sample_count
    # Trend only when not low-confidence for claim use
    if market.trend_pct is not None and not market.low_confidence:
        d["trend_pct"] = market.trend_pct
    return d


def allowed_number_tokens(stats: dict[str, Any]) -> set[str]:
    """All numeric spellings that may appear in market evidence text."""
    tokens: set[str] = set()
    for v in stats.values():
        if isinstance(v, bool):
            continue
        if isinstance(v, int):
            tokens.add(str(v))
        elif isinstance(v, float):
            # both 12 and 12.0 style
            if v == int(v):
                tokens.add(str(int(v)))
            tokens.add(str(v))
            tokens.add(f"{v:g}")
            # Vietnamese UI sometimes uses comma decimal
            tokens.add(str(v).replace(".", ","))
    return tokens


def extract_number_tokens(text: str) -> list[str]:
    found = _NUM_RE.findall(text or "")
    # normalize comma decimals to a comparable form; keep original for membership
    return found


def numbers_grounded(text: str, allowed: set[str]) -> bool:
    """True iff every number token in text is allowed (or empty text)."""
    if not text:
        return True
    # Expand allowed with simple variants
    expanded = set(allowed)
    for a in list(allowed):
        expanded.add(a.replace(",", "."))
        expanded.add(a.replace(".", ","))
        if a.endswith(".0"):
            expanded.add(a[:-2])
    for tok in extract_number_tokens(text):
        variants = {tok, tok.replace(",", "."), tok.replace(".", ",")}
        if tok.endswith(".0"):
            variants.add(tok[:-2])
        if not variants & expanded:
            return False
    return True


def quote_belongs(quote: str, allowed_quotes: list[str]) -> bool:
    q = (quote or "").strip().lower()
    if not q:
        return False
    for a in allowed_quotes:
        al = a.strip().lower()
        if q == al or q in al or al in q:
            return True
    return False


def _looks_like_injection(text: str) -> bool:
    t = text.lower()
    return any(
        b in t
        for b in (
            "ignore previous",
            "system:",
            "api_key",
            "you are dan",
            "root_access",
            "sk-",
        )
    )


# ---------- template fallback (always grounded) ----------

# Below this, a profile carries essentially no concrete personal signal (no sourced
# skill, no interest, no dimension meaningfully above zero) — ranking still degrades
# gracefully to a market-led order (matching.py), but the evidence text must not claim
# a personalization that isn't there (ethics/anti-overclaim: ranking honesty matters as
# much as number honesty).
_LOW_SIGNAL_THRESHOLD = 0.15


def signal_strength(profile: Profile) -> float:
    """Rough 0..1 measure of how much concrete personal signal a profile carries.
    Only used to phrase evidence honestly for a near-blank profile — never touches scoring."""
    sourced_skills = sum(1 for s in profile.skills if (s.source_quote or "").strip())
    interests = len(profile.interests)
    max_dim = max(profile.dimensions.values(), default=0.0)
    raw = (
        min(1.0, sourced_skills / 2.0) * 0.4
        + min(1.0, interests / 2.0) * 0.3
        + min(1.0, float(max_dim)) * 0.3
    )
    return round(raw, 3)


def template_why(
    *,
    profile: Profile,
    career: dict,
    market: MarketStats,
    counterfactual: str,
) -> Why:
    quote = select_quote_for_career(profile, career)
    title = career.get("title") or "nghề này"
    # PR-10: slightly more specific reason using skills/interests when available
    skill_hint = next((s.name for s in profile.skills if s.source_quote), None)
    interest_hint = profile.interests[0] if profile.interests else None
    if skill_hint:
        reason = (
            f"bạn đã có bằng chứng «{skill_hint}» — tín hiệu này khớp với hướng {title}"
        )
    elif interest_hint:
        reason = (
            f"sở thích «{interest_hint}» trong hồ sơ gợi ý bạn có thể hợp với {title}"
        )
    elif signal_strength(profile) < _LOW_SIGNAL_THRESHOLD:
        # Honest framing: don't claim a personal-fit story the profile can't back up yet.
        reason = (
            f"hồ sơ hiện chưa có nhiều tín hiệu cụ thể — gợi ý {title} chủ yếu dựa trên "
            "dữ liệu thị trường; trò chuyện thêm để gợi ý cá nhân hoá hơn"
        )
    else:
        reason = f"phù hợp với hướng {title} dựa trên điều bạn đã chia sẻ trong hồ sơ"
    from_you = [WhyFromYou(quote=quote, reason=reason)]

    stats = market_stats_dict(market)
    from_market: list[WhyFromMarket] = []

    demand = stats.get("demand_count_90d")
    if demand is not None:
        from_market.append(
            WhyFromMarket(
                stat=f"{demand} tin tuyển trong {stats['window_days']} ngày (snapshot)",
                stat_key="demand_count",
            )
        )

    # Salary only when present (and sample count not forcing null policy)
    p25, p50, p75 = (
        stats.get("salary_p25_trieu"),
        stats.get("salary_p50_trieu"),
        stats.get("salary_p75_trieu"),
    )
    sample = int(stats.get("salary_sample_count") or market.salary_sample_count or 0)
    if p50 is not None and sample >= 5:
        if p25 is not None and p75 is not None:
            stat = f"Lương quan sát khoảng {p25}–{p75} triệu, trung vị {p50} triệu"
        else:
            stat = f"Lương trung vị quan sát khoảng {p50} triệu"
        from_market.append(WhyFromMarket(stat=stat, stat_key="salary"))
    elif market.low_confidence or sample < 5:
        # no invented salary — optional soft note without digits beyond demand
        pass

    if "trend_pct" in stats and not market.low_confidence:
        trend = stats["trend_pct"]
        from_market.append(
            WhyFromMarket(
                stat=f"Xu hướng tin tuyển thay đổi khoảng {trend}% giữa hai nửa cửa sổ",
                stat_key="trend",
            )
        )
    elif market.low_confidence:
        from_market.append(
            WhyFromMarket(
                stat="Dữ liệu thị trường còn hạn chế — nên xem số demand như tham khảo",
                stat_key="demand_count",
            )
        )

    # Final grounding pass on templates (must pass)
    allowed_nums = allowed_number_tokens(stats)
    safe_market: list[WhyFromMarket] = []
    for item in from_market:
        if numbers_grounded(item.stat, allowed_nums) or not extract_number_tokens(item.stat):
            safe_market.append(item)
    if not safe_market and demand is not None:
        safe_market.append(
            WhyFromMarket(
                stat=f"{demand} tin tuyển (snapshot)",
                stat_key="demand_count",
            )
        )

    return Why(
        from_you=from_you,
        from_market=safe_market,
        counterfactual=counterfactual,
    )


def validate_why(
    why: Why,
    *,
    allowed_quotes: list[str],
    stats: dict[str, Any],
    counterfactual_fact: str,
) -> Why | None:
    """Return sanitized Why or None if unrecoverable."""
    allowed_nums = allowed_number_tokens(stats)

    # from_you: quotes must belong
    safe_you: list[WhyFromYou] = []
    for item in why.from_you:
        if _looks_like_injection(item.quote) or _looks_like_injection(item.reason):
            continue
        if not quote_belongs(item.quote, allowed_quotes) and item.quote != "hồ sơ hiện tại của bạn":
            # try salvage: if reason ok but quote bad, skip item
            continue
        safe_you.append(item)
    if not safe_you and allowed_quotes:
        safe_you = [
            WhyFromYou(
                quote=allowed_quotes[0][:200],
                reason="dựa trên điều bạn đã chia sẻ trong hồ sơ",
            )
        ]
    elif not safe_you:
        safe_you = [
            WhyFromYou(
                quote="hồ sơ hiện tại của bạn",
                reason="gợi ý mang tính tham khảo theo hồ sơ hiện có",
            )
        ]

    safe_market: list[WhyFromMarket] = []
    for item in why.from_market:
        if _looks_like_injection(item.stat):
            continue
        if extract_number_tokens(item.stat) and not numbers_grounded(item.stat, allowed_nums):
            continue
        if item.stat_key not in (
            "demand_count",
            "salary",
            "trend",
            "entry_level",
            "source",
        ):
            # keep only known keys
            continue
        safe_market.append(item)

    # Counterfactual: prefer code fact if LLM drifts with ungrounded numbers
    cf = (why.counterfactual or "").strip() or counterfactual_fact
    if extract_number_tokens(cf) and not numbers_grounded(cf, allowed_nums | {t for t in extract_number_tokens(counterfactual_fact)}):
        cf = counterfactual_fact
    if not cf:
        cf = counterfactual_fact or "Nếu hồ sơ đổi, gợi ý có thể thay đổi — chỉ mang tính tham khảo."

    if not safe_market:
        return None
    return Why(from_you=safe_you, from_market=safe_market, counterfactual=cf)


def _try_llm_why(
    *,
    career_title: str,
    allowed_quotes: list[str],
    stats: dict[str, Any],
    counterfactual_fact: str,
) -> Why | None:
    settings = get_settings()
    if not settings.chat_api_key or settings.demo_mode == "replay":
        return None
    try:
        payload = build_evidence_user_payload(
            career_title=career_title,
            allowed_quotes=allowed_quotes,
            allowed_stats=stats,
            counterfactual_fact=counterfactual_fact,
        )
        out = chat_json(
            EVIDENCE_SYSTEM,
            [{"role": "user", "content": payload}],
            EvidenceLLMOut,
            max_retries=1,  # one repair retry inside gateway; then we template
        )
        why = Why(
            from_you=out.from_you,
            from_market=out.from_market,
            counterfactual=out.counterfactual or counterfactual_fact,
        )
        return validate_why(
            why,
            allowed_quotes=allowed_quotes,
            stats=stats,
            counterfactual_fact=counterfactual_fact,
        )
    except LLMError as exc:
        log.warning("evidence LLM fallback: %s", type(exc).__name__)
        return None
    except Exception as exc:  # noqa: BLE001
        log.warning("evidence LLM unexpected: %s", type(exc).__name__)
        return None


def build_why(
    *,
    profile: Profile,
    career: dict,
    market: MarketStats,
    counterfactual: str,
) -> Why:
    """Public entry: grounded Why with optional LLM polish + template fallback."""
    allowed_quotes = collect_allowed_quotes(profile)
    # Ensure selected quote is in allowed list for belonging checks
    selected = select_quote_for_career(profile, career)
    if selected and selected not in allowed_quotes and selected != "hồ sơ hiện tại của bạn":
        allowed_quotes = [selected] + allowed_quotes
    stats = market_stats_dict(market)

    llm_why = _try_llm_why(
        career_title=str(career.get("title") or ""),
        allowed_quotes=allowed_quotes or [selected],
        stats=stats,
        counterfactual_fact=counterfactual,
    )
    if llm_why is not None:
        return llm_why

    return template_why(
        profile=profile,
        career=career,
        market=market,
        counterfactual=counterfactual,
    )


def assert_why_grounded(why: Why, profile: Profile, market: MarketStats) -> None:
    """Raise AssertionError if why violates grounding — for tests."""
    allowed_q = collect_allowed_quotes(profile) + ["hồ sơ hiện tại của bạn"]
    stats = market_stats_dict(market)
    nums = allowed_number_tokens(stats)
    for item in why.from_you:
        assert quote_belongs(item.quote, allowed_q) or item.quote == "hồ sơ hiện tại của bạn"
    for item in why.from_market:
        assert numbers_grounded(item.stat, nums) or not extract_number_tokens(item.stat)
    # counterfactual may include career title words; numbers still checked against stats + none
    if extract_number_tokens(why.counterfactual):
        # allow numbers only if in stats (titles usually have no digits)
        assert numbers_grounded(why.counterfactual, nums)
