"""Matching engine — PR-05. Design: docs/AI_DESIGN.md §4.

score(career) = w_cosine * cosine(profile, career)
              + w_skill_overlap * skill_overlap(profile, career.top_skills)
              + w_market_signal * market_signal(career, region_pref)

Weights from Settings. profile_text / fit vectors NEVER include gender or region.
Region only enters market_signal for informational ordering — never filters candidates.

Cosine source:
1. If data/processed/careers.npy + career_ids.json exist and align → use them
   (MI-06 artifact). Profile side uses a bag-of-tokens hash projection so we
   stay offline without calling embed API in the request path.
2. Else fallback: cosine on the shared 5-dimension vectors (always available).

Stretch: among ranks 6..15 (or remainder), pick highest score whose dominant
career dimension differs from the user's dominant dimension.

Launch readiness + pathways: `pathways.py` (PR-07) — Explore job_readiness=null;
Launch matched/missing/band/queries/actions with GRADUATE_LAUNCH invariants.
"""
from __future__ import annotations

import json
import logging
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import numpy as np

from app.core.config import get_settings
from app.data.seed_loader import get_career, load_careers
from app.models.schemas import MarketStats, Profile, Recommendation
from app.services import evidence as evidence_service
from app.services import pathways

log = logging.getLogger("matching")

DIM_KEYS = ("ky_thuat", "phan_tich", "sang_tao", "xa_hoi", "quan_ly")
DIM_LABELS_VI = {
    "ky_thuat": "thực hành–kỹ thuật",
    "phan_tich": "phân tích–logic",
    "sang_tao": "sáng tạo",
    "xa_hoi": "làm việc với con người",
    "quan_ly": "tổ chức–quản lý",
}

# Cap so a market spike cannot dominate a low-fit profile (PR-05 invariant).
MARKET_SIGNAL_CAP = 0.35
REPO_ROOT = Path(__file__).resolve().parents[3]
PROCESSED = REPO_ROOT / "data" / "processed"
CAREERS_NPY = PROCESSED / "careers.npy"
CAREER_IDS_JSON = PROCESSED / "career_ids.json"


# Stripped from scoring text so free-text leaks cannot bias ranking (PR-08).
_BIAS_LEAK_RE = re.compile(
    r"(?i)\b("
    r"giới\s*tính|con\s+trai|con\s+gái|nam\s+giới|nữ\s+giới|"
    r"\bnữ\b|\bnam\b|"
    r"GPA|điểm\s+trung\s+bình|"
    r"ĐH\s+Bách\s+Khoa|Bách\s+Khoa|NEU|FTU|RMIT|FPT\s+University|"
    r"trường\s+top|trường\s+nổi\s+tiếng|trường\s+chuyên"
    r")\b"
)


def sanitize_scoring_text(text: str) -> str:
    """Remove gender/prestige tokens from free text used only for ranking."""
    cleaned = _BIAS_LEAK_RE.sub(" ", text or "")
    return re.sub(r"\s+", " ", cleaned).strip()


def profile_text(profile: Profile) -> str:
    """Serialize profile for retrieval. NO region, NO gender, NO school prestige."""
    parts: list[str] = []
    for k in DIM_KEYS:
        v = float(profile.dimensions.get(k, 0.0) or 0.0)
        if v > 0.05:
            parts.append(f"{k}:{v:.2f}")
    parts.extend(s.name for s in profile.skills if s.name)
    parts.extend(profile.interests)
    for e in profile.experiences:
        parts.append(e.title)
        parts.extend(e.skills or [])
    if profile.job_goal:
        parts.append(profile.job_goal)
    # quotes — sanitized so gender/school mentions do not enter scoring
    for q in profile.evidence_quotes[:8]:
        if q.quote:
            parts.append(sanitize_scoring_text(q.quote[:120]))
    # constraints.notes / region intentionally omitted (region is not a filter)
    return sanitize_scoring_text(" | ".join(parts))


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))


def _dim_vector(dims: dict[str, Any]) -> list[float]:
    return [float(dims.get(k, 0.0) or 0.0) for k in DIM_KEYS]


def dominant_dimension(dims: dict[str, Any]) -> str:
    vec = [(k, float(dims.get(k, 0.0) or 0.0)) for k in DIM_KEYS]
    vec.sort(key=lambda x: x[1], reverse=True)
    return vec[0][0]


def skill_overlap(profile: Profile, career_top_skills: list[str]) -> float:
    """Weighted Jaccard between profile skills∪interests∪exp skills and career top skills."""
    prof: set[str] = set()
    weights: dict[str, float] = {}
    for s in profile.skills:
        key = _normalize(s.name)
        if not key:
            continue
        prof.add(key)
        # sourced skills weigh more
        weights[key] = max(weights.get(key, 0.0), 1.0 if s.source_quote else 0.6)
    for i in profile.interests:
        key = _normalize(i)
        if key:
            prof.add(key)
            weights[key] = max(weights.get(key, 0.0), 0.5)
    for e in profile.experiences:
        for sk in e.skills or []:
            key = _normalize(sk)
            if key:
                prof.add(key)
                weights[key] = max(weights.get(key, 0.0), 0.9)
        if e.title:
            prof.add(_normalize(e.title))
            weights[_normalize(e.title)] = max(weights.get(_normalize(e.title), 0.0), 0.4)

    career = {_normalize(s) for s in career_top_skills if s}
    if not career and not prof:
        return 0.0
    if not career:
        return 0.0

    # soft match: token containment
    inter_w = 0.0
    matched_c: set[str] = set()
    for csk in career:
        best = 0.0
        for psk in prof:
            if psk == csk or psk in csk or csk in psk:
                best = max(best, weights.get(psk, 0.5))
                matched_c.add(csk)
        inter_w += best
    union = len(prof | career)
    if union == 0:
        return 0.0
    # blend set jaccard with weight coverage of career skills
    jaccard = len(matched_c) / max(1, len(career | {p for p in prof}))
    coverage = inter_w / max(1.0, float(len(career)))
    return max(0.0, min(1.0, 0.5 * jaccard + 0.5 * min(1.0, coverage)))


def market_signal(seed_market: dict, region_pref: Optional[str]) -> float:
    """norm(demand)*(1+trend/200), optionally mild boost if region in top_regions — NEVER a filter."""
    demand = float(seed_market.get("demand_count_90d") or 0)
    trend = seed_market.get("trend_pct")
    trend_f = float(trend) if trend is not None else 0.0
    # log-normalize demand (seed max ~2k)
    norm_d = math.log1p(demand) / math.log1p(2000.0)
    norm_d = max(0.0, min(1.0, norm_d))
    signal = norm_d * (1.0 + max(-50.0, min(100.0, trend_f)) / 200.0)
    signal = max(0.0, min(1.0, signal / 1.5))  # keep roughly in 0..1
    if region_pref:
        tops = [str(r).lower() for r in (seed_market.get("top_regions") or [])]
        if region_pref.lower() in tops:
            signal = min(1.0, signal * 1.05)
    return min(MARKET_SIGNAL_CAP * 3, signal)  # raw before weight; weight applied later


def _capped_market_component(raw_signal: float, w_market: float) -> float:
    """Ensure market contribution ≤ MARKET_SIGNAL_CAP even if weight is high."""
    return min(MARKET_SIGNAL_CAP, w_market * raw_signal)


@lru_cache
def _load_embedding_index() -> tuple[Optional[np.ndarray], tuple[str, ...]]:
    if not CAREERS_NPY.is_file() or not CAREER_IDS_JSON.is_file():
        return None, tuple()
    try:
        ids = json.loads(CAREER_IDS_JSON.read_text(encoding="utf-8"))
        if isinstance(ids, dict):
            ids = ids.get("career_ids") or ids.get("ids") or []
        mat = np.load(CAREERS_NPY)
        if len(ids) != mat.shape[0]:
            log.warning("careers.npy / career_ids length mismatch — using dim fallback")
            return None, tuple()
        return mat, tuple(str(i) for i in ids)
    except Exception as exc:  # noqa: BLE001 — offline demo must not die
        log.warning("failed to load embeddings: %s", type(exc).__name__)
        return None, tuple()


def _hash_embed(text: str, dim: int) -> np.ndarray:
    """Deterministic bag-of-tokens projection for offline profile embedding."""
    vec = np.zeros(dim, dtype=np.float64)
    tokens = re.findall(r"[\wÀ-ỹ]+", text.lower())
    if not tokens:
        return vec
    for tok in tokens:
        h = hash(tok) % dim
        vec[h] += 1.0
    n = np.linalg.norm(vec)
    if n > 1e-12:
        vec /= n
    return vec


def cosine_fit(profile: Profile, career: dict) -> float:
    """Cosine similarity profile↔career (embeddings or dimension fallback)."""
    mat, ids = _load_embedding_index()
    cid = career["career_id"]
    if mat is not None and cid in ids:
        idx = ids.index(cid)
        dim = mat.shape[1]
        pvec = _hash_embed(profile_text(profile), dim)
        cvec = mat[idx].astype(np.float64)
        cn = np.linalg.norm(cvec)
        if cn > 1e-12:
            cvec = cvec / cn
        return float(max(0.0, min(1.0, np.dot(pvec, cvec))))
    # Dimension fallback (MI-06 not ready)
    return _cosine(_dim_vector(profile.dimensions), _dim_vector(career.get("dimensions") or {}))


def score_career(profile: Profile, career: dict, *, use_market: bool = True) -> dict[str, float]:
    settings = get_settings()
    cos = cosine_fit(profile, career)
    sk = skill_overlap(profile, (career.get("seed_market") or {}).get("top_skills") or [])
    raw_m = market_signal(career.get("seed_market") or {}, profile.constraints.region_pref)
    m_comp = _capped_market_component(raw_m, settings.w_market_signal) if use_market else 0.0
    total = settings.w_cosine * cos + settings.w_skill_overlap * sk + m_comp
    # When market disabled, renormalize human-fit weights for fair ranking
    if not use_market:
        wsum = settings.w_cosine + settings.w_skill_overlap
        if wsum > 0:
            total = (settings.w_cosine * cos + settings.w_skill_overlap * sk) / wsum
    return {
        "total": float(max(0.0, min(1.0, total))),
        "cosine": float(cos),
        "skill": float(sk),
        "market": float(raw_m),
        "market_component": float(m_comp),
    }


def top_k_careers(profile: Profile, k: int = 20) -> list[tuple[str, float, dict[str, float]]]:
    """Rank all careers; region never drops a career."""
    scored: list[tuple[str, float, dict[str, float]]] = []
    for c in load_careers():
        parts = score_career(profile, c, use_market=True)
        scored.append((c["career_id"], parts["total"], parts))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


def pick_stretch(
    ranked: list[tuple[str, float, dict[str, float]]],
    profile: Profile,
    top5_ids: set[str],
) -> tuple[str, float]:
    user_dom = dominant_dimension(profile.dimensions)
    # candidates from ranks 6..15 first, then any non-top5
    pool = ranked[5:15] or ranked[5:] or ranked
    best: Optional[tuple[str, float]] = None
    for cid, sc, _ in pool:
        if cid in top5_ids:
            continue
        career = get_career(cid)
        if not career:
            continue
        c_dom = dominant_dimension(career.get("dimensions") or {})
        if c_dom != user_dom:
            if best is None or sc > best[1]:
                best = (cid, sc)
    if best:
        return best
    # fallback: best not in top5
    for cid, sc, _ in ranked:
        if cid not in top5_ids:
            return cid, sc
    # absolute fallback: last of ranked
    return ranked[-1][0], ranked[-1][1]


def _market_stats(career: dict) -> MarketStats:
    m = career.get("seed_market") or {}
    return MarketStats(
        demand_count_90d=int(m.get("demand_count_90d") or 0),
        entry_level_count_90d=int(m.get("entry_level_count_90d") or max(0, int((m.get("demand_count_90d") or 0) * 0.2))),
        salary_p25_trieu=m.get("salary_p25_trieu"),
        salary_p50_trieu=m.get("salary_p50_trieu"),
        salary_p75_trieu=m.get("salary_p75_trieu"),
        trend_pct=m.get("trend_pct"),
        salary_sample_count=int(m.get("salary_sample_count") or 30),
        low_confidence=bool(m.get("low_confidence", False)),
        top_regions=list(m.get("top_regions") or []),
        top_skills=list(m.get("top_skills") or []),
        source_note=str(
            m.get("source_note")
            or "Dữ liệu mẫu (seed) — thay bằng số thật sau MI-04"
        ),
    )


def _counterfactual_text(profile: Profile, current_id: str) -> str:
    """Flip dominant dimension ±0.3 and re-score; report new top if different."""
    dom = dominant_dimension(profile.dimensions)
    # shallow copy profile dims
    alt = profile.model_copy(deep=True)
    for k in DIM_KEYS:
        alt.dimensions[k] = float(alt.dimensions.get(k, 0.0) or 0.0)
    # boost a different dimension
    others = [k for k in DIM_KEYS if k != dom]
    target = max(others, key=lambda k: float(alt.dimensions.get(k, 0.0) or 0.0)) if others else dom
    if target == dom and others:
        target = others[0]
    alt.dimensions[target] = min(1.0, float(alt.dimensions.get(target, 0.0) or 0.0) + 0.3)
    alt.dimensions[dom] = max(0.0, float(alt.dimensions.get(dom, 0.0) or 0.0) - 0.15)
    ranked = top_k_careers(alt, k=5)
    if not ranked:
        return "Nếu hồ sơ đổi, gợi ý có thể thay đổi — đây chỉ là tham khảo."
    new_id, _, _ = ranked[0]
    if new_id == current_id and len(ranked) > 1:
        new_id = ranked[1][0]
    career = get_career(new_id)
    title = career["title"] if career else new_id
    return (
        f"Nếu bạn thiên về {DIM_LABELS_VI.get(target, target)} hơn "
        f"{DIM_LABELS_VI.get(dom, dom)}, gợi ý đầu bảng có thể là {title}."
    )


def build_recommendation(
    profile: Profile,
    career_id: str,
    score: float,
    *,
    is_stretch: bool = False,
) -> Recommendation:
    career = get_career(career_id)
    if not career:
        raise KeyError(career_id)
    market = _market_stats(career)
    routes = pathways.ensure_routes(career, journey_mode=profile.journey_mode)
    roadmap = pathways.ensure_skill_roadmap(career)
    # PR-06: grounded evidence (code selects quotes/stats; LLM optional; template fallback)
    cf = _counterfactual_text(profile, career_id)
    why = evidence_service.build_why(
        profile=profile,
        career=career,
        market=market,
        counterfactual=cf,
    )
    return Recommendation(
        career_id=career_id,
        title=career["title"],
        match_score=round(float(score), 4),
        is_stretch=is_stretch,
        why=why,
        market=market,
        routes=routes,
        skill_roadmap=roadmap,
        job_readiness=pathways.build_job_readiness(profile, career),
    )


def recommend(profile: Profile) -> tuple[list[Recommendation], Recommendation]:
    """Return (top5, stretch). Same engine for Explore and Launch."""
    ranked = top_k_careers(profile, k=20)
    if not ranked:
        # pathological empty KB
        raise RuntimeError("career KB empty")
    top5_raw = ranked[:5]
    # pad if KB smaller than 5
    while len(top5_raw) < 5 and ranked:
        top5_raw.append(ranked[len(top5_raw) % len(ranked)])
    top5_ids = {cid for cid, _, _ in top5_raw[:5]}
    stretch_id, stretch_score = pick_stretch(ranked, profile, top5_ids)
    top5 = [
        build_recommendation(profile, cid, sc, is_stretch=False)
        for cid, sc, _ in top5_raw[:5]
    ]
    stretch = build_recommendation(profile, stretch_id, stretch_score, is_stretch=True)
    return top5, stretch
