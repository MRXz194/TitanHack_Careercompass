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
    top_id = ranked[0][0]
    # Should prefer dieu-duong-like over pure market spike web dev when fit is social
    assert top_id in ("dieu-duong", "digital-marketing", "ke-toan", "logistics-van-hanh") or ranked[0][2]["skill"] >= ranked[0][2]["market_component"]


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
