"""Conversational profiler — PR-03. Design: docs/AI_DESIGN.md §1.

Shared engine for journey_mode explore|launch; mode locked on opening turn.
Phase transitions decided by CODE from profile completeness (not the LLM).
LLM structured output optional; always falls back to deterministic path.
User corrections outrank model inference on later merges.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from typing import Optional

from app.core.config import get_settings
from app.models.profiler_io import ProfileDelta, ProfilerTurnOutput
from app.models.schemas import (
    ChatResponse,
    Constraints,
    EvidenceQuote,
    ExperienceEvidence,
    JourneyMode,
    Phase,
    Profile,
    ProfilePatch,
    ProfileSkill,
)
from app.prompts.profiler import (
    PHASES,
    build_profiler_system,
    get_fallback_question,
)
from app.services import agent_policy, session_store
from app.services.llm import LLMError, chat_json
from app.services.session_store import Corrections, SessionState

log = logging.getLogger("profiler")

PHASE_ORDER: list[Phase] = list(PHASES)  # type: ignore[arg-type]
DIM_KEYS = ("ky_thuat", "phan_tich", "sang_tao", "xa_hoi", "quan_ly")

# Soft keyword → dimension bumps for deterministic offline path (no live LLM).
_DIM_KEYWORDS: dict[str, tuple[str, ...]] = {
    # Avoid accent-folding homographs such as "hạn"→"han" (not welding) and
    # generic nouns such as "điện thoại" (not evidence of technical ability).
    "ky_thuat": (
        "sửa", "sửa đồ", "sửa quạt", "sửa xe", "sửa máy", "sửa chữa",
        "đồ điện", "điện lạnh", "mạch điện", "dây điện",
        "máy móc", "vận hành máy", "lắp ráp", "lắp đặt", "code", "lập trình",
        "react", "python", "cơ khí", "hàn dây", "mỏ hàn",
    ),
    "phan_tich": (
        "dữ liệu", "excel", "phân tích", "dashboard", "số liệu", "logic",
        "bài toán", "toán học", "sql",
    ),
    "sang_tao": (
        "vẽ", "vẽ tranh", "vẽ tay", "vẽ logo", "vẽ minh họa", "thiết kế",
        "nhạc", "sáng tạo", "viết", "viết bài", "viết truyện", "viết content",
        "viết lách", "photoshop", "figma", "màu sắc", "quay video", "dựng phim",
    ),
    "xa_hoi": (
        "dạy", "dạy học", "dạy bạn", "dạy trẻ", "dạy tiếng", "giảng dạy",
        "hướng dẫn", "giúp", "tình nguyện", "chăm sóc", "tư vấn", "giao tiếp",
    ),
    # "lịch" alone also appears in "du lịch" and "lịch sử". Scheduling
    # phrases remain useful evidence without turning travel/history into management.
    "quan_ly": (
        "tổ chức", "xếp lịch", "lên lịch", "làm lịch", "nhóm", "quản lý",
        "điều phối", "kinh doanh",
    ),
}


def _fold_text(text: str) -> str:
    """Lowercase Vietnamese text and remove accents for resilient keyword matching."""
    normalized = unicodedata.normalize("NFKD", (text or "").lower().replace("đ", "d"))
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _has_vietnamese_marks(text: str) -> bool:
    raw = (text or "").lower()
    return "đ" in raw or any(
        unicodedata.combining(char)
        for char in unicodedata.normalize("NFKD", raw)
    )


def _contains_phrase(text: str, phrase: str) -> bool:
    escaped = re.escape(phrase.strip()).replace(r"\ ", r"\s+")
    return bool(re.search(rf"(?<!\w){escaped}(?!\w)", text))


def _contains_keyword(text: str, keyword: str) -> bool:
    """Match whole Vietnamese phrases and support fully unaccented user input.

    We first compare the original text. Accent folding is only used when the user's
    input itself has no Vietnamese marks; this avoids treating words such as "hạn"
    and "hàn" as equivalent in normal accented Vietnamese.
    """
    raw = (text or "").lower()
    key = (keyword or "").lower()
    if _contains_phrase(raw, key):
        return True
    if _has_vietnamese_marks(raw):
        return False
    # These one-word forms collapse into common unrelated Vietnamese words when
    # accents are removed (vẽ→ve/về, dạy→day/đây, sửa→sua/sữa). Their explicit
    # multi-word variants remain available in `_DIM_KEYWORDS` for no-accent input.
    if _fold_text(key) in {"ve", "day", "sua", "viet"}:
        return False
    return _contains_phrase(_fold_text(raw), _fold_text(key))


_UNCERTAIN_INTEREST_CUES = (
    "không biết",
    "chưa biết",
    "không rõ",
    "chưa rõ",
    "không có gì",
    "tùy",
    "bình thường",
)


_NEGATED_SKILL_PREFIXES = (
    "không biết",
    "chưa biết",
    "không dùng",
    "chưa dùng",
    "không giỏi",
    "chưa giỏi",
    "không có kinh nghiệm",
)


def _all_mentions_locally_negated(
    text: str, keyword: str, prefixes: tuple[str, ...]
) -> bool:
    folded = _fold_text(text)
    key = _fold_text(keyword)
    matches = list(re.finditer(rf"(?<!\w){re.escape(key)}(?!\w)", folded))
    if not matches:
        return False
    for match in matches:
        context = folded[max(0, match.start() - 64) : match.start()]
        # A contrast/conjunction starts a new local claim: "chưa biết Python nhưng
        # đã dùng SQL" must not accidentally negate SQL as well.
        context = re.split(r"[,.!?;]|\b(?:nhung|tuy nhien|con|song)\b", context)[-1]
        if not any(_fold_text(prefix) in context for prefix in prefixes):
            return False
    return True


def _is_negated_skill_mention(text: str, keyword: str) -> bool:
    """True only when every mention says the user does not have that skill."""
    return _all_mentions_locally_negated(text, keyword, _NEGATED_SKILL_PREFIXES)

# Cues that a user is retracting/contradicting something said earlier in the
# conversation — never additive. Profile is visible/editable, so a correction must
# also leave a trace in evidence_quotes (transparency), not just silently vanish.
_NEGATION_CUES: tuple[str, ...] = (
    "không thích",
    "không muốn",
    "hết thích",
    "không còn thích",
    "không còn",
    "ghét",
    "chán",
    "không giỏi",
    "không hợp",
    "chưa biết",
    "không biết",
    "bỏ",
    "xóa",
)


def _is_negated_signal_mention(text: str, keyword: str) -> bool:
    """Do not turn a rejected activity into a positive profile dimension."""
    return _all_mentions_locally_negated(
        text,
        keyword,
        _NEGATION_CUES + _NEGATED_SKILL_PREFIXES,
    )


# Filler words to strip before comparing an interest label against a correction
# message — interest labels are often a whole clause ("em thích vẽ"), not a compact
# token like a skill name, so exact/full-string containment would almost never match
# a later, differently-worded negation. Compare on remaining content words instead.
_INTEREST_STOPWORDS = frozenset(
    {
        "em", "mình", "bạn", "thích", "rất", "khá", "cũng", "và", "là", "có",
        "được", "hay", "nhiều", "một", "chút", "hơi", "thấy", "vui", "làm", "nữa",
        "không", "à", "gì", "cái", "này", "đó", "the", "a",
    }
)


def _interest_content_words(text: str) -> list[str]:
    folded_stopwords = {_fold_text(word) for word in _INTEREST_STOPWORDS}
    return [
        w
        for w in re.findall(r"[a-z]+", _fold_text(text))
        if w not in folded_stopwords and len(w) >= 2
    ]


def _interest_matches_removed(candidate: str, removed: str) -> bool:
    candidate_words = set(_interest_content_words(candidate))
    removed_words = set(_interest_content_words(removed))
    if not removed_words:
        return _fold_text(candidate).strip() == _fold_text(removed).strip()
    return removed_words.issubset(candidate_words)


def _detect_corrections(text: str, profile: Optional[Profile]) -> Optional["CorrectionsDelta"]:
    """Detect a verbal correction: negation cue + a skill/interest/dimension keyword
    already present in this message. Never additive — only ever removes/resets."""
    from app.models.profiler_io import CorrectionsDelta

    folded = _fold_text(text)
    if not any(_fold_text(cue) in folded for cue in _NEGATION_CUES):
        return None

    remove_skills: list[str] = []
    remove_interests: list[str] = []
    if profile is not None:
        for skill in profile.skills:
            if skill.name and _contains_phrase(folded, _fold_text(skill.name)):
                remove_skills.append(skill.name)
        for interest in profile.interests:
            words = _interest_content_words(interest)
            if words and any(_contains_phrase(folded, word) for word in words):
                remove_interests.append(interest)

    reset_dims: list[str] = []
    for dim, kws in _DIM_KEYWORDS.items():
        # A first-time "chưa biết Python" is absence of evidence, not a weak
        # technical score. Reset only a signal that was actually present before.
        if (
            profile is not None
            and float(profile.dimensions.get(dim, 0.0) or 0.0) > 0.0
            and any(_contains_keyword(text, k) for k in kws)
        ):
            reset_dims.append(dim)

    if not (remove_skills or remove_interests or reset_dims):
        return None
    return CorrectionsDelta(
        remove_skills=remove_skills,
        remove_interests=remove_interests,
        reset_dimensions=reset_dims,
    )


# ---------- merge / completeness / phase (pure) ----------


def merge_delta(
    profile: Profile,
    delta: ProfileDelta,
    corrections: Corrections,
    turn: int,
) -> Profile:
    """Merge validated delta into profile; corrections win."""
    # Verbal corrections (retract/reset) apply BEFORE the additive merge below, so a
    # same-turn "remove X, but here's evidence for Y" still lands Y correctly.
    if delta.corrections is not None:
        for name in delta.corrections.remove_skills:
            corrections.removed_skills.add(name)
        for name in delta.corrections.remove_interests:
            corrections.removed_interests.add(name)
        for dim in delta.corrections.reset_dimensions:
            if dim in DIM_KEYS:
                profile.dimensions[dim] = 0.15
                corrections.dimension_overrides.pop(dim, None)
        profile.skills = [
            s for s in profile.skills if s.name.lower() not in {r.lower() for r in corrections.removed_skills}
        ]
        profile.interests = [
            i for i in profile.interests if i.lower() not in {r.lower() for r in corrections.removed_interests}
        ]

    # Dimensions
    for key, value in (delta.dimensions or {}).items():
        if key not in DIM_KEYS:
            continue
        if key in corrections.dimension_overrides:
            profile.dimensions[key] = corrections.dimension_overrides[key]
            continue
        try:
            v = float(value)
        except (TypeError, ValueError):
            continue
        v = max(0.0, min(1.0, v))
        profile.dimensions[key] = max(profile.dimensions.get(key, 0.0), v)
    for key, value in corrections.dimension_overrides.items():
        profile.dimensions[key] = value

    # Interests (union) — same injection guard as skills/evidence_quotes, since an LLM-produced
    # delta is not otherwise re-checked past the skill-name filter below.
    seen_i = {i.lower() for i in profile.interests}
    removed_i = {r.lower() for r in corrections.removed_interests}
    for interest in delta.interests or []:
        text = (interest or "").strip()
        if (
            text
            and text.lower() not in seen_i
            and text.lower() not in removed_i
            and not any(
                _interest_matches_removed(text, removed)
                for removed in corrections.removed_interests
            )
            and not _looks_like_injection(text)
        ):
            profile.interests.append(text)
            seen_i.add(text.lower())

    # Skills — skip removed by user correction; require source_quote for new
    existing_skills = {s.name.lower(): s for s in profile.skills}
    for skill in delta.skills or []:
        name = (skill.name or "").strip()
        if not name or name.lower() in {r.lower() for r in corrections.removed_skills}:
            continue
        quote = (skill.source_quote or "").strip()
        if not quote:
            continue
        # Never store instruction-like "skills"
        if _looks_like_injection(name):
            continue
        if name.lower() in existing_skills:
            prev = existing_skills[name.lower()]
            if quote and not prev.source_quote:
                prev.source_quote = quote
            if skill.level and not prev.level:
                prev.level = skill.level
        else:
            item = ProfileSkill(name=name, level=skill.level or "", source_quote=quote)
            profile.skills.append(item)
            existing_skills[name.lower()] = item
    profile.skills = [
        s for s in profile.skills if s.name.lower() not in {r.lower() for r in corrections.removed_skills}
    ]

    # Experiences (max 3); respect removals
    titles = {e.title.lower() for e in profile.experiences}
    for exp in delta.experiences or []:
        title = (exp.title or "").strip()
        if not title:
            continue
        if title.lower() in {r.lower() for r in corrections.removed_experience_titles}:
            continue
        if title.lower() in titles:
            continue
        if len(profile.experiences) >= 3:
            break
        if not (exp.source_quote or "").strip():
            continue
        profile.experiences.append(
            ExperienceEvidence(
                title=title,
                kind=exp.kind,
                description=exp.description or "",
                skills=list(exp.skills or []),
                source_quote=exp.source_quote,
            )
        )
        titles.add(title.lower())
    profile.experiences = [
        e
        for e in profile.experiences
        if e.title.lower() not in {r.lower() for r in corrections.removed_experience_titles}
    ]

    # Constraints (partial)
    if delta.constraints is not None:
        c = profile.constraints
        if delta.constraints.region_pref is not None:
            c.region_pref = delta.constraints.region_pref
        if delta.constraints.study_budget is not None:
            c.study_budget = delta.constraints.study_budget
        if delta.constraints.study_duration_pref is not None:
            c.study_duration_pref = delta.constraints.study_duration_pref
        if (
            delta.constraints.notes is not None
            and delta.constraints.notes != ""
            and not _looks_like_injection(delta.constraints.notes)
        ):
            if c.notes:
                c.notes = f"{c.notes}; {delta.constraints.notes}"
            else:
                c.notes = delta.constraints.notes

    # Education / job goal — respect locks
    if not corrections.locked_education_stage and delta.education_stage is not None:
        profile.education_stage = delta.education_stage
    if not corrections.locked_job_goal and delta.job_goal is not None:
        profile.job_goal = delta.job_goal

    # Both the agent extractor and classic deterministic path can describe the same
    # user turn. Keep one transparent evidence item per (turn, quote).
    seen_quotes = {(item.turn, item.quote) for item in profile.evidence_quotes}
    for eq in delta.evidence_quotes or []:
        quote = (eq.quote or "").strip()
        if not quote or _looks_like_injection(quote):
            continue
        key = (eq.turn or turn, quote[:500])
        if key in seen_quotes:
            continue
        seen_quotes.add(key)
        profile.evidence_quotes.append(
            EvidenceQuote(turn=eq.turn or turn, quote=quote[:500], mapped_to=eq.mapped_to or "")
        )

    profile.completeness = compute_completeness(profile.journey_mode, profile)
    return profile


def apply_patch(profile: Profile, patch: ProfilePatch, corrections: Corrections) -> Profile:
    if patch.dimensions:
        for key, value in patch.dimensions.items():
            if key in DIM_KEYS:
                v = max(0.0, min(1.0, float(value)))
                profile.dimensions[key] = v
                corrections.dimension_overrides[key] = v

    if patch.remove_skills:
        remove = {n.lower() for n in patch.remove_skills}
        corrections.removed_skills.update(patch.remove_skills)
        profile.skills = [s for s in profile.skills if s.name.lower() not in remove]

    if patch.add_interests:
        seen = {i.lower() for i in profile.interests}
        for interest in patch.add_interests:
            t = interest.strip()
            if t and t.lower() not in seen:
                profile.interests.append(t)
                seen.add(t.lower())
            # A direct user edit is newer and higher-authority than an old removal.
            corrections.removed_interests = {
                removed
                for removed in corrections.removed_interests
                if not _interest_matches_removed(t, removed)
            }

    if patch.remove_interests:
        remove_interests = {item.strip().lower() for item in patch.remove_interests if item.strip()}
        corrections.removed_interests.update(patch.remove_interests)
        profile.interests = [
            interest for interest in profile.interests if interest.lower() not in remove_interests
        ]

    if "education_stage" in patch.model_fields_set:
        profile.education_stage = patch.education_stage
        corrections.locked_education_stage = True

    if "job_goal" in patch.model_fields_set:
        profile.job_goal = patch.job_goal
        corrections.locked_job_goal = True

    if patch.remove_experience_titles:
        corrections.removed_experience_titles.update(patch.remove_experience_titles)
        remove_t = {t.lower() for t in patch.remove_experience_titles}
        profile.experiences = [e for e in profile.experiences if e.title.lower() not in remove_t]

    if patch.add_experiences:
        titles = {e.title.lower() for e in profile.experiences}
        for exp in patch.add_experiences:
            if exp.title.lower() in titles:
                continue
            if len(profile.experiences) >= 3:
                break
            profile.experiences.append(exp)
            titles.add(exp.title.lower())
            corrections.removed_experience_titles.discard(exp.title)

    profile.completeness = compute_completeness(profile.journey_mode, profile)
    return profile


def _sourced_skills(profile: Profile) -> list[ProfileSkill]:
    return [s for s in profile.skills if (s.source_quote or "").strip()]


def _active_dimensions(profile: Profile) -> int:
    return sum(1 for v in profile.dimensions.values() if v and float(v) > 0.05)


def _has_constraint_signal(profile: Profile, declined: bool) -> bool:
    c = profile.constraints
    return bool(
        declined
        or c.region_pref
        or c.study_budget
        or c.study_duration_pref
        or (c.notes and c.notes.strip())
    )


def compute_completeness(mode: JourneyMode, profile: Profile, declined: bool = False) -> float:
    """0..1 progress for FE; mode-specific weights."""
    if mode == "launch":
        parts = [
            1.0 if profile.education_stage else 0.0,
            1.0 if profile.job_goal or "chưa" in (profile.constraints.notes or "").lower() else 0.0,
            min(1.0, len(profile.experiences) / 1.0) if profile.experiences else (
                0.5 if "chưa" in (profile.constraints.notes or "").lower() else 0.0
            ),
            min(1.0, len(_sourced_skills(profile)) / 2.0),
            1.0 if _has_constraint_signal(profile, declined) else 0.0,
        ]
    else:
        parts = [
            min(1.0, len(profile.interests) / 2.0),
            min(1.0, _active_dimensions(profile) / 2.0),
            min(1.0, len(_sourced_skills(profile)) / 2.0),
            1.0 if _has_constraint_signal(profile, declined) else 0.0,
        ]
    return round(sum(parts) / len(parts), 2)


def phase_goals_met(
    mode: JourneyMode,
    phase: Phase,
    profile: Profile,
    *,
    constraint_declined: bool = False,
    turns_in_phase: int = 0,
) -> bool:
    """Whether CODE should advance past this phase."""
    if phase == "warmup":
        return turns_in_phase >= 1
    if phase == "interests":
        if mode == "launch":
            return turns_in_phase >= 1 and (
                len(profile.interests) >= 1
                or bool(profile.job_goal)
                or turns_in_phase >= 2
            )
        return turns_in_phase >= 1 and (
            (len(profile.interests) >= 2 and _active_dimensions(profile) >= 1)
            or turns_in_phase >= 3
        )
    if phase == "abilities":
        return len(_sourced_skills(profile)) >= 2 or turns_in_phase >= 3
    if phase == "constraints":
        return _has_constraint_signal(profile, constraint_declined) or turns_in_phase >= 2
    if phase == "wrapup":
        return turns_in_phase >= 1
    return False


def advance_phase(
    mode: JourneyMode,
    phase: Phase,
    profile: Profile,
    *,
    constraint_declined: bool,
    turns_in_phase: int,
    force_done_signal: bool = False,
) -> tuple[Phase, bool, int]:
    """Return (new_phase, done, turns_in_phase)."""
    turns = turns_in_phase
    current = phase
    if current == "wrapup" and (force_done_signal or turns >= 1):
        if force_done_signal or turns >= 1:
            return "wrapup", True, turns

    while phase_goals_met(
        mode, current, profile, constraint_declined=constraint_declined, turns_in_phase=turns
    ):
        idx = PHASE_ORDER.index(current)
        if idx >= len(PHASE_ORDER) - 1:
            # stay on wrapup until confirmation
            return "wrapup", False, turns
        current = PHASE_ORDER[idx + 1]
        turns = 0
        if current == "wrapup":
            break
    return current, False, turns


def _looks_like_injection(text: str) -> bool:
    t = text.lower()
    bad = (
        "ignore previous",
        "api_key",
        "root_access",
        "system:",
        "you are dan",
        "sk-",
    )
    return any(b in t for b in bad)


def _user_declines_constraint(message: str) -> bool:
    m = message.lower()
    return any(
        p in m
        for p in (
            "không rõ",
            "khong ro",
            "chưa biết",
            "chua biet",
            "không có",
            "khong co",
            "tùy",
            "không quan trọng",
            "không ràng buộc",
        )
    )


def _wants_results(message: str) -> bool:
    """An explicit request to stop profiling and inspect suggestions."""
    folded = _fold_text(message)
    return any(
        phrase in folded
        for phrase in (
            "xem goi y",
            "xem huong",
            "xem ket qua",
            "xem nghe",
            "goi y nghe",
            "cho em xem",
            "cho minh xem",
        )
    )


def _wants_done(message: str) -> bool:
    m = message.lower()
    return any(
        p in m
        for p in (
            "ok",
            "được",
            "duoc",
            "sẵn sàng",
            "san sang",
            "xem hướng",
            "xem goi y",
            "đúng rồi",
            "dung roi",
            "ổn",
            "xon",
        )
    )


# ---------- deterministic LLM-free turn ----------


def _compact_interest_label(text: str) -> str | None:
    """PR-10: avoid dumping the full utterance as an interest (noise)."""
    raw = re.sub(r"\s+", " ", (text or "").strip())
    if len(raw) < 8 or _looks_like_injection(raw):
        return None
    folded = _fold_text(raw)
    # Prefer explicit activities; generic device mentions such as "điện thoại"
    # are not in this allowlist and therefore cannot create technical evidence.
    activity_keys = (
        "sửa",
        "vẽ",
        "code",
        "lập trình",
        "dashboard",
        "excel",
        "nấu",
        "dạy",
        "thiết kế",
        "chăm",
        "phân tích",
        "máy móc",
        "đồ điện",
        "hàn",
        "game",
        "viết",
        "quay video",
        "edit",
        "đọc sách",
        "thể thao",
        "bóng đá",
        "làm vườn",
        "bán hàng",
        "tổ chức",
        "giúp",
        "tình nguyện",
    )

    interest_cues = (
        "thích", "mê", "đam mê", "yêu thích", "hứng thú", "muốn thử",
        "hay làm", "quên cả thời gian",
    )
    non_interest_markers = (
        "em o ", "minh o ", "gia dinh", "ngan sach", "khong co nhieu tien",
        "hoc phi", "cho em xem", "cho minh xem", "xem goi y", "xem huong",
        "xem ket qua", "san sang", "dung roi",
    )
    education_only = re.compile(
        r"^(?:em|minh|toi)?\s*(?:dang)?\s*(?:hoc|la)?\s*"
        r"(?:lop\s*\d+|cap\s*\d|hoc sinh|sinh vien(?:\s*nam\s*\w+)?)\s*$"
    )

    # Pick the clause carrying the activity, not a demographic lead-in such as
    # "em học lớp 12, em thích vẽ". Activity evidence wins over a generic cue.
    best: str | None = None
    best_has_activity = False
    for clause in (part.strip() for part in re.split(r"[.!?,;]", raw)):
        if not clause:
            continue
        clause_folded = _fold_text(clause)
        if education_only.match(clause_folded):
            continue
        if any(marker in clause_folded for marker in non_interest_markers):
            continue
        has_activity = any(_contains_keyword(clause, key) for key in activity_keys)
        has_cue = any(_contains_keyword(clause, cue) for cue in interest_cues)
        if not (has_activity or has_cue):
            continue
        if best is None or (has_activity and not best_has_activity):
            best = clause
            best_has_activity = has_activity
        if has_activity:
            break

    if best is None:
        return None
    if any(_fold_text(cue) in folded for cue in _UNCERTAIN_INTEREST_CUES) and not best_has_activity:
        return None
    return best if len(best) <= 40 else best[:37] + "…"


_REDACTION_MARKER_RE = re.compile(
    r"\[(?:email|số điện thoại|khóa bí mật) đã ẩn\]",
    flags=re.IGNORECASE,
)
_REDACTED_FIELD_RE = re.compile(
    r"\b(?:e-?mail|mail|số(?:\s+điện\s+thoại)?|sđt|phone|điện\s+thoại|"
    r"api\s*key|key)\s*[:=]?\s*"
    r"\[(?:email|số điện thoại|khóa bí mật) đã ẩn\]",
    flags=re.IGNORECASE,
)
_PRIVACY_BOILERPLATE_RE = re.compile(
    r"\b(?:em|tôi|toi|mình|minh|cháu|chau|của|cua|là|la|và|va|"
    r"liên\s+hệ|lien\s+he|qua|số|so|điện\s+thoại|dien\s+thoai|"
    r"e-?mail|mail|sđt|sdt|phone|api|key)\b",
    flags=re.IGNORECASE,
)


def _has_meaningful_profile_text(text: str) -> bool:
    """Privacy-only/contact-only turns must not advance profiling progress."""
    without_fields = _REDACTED_FIELD_RE.sub(" ", text or "")
    without_markers = _REDACTION_MARKER_RE.sub(" ", without_fields)
    without_boilerplate = _PRIVACY_BOILERPLATE_RE.sub(" ", without_markers)
    return bool(re.search(r"[\wÀ-ỹ]", without_boilerplate, flags=re.UNICODE))


def _extract_job_goal(text: str, phase: Phase) -> str | None:
    """Only set job_goal on clear intent (not every message containing 'việc')."""
    folded = _fold_text(text)
    if phase not in ("warmup", "interests", "constraints", "wrapup"):
        # abilities turns usually describe tools, not goals
        if not any(
            _contains_phrase(folded, _fold_text(k))
            for k in ("muốn làm", "tìm việc", "ứng tuyển", "entry", "fresher")
        ):
            return None
    goal_markers = (
        "muốn làm",
        "tìm việc",
        "muốn tìm",
        "entry-level",
        "entry level",
        "fresher",
        "thực tập",
        "data",
        "dữ liệu",
        "lập trình",
        "marketing",
        "kế toán",
        "thiết kế",
    )
    if not any(_contains_phrase(folded, _fold_text(k)) for k in goal_markers):
        return None
    # Prefer short canned goals when keywords match
    if any(_contains_phrase(folded, _fold_text(k)) for k in ("data", "dữ liệu", "excel", "dashboard")):
        return "việc dữ liệu / phân tích entry-level"
    if any(_contains_phrase(folded, _fold_text(k)) for k in ("lập trình", "react", "python", "web", "code")):
        return "việc lập trình / web entry-level"
    if _contains_phrase(folded, "marketing"):
        return "việc digital marketing entry-level"
    # fallback: first 80 chars if short enough intent phrase
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned[:80] if len(cleaned) <= 80 else cleaned[:77] + "…"


def deterministic_turn(
    *,
    journey_mode: JourneyMode,
    phase: Phase,
    message: str,
    turn: int,
    fallback_index: int,
    recent_replies: list[str] | None = None,
    profile: Optional[Profile] = None,
) -> ProfilerTurnOutput:
    """Build a structured turn without calling a model provider."""
    text = (message or "").strip()
    delta = ProfileDelta()
    lower = text.lower()
    folded = _fold_text(text)

    corrections_delta = _detect_corrections(text, profile)
    if corrections_delta is not None:
        delta.corrections = corrections_delta

    if journey_mode == "launch":
        if any(_contains_phrase(folded, _fold_text(k)) for k in ("năm cuối", "final year")):
            delta.education_stage = "final_year"
        if any(_contains_phrase(folded, _fold_text(k)) for k in ("mới tốt nghiệp", "tốt nghiệp")):
            delta.education_stage = "recent_graduate"
        goal = _extract_job_goal(text, phase)
        if goal:
            delta.job_goal = goal
        explicit_no_experience = any(
            _contains_phrase(folded, _fold_text(k))
            for k in (
                "chưa có thực tập", "chưa có project", "chưa có kinh nghiệm",
                "không có project", "không có thực tập", "chưa từng thực tập",
            )
        )
        if explicit_no_experience:
            from app.models.profiler_io import ConstraintsDelta

            delta.constraints = ConstraintsDelta(notes="chưa có thực tập/project — explicit no experience")
        experience_mentioned = any(
            _contains_phrase(folded, _fold_text(k))
            for k in ("project", "dashboard", "ứng dụng", "app", "thực tập", "internship")
        )
        if experience_mentioned and not explicit_no_experience:
            title = "Project từ hội thoại"
            if _contains_phrase(folded, "dashboard"):
                title = "Dashboard"
            elif _contains_phrase(folded, "todo") or _contains_phrase(folded, "react"):
                title = "App todo"
            skills: list[str] = []
            for token in ("excel", "react", "python", "sql", "figma", "powerpoint", "word"):
                if _contains_phrase(folded, token) and not _is_negated_skill_mention(text, token):
                    skills.append(
                        token.upper()
                        if token == "sql"
                        else ("Excel" if token == "excel" else token.capitalize())
                    )
            delta.experiences = [
                ExperienceEvidence(
                    title=title,
                    kind="internship"
                    if _contains_phrase(folded, _fold_text("thực tập")) or _contains_phrase(folded, "internship")
                    else "project",
                    description=text[:200],
                    skills=skills,
                    source_quote=text[:240],
                )
            ]
            for s in skills:
                delta.skills.append(
                    ProfileSkill(name=s, level="đã đề cập", source_quote=text[:240])
                )
    else:
        if any(
            _contains_phrase(folded, _fold_text(k))
            for k in ("lớp 12", "lớp 11", "cấp 3", "học sinh")
        ):
            delta.education_stage = "high_school"

    # Interests: compact labels only (PR-10); skip pure ability/tool turns.
    # A correction turn ("à không, em không thích vẽ nữa") must not immediately
    # re-add the very interest it's retracting.
    if corrections_delta is None:
        if phase in ("warmup", "interests", "constraints") or journey_mode == "launch" and phase == "interests":
            label = _compact_interest_label(text)
            if label:
                delta.interests = [label]
        elif phase == "abilities" and not any(
            _contains_keyword(text, k)
            for k in ("excel", "python", "react", "khen", "giỏi", "làm tốt")
        ):
            label = _compact_interest_label(text)
            if label:
                delta.interests = [label]

    # Dimension bumps from keywords — skip entirely if the whole message looks like an
    # injection attempt, even if it also contains a legit-sounding keyword substring
    # (e.g. "code" inside an "ignore previous instructions... code" message). Also skip
    # any dimension this same turn is resetting via a correction — bumping and
    # resetting the same dimension in one delta would fight each other in merge_delta.
    dims: dict[str, float] = {}
    reset_now = set(corrections_delta.reset_dimensions) if corrections_delta else set()
    if not _looks_like_injection(text):
        for dim, kws in _DIM_KEYWORDS.items():
            if dim in reset_now:
                continue
            if any(
                _contains_keyword(text, k)
                and not _is_negated_signal_mention(text, k)
                for k in kws
            ):
                current = float((profile.dimensions if profile else {}).get(dim, 0.0) or 0.0)
                # Repeated concrete evidence should strengthen a signal instead of every
                # persona collapsing to the same binary 0.55 dimension vector.
                # Keyword-only inference remains intentionally conservative; richer
                # confidence must come from stronger/validated evidence, not repetition.
                dims[dim] = min(0.8, max(0.55, current + 0.15))
    delta.dimensions = dims

    # Skills from tool keywords if not already added
    tool_map = {
        "excel": "Excel",
        "react": "React",
        "python": "Python",
        "figma": "Figma",
        "photoshop": "Photoshop",
        "javascript": "JavaScript",
        "sql": "SQL",
    }
    existing = {s.name.lower() for s in delta.skills}
    for key, name in tool_map.items():
        if (
            _contains_keyword(text, key)
            and name.lower() not in existing
            and not _looks_like_injection(name)
            and not _is_negated_skill_mention(text, key)
        ):
            delta.skills.append(
                ProfileSkill(name=name, level="đã đề cập", source_quote=text[:240] or name)
            )

    if text and not _looks_like_injection(text):
        mapped = next(iter(dims.keys()), "interests")
        delta.evidence_quotes = [
            EvidenceQuote(turn=turn, quote=text[:240], mapped_to=mapped)
        ]

    # Soft constraints
    if any(
        _contains_phrase(folded, _fold_text(k))
        for k in ("hà nội", "hanoi", "hcm", "sài gòn", "đà nẵng", "danang")
    ):
        from app.models.profiler_io import ConstraintsDelta

        region = "hanoi" if any(_contains_phrase(folded, k) for k in ("ha noi", "hanoi")) else (
            "hcm" if any(_contains_phrase(folded, k) for k in ("hcm", "sai gon")) else (
                "danang" if any(_contains_phrase(folded, k) for k in ("da nang", "danang")) else None
            )
        )
        if region:
            if delta.constraints is None:
                delta.constraints = ConstraintsDelta(region_pref=region)
            else:
                delta.constraints.region_pref = region

    if any(
        _contains_phrase(folded, _fold_text(k))
        for k in ("hạn chế", "eo hẹp", "không có nhiều tiền", "ngân sách thấp")
    ):
        from app.models.profiler_io import ConstraintsDelta

        if delta.constraints is None:
            delta.constraints = ConstraintsDelta(study_budget="hạn chế")
        else:
            delta.constraints.study_budget = "hạn chế"

    reply = get_fallback_question(
        journey_mode, phase, fallback_index, recent_replies=recent_replies
    )
    return ProfilerTurnOutput(reply=reply, profile_delta=delta, phase_done=False)


# ---------- public API ----------


def handle_turn(
    session_id: str,
    message: Optional[str],
    journey_mode: JourneyMode = "explore",
) -> ChatResponse:
    state = session_store.get_session(session_id)
    is_new_session = state is None
    if state is None:
        state = session_store.create_session(session_id, journey_mode)
    else:
        # Mode locked after opening — ignore later journey_mode changes
        journey_mode = state.journey_mode

    def _recent_assistant() -> list[str]:
        return [
            m["content"]
            for m in state.messages
            if m.get("role") == "assistant" and m.get("content")
        ][-4:]

    opening_request = message is None or (
        isinstance(message, str) and message.strip() == ""
    )

    # Opening turn (no user message yet). Reopening an existing session must be
    # idempotent: never rewind its phase/turn while retaining the old profile.
    if opening_request and not is_new_session and state.turn > 0:
        if state.done:
            reply = "Hồ sơ này đã sẵn sàng. Bạn có thể xem lại hồ sơ hoặc mở phần gợi ý bên dưới."
        else:
            reply = "Mình đã mở lại hồ sơ đang làm dở. Bạn tiếp tục từ chỗ trước nhé."
        return ChatResponse(
            reply=reply,
            phase=state.phase,
            turn=state.turn,
            done=state.done,
            profile=state.profile,
        )

    if opening_request and state.turn == 0:
        state.turn = 1
        state.phase = "warmup"
        state.turns_in_phase = 0
        reply = get_fallback_question(
            state.journey_mode,
            "warmup",
            state.fallback_index,
            recent_replies=_recent_assistant(),
        )
        state.fallback_index += 1
        state.messages.append({"role": "assistant", "content": reply})
        state.profile.completeness = compute_completeness(
            state.journey_mode, state.profile, state.constraint_declined
        )
        session_store.save_session(state)
        return ChatResponse(
            reply=reply,
            phase=state.phase,
            turn=state.turn,
            done=False,
            profile=state.profile,
        )

    # Persist and send to model only a privacy-sanitized turn. This removes direct
    # contact identifiers, secrets, gender/self-label and prestige/GPA proxies while
    # preserving career evidence such as tools, activities and regions.
    raw_user_text = (message or "").strip()
    user_text = agent_policy.strip_privacy_text(raw_user_text)
    if raw_user_text and not _has_meaningful_profile_text(user_text):
        reply = (
            "Mình không dùng thông tin nhận dạng đó để định hướng. "
            "Bạn hãy kể một hoạt động, kỹ năng hoặc điều kiện học tập liên quan nhé."
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.messages = state.messages[-16:]
        session_store.save_session(state)
        return ChatResponse(
            reply=reply,
            phase=state.phase,
            turn=state.turn,
            done=state.done,
            profile=state.profile,
        )
    state.messages.append({"role": "user", "content": user_text})
    state.turn += 1
    state.turns_in_phase += 1

    if state.phase == "constraints" and _user_declines_constraint(user_text):
        state.constraint_declined = True

    # PR-13: optional agent path for discover/confirm (langgraph mode only).
    # Classic path always remains fallback; API shape unchanged; no CoT in response.
    from app.services import agent_chat

    agent_reply: str | None = None
    agent_delta = None
    agent_applied_patch: ProfilePatch | None = None
    if agent_chat.agent_enabled_for_chat():
        enrich = agent_chat.run_agent_enrichment(state, user_text)
        agent_delta = enrich.get("delta")
        if not enrich.get("fallback"):
            agent_reply = enrich.get("reply")
        raw_patch = enrich.get("applied_patch")
        if raw_patch:
            try:
                agent_applied_patch = ProfilePatch.model_validate(raw_patch)
            except Exception as exc:  # noqa: BLE001
                log.warning("agent applied_patch invalid session=%s err=%s", state.session_id, type(exc).__name__)
        # never expose enrich["trace"] on ChatResponse
    else:
        # Deterministic: may still use local extract tool (no graph/network planner)
        agent_delta = agent_chat.maybe_run_extract_tools_only(state, user_text)

    turn_out = _produce_turn_output(state, user_text)
    # Prefer agent-extracted delta when present (then classic delta fills gaps)
    delta = turn_out.profile_delta
    if agent_delta is not None:
        # merge agent delta first so classic can add more signals
        state.profile = merge_delta(
            state.profile, agent_delta, state.corrections, state.turn
        )
    if agent_applied_patch is not None:
        # Same correction-precedence path as the REST PATCH /profile endpoint.
        state.profile = apply_patch(state.profile, agent_applied_patch, state.corrections)
    state.profile = merge_delta(
        state.profile, delta, state.corrections, state.turn
    )
    state.profile.session_id = session_id
    state.profile.journey_mode = state.journey_mode
    state.profile.completeness = compute_completeness(
        state.journey_mode, state.profile, state.constraint_declined
    )

    force_done = state.phase == "wrapup" and _wants_done(user_text)
    if (
        not force_done
        and state.phase not in ("warmup", "wrapup")
        and _wants_results(user_text)
        and state.profile.completeness >= 0.5
    ):
        # Respect autonomy when the profile has enough evidence: stop asking
        # canned questions and acknowledge that suggestions are ready.
        force_done = True
        state.phase = "wrapup"
        state.turns_in_phase = 0
        turn_out.reply = get_fallback_question(
            state.journey_mode,
            "wrapup",
            state.fallback_index,
            recent_replies=_recent_assistant(),
        )
        state.fallback_index += 1
    new_phase, done, turns_in_phase = advance_phase(
        state.journey_mode,
        state.phase,
        state.profile,
        constraint_declined=state.constraint_declined,
        turns_in_phase=state.turns_in_phase,
        force_done_signal=force_done,
    )
    if new_phase != state.phase:
        state.phase = new_phase
        state.turns_in_phase = turns_in_phase
        # After phase change, prefer a question for the new phase
        if not done and state.phase != "wrapup":
            turn_out.reply = get_fallback_question(
                state.journey_mode,
                state.phase,
                state.fallback_index,
                recent_replies=_recent_assistant() + [turn_out.reply],
            )
            state.fallback_index += 1
    else:
        state.turns_in_phase = turns_in_phase

    if done or force_done:
        state.done = True
        state.phase = "wrapup"

    # Cap runaway turns still allow wrapup CTA after many messages
    if state.turn >= 10 and state.phase in ("constraints", "wrapup"):
        state.phase = "wrapup"
        if state.turn >= 12:
            state.done = True

    # Prefer agent-composed reply only when non-empty and not done CTA phase
    if agent_reply and not state.done and state.phase != "wrapup":
        reply = agent_reply.strip()
    else:
        reply = turn_out.reply.strip() or get_fallback_question(
            state.journey_mode,
            state.phase,
            state.fallback_index,
            recent_replies=_recent_assistant(),
        )
    # Final de-dupe against last assistant message
    recent = _recent_assistant()
    if reply in recent:
        reply = get_fallback_question(
            state.journey_mode,
            state.phase,
            state.fallback_index + 1,
            recent_replies=recent,
        )
        state.fallback_index += 1
    state.messages.append({"role": "assistant", "content": reply})
    # Keep only last 16 messages in session (demo memory bound)
    state.messages = state.messages[-16:]
    session_store.save_session(state)

    return ChatResponse(
        reply=reply,
        phase=state.phase,
        turn=state.turn,
        done=state.done,
        profile=state.profile,
    )


def _produce_turn_output(state: SessionState, user_text: str) -> ProfilerTurnOutput:
    settings = get_settings()
    use_llm = bool(settings.chat_api_key) and settings.demo_mode != "replay"
    recent = [
        m["content"]
        for m in state.messages
        if m.get("role") == "assistant" and m.get("content")
    ][-4:]

    if use_llm:
        try:
            system = build_profiler_system(state.journey_mode, state.phase)
            # Only pass recent messages; do not log them.
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in state.messages[-8:]
                if m.get("role") in ("user", "assistant")
            ]
            return chat_json(system, history, ProfilerTurnOutput, max_retries=2)
        except LLMError as exc:
            log.warning("profiler LLM fallback session=%s err=%s", state.session_id, type(exc).__name__)
        except Exception as exc:  # noqa: BLE001 — never let an LLM-path bug 500 the chat endpoint
            log.error(
                "profiler LLM path raised unexpected error session=%s err=%s",
                state.session_id,
                type(exc).__name__,
            )

    out = deterministic_turn(
        journey_mode=state.journey_mode,
        phase=state.phase,
        message=user_text,
        turn=state.turn,
        fallback_index=state.fallback_index,
        recent_replies=recent,
        profile=state.profile,
    )
    state.fallback_index += 1
    return out


def get_profile(session_id: str) -> Profile:
    state = session_store.get_session(session_id)
    if state is None:
        raise KeyError(session_id)
    return state.profile


def patch_profile(session_id: str, patch: ProfilePatch) -> Profile:
    state = session_store.get_session(session_id)
    if state is None:
        raise KeyError(session_id)
    state.profile = apply_patch(state.profile, patch, state.corrections)
    state.profile.session_id = session_id
    state.profile.journey_mode = state.journey_mode
    session_store.save_session(state)
    return state.profile


def delete_session(session_id: str) -> bool:
    return session_store.delete_session(session_id)
