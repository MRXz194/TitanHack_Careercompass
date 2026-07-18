"""PR-05 unit tests — scoring weights, region non-filter, market cap, stretch."""
from __future__ import annotations

import pytest

from app.core.config import get_settings
from app.data.seed_loader import load_careers
from app.models.schemas import ExperienceEvidence, Profile, ProfileSkill
from app.services import matching


pytestmark = pytest.mark.unit


def _tech_profile(**kwargs) -> Profile:
    base = dict(
        session_id="m-tech",
        journey_mode="explore",
        dimensions={
            "ky_thuat": 0.9,
            "phan_tich": 0.4,
            "sang_tao": 0.2,
            "xa_hoi": 0.2,
            "quan_ly": 0.1,
        },
        skills=[
            ProfileSkill(name="hàn dây điện", level="ok", source_quote="em hay hàn dây"),
            ProfileSkill(name="sửa chữa", source_quote="em sửa quạt"),
        ],
        interests=["sửa đồ điện", "máy móc"],
        evidence_quotes=[],
    )
    base.update(kwargs)
    return Profile(**base)


def test_profile_text_excludes_region_and_has_no_gender_field() -> None:
    p = _tech_profile()
    p.constraints.region_pref = "hanoi"
    text = matching.profile_text(p)
    assert "hanoi" not in text.lower()
    assert "gender" not in text.lower()
    assert "hàn dây" in text or "sửa" in text


def test_skill_overlap_and_cosine_in_unit_range() -> None:
    p = _tech_profile()
    careers = load_careers()
    dien = next(c for c in careers if c["career_id"] == "ky-thuat-vien-dien-lanh")
    parts = matching.score_career(p, dien)
    assert 0.0 <= parts["cosine"] <= 1.0
    assert 0.0 <= parts["skill"] <= 1.0
    assert 0.0 <= parts["total"] <= 1.0


def test_skill_overlap_short_token_does_not_spuriously_match() -> None:
    """1c: a bare "C" skill must not inflate overlap against "CI/CD" via substring
    containment — shares the length-guarded primitive with pathways.skill_match."""
    p = Profile(
        session_id="short-tok",
        journey_mode="explore",
        skills=[ProfileSkill(name="C", source_quote="em học ngôn ngữ C ở trường")],
    )
    overlap_unrelated = matching.skill_overlap(p, ["CI/CD", "Kubernetes"])
    assert overlap_unrelated == 0.0
    overlap_exact = matching.skill_overlap(p, ["C", "Kubernetes"])
    assert overlap_exact > 0.0


def test_market_component_is_capped() -> None:
    settings = get_settings()
    # Even with huge demand, market contribution after cap logic ≤ MARKET_SIGNAL_CAP
    huge = {"demand_count_90d": 10_000_000, "trend_pct": 500, "top_regions": ["hcm"]}
    raw = matching.market_signal(huge, "hcm")
    comp = matching._capped_market_component(raw, settings.w_market_signal)
    assert comp <= matching.MARKET_SIGNAL_CAP + 1e-9


def test_market_cannot_dominate_low_fit() -> None:
    """Low human-fit profile should not rank a random high-demand career first solely via market."""
    p = Profile(
        session_id="low-fit",
        dimensions={k: 0.0 for k in matching.DIM_KEYS},
        skills=[],
        interests=[],
    )
    # Force dimensions toward social care
    p.dimensions["xa_hoi"] = 0.95
    p.skills = [ProfileSkill(name="chăm sóc bệnh nhân", source_quote="em thích chăm người ốm")]
    ranked = matching.top_k_careers(p, k=10)
    top_id, top_score, top_detail = ranked[0]
    # Real market.db now reports honest per-career demand (often 0 for careers absent
    # from this small IT-skewed crawl sample, e.g. "dieu-duong") instead of a fabricated
    # seed number — so which exact social career wins a close race can shift with real
    # data. The actual invariant: the WINNER must be won on human-fit (cosine), not
    # carried by market_component, and must not be an unrelated tech/market-spike pick.
    assert top_id != "lap-trinh-vien-web"
    assert top_detail["cosine"] >= 0.7
    assert top_detail["cosine"] > top_detail["market_component"]


def test_region_does_not_change_candidate_set() -> None:
    p1 = _tech_profile(session_id="r1")
    p1.constraints.region_pref = "hanoi"
    p2 = _tech_profile(session_id="r2")
    p2.constraints.region_pref = "danang"
    n = len(load_careers())
    # Rank full KB — region may reorder but must not drop any career.
    set1 = {cid for cid, _, _ in matching.top_k_careers(p1, k=n)}
    set2 = {cid for cid, _, _ in matching.top_k_careers(p2, k=n)}
    assert set1 == set2
    assert len(set1) == n


def test_personal_signal_guard_rejects_blank_and_accepts_evidence() -> None:
    blank = Profile(session_id="blank-personal-signal")
    assert matching.has_personal_signal(blank) is False

    with_evidence = Profile(
        session_id="evidence-personal-signal",
        skills=[ProfileSkill(name="Excel", source_quote="em dùng Excel")],
    )
    assert matching.has_personal_signal(with_evidence) is True


def test_recommend_returns_top5_and_stretch() -> None:
    p = _tech_profile()
    top5, stretch = matching.recommend(p)
    assert len(top5) == 5
    assert stretch.is_stretch is True
    assert all(not r.is_stretch for r in top5)
    assert all(len(r.routes) >= 2 for r in top5)
    assert all(
        any(rt.type in ("vocational", "college", "certificate") for rt in r.routes)
        for r in top5
    )
    ids = {r.career_id for r in top5}
    # stretch should expand choices — preferably not duplicate all of top5 only
    assert stretch.career_id
    # scores sorted non-increasing among top5
    scores = [r.match_score for r in top5]
    assert scores == sorted(scores, reverse=True)


def test_top_k_careers_tie_break_is_deterministic_by_career_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """2a: ties must break by career_id, not incidental KB iteration order."""
    fake_careers = [
        {"career_id": "zzz-last", "title": "Z", "dimensions": {}, "seed_market": {}},
        {"career_id": "aaa-first", "title": "A", "dimensions": {}, "seed_market": {}},
    ]
    monkeypatch.setattr(matching, "load_careers", lambda: fake_careers)
    monkeypatch.setattr(
        matching,
        "score_career",
        lambda profile, career, use_market=True: {
            "total": 0.5, "cosine": 0.5, "skill": 0.0, "market": 0.0, "market_component": 0.0,
        },
    )
    ranked = matching.top_k_careers(_tech_profile(), k=10)
    assert [cid for cid, _, _ in ranked] == ["aaa-first", "zzz-last"]


def test_pick_stretch_full_scan_fallback_finds_dimension_diverse_career(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """2b: if ranks 6..15 all share the user's dominant dimension, the fallback must keep
    scanning the FULL ranked list for a dimension-diverse career before giving up the
    "expand choices" guarantee — not silently drop the filter."""
    user_dom_dims = {"ky_thuat": 0.9, "phan_tich": 0.1, "sang_tao": 0.1, "xa_hoi": 0.1, "quan_ly": 0.1}
    same_dom = {"ky_thuat": 0.8, "phan_tich": 0.2, "sang_tao": 0.1, "xa_hoi": 0.1, "quan_ly": 0.1}
    diverse_dom = {"ky_thuat": 0.1, "phan_tich": 0.1, "sang_tao": 0.1, "xa_hoi": 0.9, "quan_ly": 0.1}

    ranked = [(f"top{i}", 0.9 - i * 0.01, {}) for i in range(5)]
    ranked += [(f"same{i}", 0.5 - i * 0.01, {}) for i in range(10)]  # ranks 6..15
    ranked += [("diverse-1", 0.1, {})]  # only found via full-scan fallback

    def _fake_get_career(cid: str):
        if cid.startswith("top") or cid.startswith("same"):
            return {"career_id": cid, "dimensions": same_dom}
        if cid == "diverse-1":
            return {"career_id": cid, "dimensions": diverse_dom}
        return None

    monkeypatch.setattr(matching, "get_career", _fake_get_career)
    profile = Profile(session_id="stretch-fallback", journey_mode="explore", dimensions=user_dom_dims)
    top5_ids = {f"top{i}" for i in range(5)}
    stretch_id, _ = matching.pick_stretch(ranked, profile, top5_ids)
    assert stretch_id == "diverse-1"


def test_recommend_top5_never_duplicates_career_id_when_kb_smaller_than_five(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """2c: KB smaller than 5 must yield fewer unique recommendations, never the same
    career_id padded in twice as if it were two distinct suggestions."""
    real_careers = load_careers()[:3]
    monkeypatch.setattr(matching, "load_careers", lambda: real_careers)
    top5, stretch = matching.recommend(_tech_profile())
    ids = [r.career_id for r in top5]
    assert len(ids) == len(set(ids))
    assert len(ids) <= 3
    assert stretch.career_id


def test_tech_profile_prefers_technical_careers() -> None:
    p = _tech_profile()
    top5, _ = matching.recommend(p)
    top_ids = [r.career_id for r in top5]
    # At least one hands-on technical role near the top
    assert any(
        cid in top_ids[:3]
        for cid in ("ky-thuat-vien-dien-lanh", "co-khi-cnc", "lap-trinh-vien-web")
    )


def test_launch_readiness_matched_has_evidence() -> None:
    p = Profile(
        session_id="launch-1",
        journey_mode="launch",
        dimensions={"phan_tich": 0.85, "ky_thuat": 0.3, "sang_tao": 0.2, "xa_hoi": 0.2, "quan_ly": 0.2},
        skills=[ProfileSkill(name="Excel", source_quote="em làm dashboard Excel")],
        experiences=[
            ExperienceEvidence(
                title="Dashboard",
                kind="project",
                skills=["Excel"],
                source_quote="em làm dashboard Excel",
            )
        ],
        interests=["dữ liệu"],
    )
    top5, _ = matching.recommend(p)
    # find a rec with readiness
    with_ready = [r for r in top5 if r.job_readiness is not None]
    assert with_ready
    jr = with_ready[0].job_readiness
    assert jr is not None
    for m in jr.matched_skills:
        assert m.evidence
    # missing and matched disjoint
    matched_names = {_normalize(m.skill) for m in jr.matched_skills}
    for miss in jr.missing_skills:
        assert _normalize(miss) not in matched_names


def _normalize(s: str) -> str:
    return s.strip().lower()


def test_weights_come_from_settings() -> None:
    s = get_settings()
    assert abs((s.w_cosine + s.w_skill_overlap + s.w_market_signal) - 1.0) < 1e-6
