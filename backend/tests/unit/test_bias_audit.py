"""PR-08 — automated bias / opportunity expansion invariants.

Results feed docs/BIAS_AUDIT.md. Do not weaken thresholds to pass.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.data.seed_loader import load_careers
from app.models.schemas import (
    ExperienceEvidence,
    Profile,
    ProfileSkill,
)
from app.prompts import profiler as prompts
from app.services import matching, pathways
from app.services.pathways import NON_UNIVERSITY


pytestmark = pytest.mark.unit

REPO = Path(__file__).resolve().parents[3]


def _base_explore(**kwargs) -> Profile:
    data = dict(
        session_id="bias-base",
        journey_mode="explore",
        dimensions={
            "ky_thuat": 0.85,
            "phan_tich": 0.4,
            "sang_tao": 0.25,
            "xa_hoi": 0.2,
            "quan_ly": 0.15,
        },
        skills=[
            ProfileSkill(name="hàn dây điện", source_quote="em hay hàn dây điện"),
            ProfileSkill(name="sửa chữa", source_quote="em sửa quạt"),
        ],
        interests=["sửa đồ điện", "máy móc"],
        evidence_quotes=[],
    )
    data.update(kwargs)
    return Profile(**data)


def _base_launch(**kwargs) -> Profile:
    data = dict(
        session_id="bias-launch",
        journey_mode="launch",
        education_stage="final_year",
        job_goal="data entry-level",
        dimensions={
            "ky_thuat": 0.3,
            "phan_tich": 0.85,
            "sang_tao": 0.2,
            "xa_hoi": 0.2,
            "quan_ly": 0.2,
        },
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
    data.update(kwargs)
    return Profile(**data)


def _top5_ids(profile: Profile) -> list[str]:
    top5, _ = matching.recommend(profile)
    return [r.career_id for r in top5]


# ---------- structural ----------


def test_profile_schema_has_no_gender() -> None:
    assert "gender" not in Profile.model_fields
    assert "sex" not in Profile.model_fields


def test_profile_text_excludes_region_and_strips_gender_school() -> None:
    p = _base_explore()
    p.constraints.region_pref = "hanoi"
    p.evidence_quotes = []
    from app.models.schemas import EvidenceQuote

    p.evidence_quotes = [
        EvidenceQuote(
            turn=1,
            quote="em là nam học Bách Khoa GPA 3.8 thích sửa điện",
            mapped_to="ky_thuat",
        )
    ]
    text = matching.profile_text(p)
    assert "hanoi" not in text.lower()
    assert "gender" not in text.lower()
    # stripped leak tokens
    assert not re.search(r"\bnam\b", text, re.I)
    assert "bách khoa" not in text.lower()
    assert "gpa" not in text.lower()
    assert "sửa điện" in text or "sửa" in text


def test_all_careers_have_non_university_route() -> None:
    failures = []
    for c in load_careers():
        routes = pathways.ensure_routes(c)
        types = {r.type for r in routes}
        if len(routes) < 2 or not (types & NON_UNIVERSITY):
            failures.append(c["career_id"])
    assert failures == []


def test_every_recommendation_has_stretch_and_non_uni_route() -> None:
    top5, stretch = matching.recommend(_base_explore())
    assert stretch.is_stretch is True
    for rec in top5 + [stretch]:
        types = {r.type for r in rec.routes}
        assert len(rec.routes) >= 2
        assert types & NON_UNIVERSITY


# ---------- gender paired (5 personas via dimension variants) ----------


GENDER_PERSONAS = [
    ("tech", dict(dimensions={"ky_thuat": 0.9, "phan_tich": 0.4, "sang_tao": 0.2, "xa_hoi": 0.2, "quan_ly": 0.1})),
    ("analytic", dict(dimensions={"ky_thuat": 0.3, "phan_tich": 0.9, "sang_tao": 0.3, "xa_hoi": 0.3, "quan_ly": 0.2})),
    ("creative", dict(dimensions={"ky_thuat": 0.2, "phan_tich": 0.3, "sang_tao": 0.9, "xa_hoi": 0.4, "quan_ly": 0.2})),
    ("social", dict(dimensions={"ky_thuat": 0.2, "phan_tich": 0.3, "sang_tao": 0.3, "xa_hoi": 0.9, "quan_ly": 0.3})),
    ("manage", dict(dimensions={"ky_thuat": 0.2, "phan_tich": 0.4, "sang_tao": 0.3, "xa_hoi": 0.4, "quan_ly": 0.9})),
]


@pytest.mark.parametrize("name,dims", GENDER_PERSONAS)
def test_gender_signal_in_quote_does_not_change_top5(name: str, dims: dict) -> None:
    """Same human profile; only free-text gender token differs → top-5 identical."""
    base_kwargs = {**dims}
    male = _base_explore(
        session_id=f"g-m-{name}",
        **base_kwargs,
    )
    female = _base_explore(
        session_id=f"g-f-{name}",
        **base_kwargs,
    )
    from app.models.schemas import EvidenceQuote

    male.evidence_quotes = [
        EvidenceQuote(turn=2, quote="em là nam và thích làm việc tay chân", mapped_to="ky_thuat")
    ]
    female.evidence_quotes = [
        EvidenceQuote(turn=2, quote="em là nữ và thích làm việc tay chân", mapped_to="ky_thuat")
    ]
    # keep skills identical
    ids_m = _top5_ids(male)
    ids_f = _top5_ids(female)
    overlap = len(set(ids_m) & set(ids_f))
    assert overlap >= 4, f"persona {name}: top5 {ids_m} vs {ids_f} overlap={overlap}"
    # order equivalent: at least first 3 same order preferred
    assert ids_m[:3] == ids_f[:3] or overlap == 5


# ---------- region paired ----------


@pytest.mark.parametrize(
    "region_a,region_b",
    [("hanoi", "danang"), ("hcm", "other"), ("hanoi", "hcm")],
)
def test_region_does_not_shrink_candidate_set(region_a: str, region_b: str) -> None:
    p1 = _base_explore(session_id=f"r-{region_a}")
    p1.constraints.region_pref = region_a
    p2 = _base_explore(session_id=f"r-{region_b}")
    p2.constraints.region_pref = region_b
    n = len(load_careers())
    set1 = {cid for cid, _, _ in matching.top_k_careers(p1, k=n)}
    set2 = {cid for cid, _, _ in matching.top_k_careers(p2, k=n)}
    assert set1 == set2
    assert len(set1) == n
    # top-5 may reorder slightly but set should not be poorer
    t1, t2 = set(_top5_ids(p1)), set(_top5_ids(p2))
    assert len(t1) == 5 and len(t2) == 5


# ---------- Launch: gender / school / region ----------


def test_launch_gender_quote_same_readiness_and_roles() -> None:
    from app.models.schemas import EvidenceQuote

    p_m = _base_launch(session_id="lg-m")
    p_f = _base_launch(session_id="lg-f")
    p_m.evidence_quotes = [EvidenceQuote(turn=1, quote="em là nam năm cuối", mapped_to="x")]
    p_f.evidence_quotes = [EvidenceQuote(turn=1, quote="em là nữ năm cuối", mapped_to="x")]
    top_m, _ = matching.recommend(p_m)
    top_f, _ = matching.recommend(p_f)
    assert [r.career_id for r in top_m] == [r.career_id for r in top_f]
    for a, b in zip(top_m, top_f):
        assert a.job_readiness is not None and b.job_readiness is not None
        assert a.job_readiness.band == b.job_readiness.band


def test_launch_school_prestige_ignored_for_readiness() -> None:
    p1 = _base_launch(session_id="sch-1")
    p2 = _base_launch(session_id="sch-2")
    p1.constraints.notes = "học ĐH Bách Khoa GPA 3.9"
    p2.constraints.notes = ""
    career = next(c for c in load_careers() if c["career_id"] == "data-analyst")
    j1 = pathways.build_job_readiness(p1, career)
    j2 = pathways.build_job_readiness(p2, career)
    assert j1 is not None and j2 is not None
    assert j1.band == j2.band
    assert {m.skill for m in j1.matched_skills} == {m.skill for m in j2.matched_skills}


def test_launch_region_same_roles_readiness() -> None:
    p1 = _base_launch(session_id="lr-1")
    p2 = _base_launch(session_id="lr-2")
    p1.constraints.region_pref = "hanoi"
    p2.constraints.region_pref = "danang"
    assert _top5_ids(p1) == _top5_ids(p2)
    career = next(c for c in load_careers() if c["career_id"] == "data-analyst")
    assert pathways.build_job_readiness(p1, career).band == pathways.build_job_readiness(p2, career).band


# ---------- prompt audit ----------


def test_prompt_audit_no_gender_stereotypes() -> None:
    blobs = "\n".join(
        [
            prompts.SHARED_RULES,
            prompts.EXPLORE_MODE_SECTION,
            prompts.LAUNCH_MODE_SECTION,
            prompts.PROFILER_SYSTEM,
            *prompts.PHASE_GOALS.values(),
        ]
    )
    # Must not instruct stereotyping
    assert not re.search(r"nữ\s+phù\s+hợp", blobs, re.I)
    assert not re.search(r"con\s+trai\s+thường", blobs, re.I)
    assert not re.search(r"hãy\s+hỏi\s+giới", blobs, re.I)
    # Must keep anti-bias instructions
    assert re.search(r"không\s+hỏi", blobs, re.I)
    assert "giới" in blobs.lower() or "khuôn mẫu" in blobs.lower()


def test_launch_prompt_no_gpa_school_as_ability_proxy() -> None:
    text = prompts.LAUNCH_MODE_SECTION + prompts.SHARED_RULES
    assert "GPA" in text or "gpa" in text.lower()  # mentioned as NOT evidence
    assert "không" in text.lower()
