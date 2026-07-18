"""PR-07 unit tests — routes, Launch readiness invariants, Explore null."""
from __future__ import annotations

import pytest

from app.data.seed_loader import load_careers
from app.models.schemas import ExperienceEvidence, Profile, ProfileSkill
from app.services import matching, pathways
from app.services.pathways import NON_UNIVERSITY


pytestmark = pytest.mark.unit


def _launch_profile_excel() -> Profile:
    return Profile(
        session_id="launch-excel",
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
        skills=[
            ProfileSkill(name="Excel", source_quote="em làm dashboard bằng Excel"),
        ],
        experiences=[
            ExperienceEvidence(
                title="Dashboard bán hàng",
                kind="project",
                skills=["Excel"],
                source_quote="em làm dashboard bằng Excel",
            )
        ],
        interests=["dữ liệu"],
    )


def test_ensure_routes_all_seed_careers() -> None:
    for c in load_careers():
        routes = pathways.ensure_routes(c, journey_mode="explore")
        assert len(routes) >= 2
        assert any(r.type in NON_UNIVERSITY for r in routes)


def test_launch_reorders_non_university_first() -> None:
    career = {
        "routes": [
            {
                "type": "university",
                "label": "ĐH",
                "detail": "",
                "first_steps": ["a"],
            },
            {
                "type": "certificate",
                "label": "Chứng chỉ",
                "detail": "",
                "first_steps": ["b"],
            },
        ],
        "seed_market": {},
    }
    routes = pathways.ensure_routes(career, journey_mode="launch")
    assert routes[0].type in NON_UNIVERSITY


def test_explore_job_readiness_is_null() -> None:
    p = Profile(session_id="ex", journey_mode="explore")
    career = load_careers()[0]
    assert pathways.build_job_readiness(p, career) is None
    top5, stretch = matching.recommend(p)
    assert all(r.job_readiness is None for r in top5)
    assert stretch.job_readiness is None


def test_launch_matched_missing_invariants() -> None:
    p = _launch_profile_excel()
    # pick data-analyst-like career if present
    career = next(
        (c for c in load_careers() if "Excel" in " ".join(c.get("seed_market", {}).get("top_skills", []))),
        load_careers()[0],
    )
    tops = list((career.get("seed_market") or {}).get("top_skills") or [])
    jr = pathways.build_job_readiness(p, career)
    assert jr is not None
    pathways.validate_job_readiness(jr, tops)
    matched_n = {m.skill.lower() for m in jr.matched_skills}
    missing_n = {s.lower() for s in jr.missing_skills}
    assert matched_n.isdisjoint(missing_n)
    for m in jr.matched_skills:
        assert m.evidence


def test_missing_subset_of_role_top_skills() -> None:
    p = _launch_profile_excel()
    career = next(c for c in load_careers() if c["career_id"] == "data-analyst")
    tops = {(s or "").lower() for s in career["seed_market"]["top_skills"]}
    jr = pathways.build_job_readiness(p, career)
    assert jr is not None
    for miss in jr.missing_skills:
        # soft: each missing is from tops (exact or we stored canonical top skill)
        assert miss.lower() in tops or any(miss.lower() in t or t in miss.lower() for t in tops)


def test_actions_four_weeks_with_deliverable() -> None:
    p = _launch_profile_excel()
    career = next(c for c in load_careers() if c["career_id"] == "data-analyst")
    jr = pathways.build_job_readiness(p, career)
    assert jr is not None
    assert len(jr.actions_30d) == 4
    assert {a.week for a in jr.actions_30d} == {1, 2, 3, 4}
    for a in jr.actions_30d:
        assert a.deliverable.strip()
        assert "học thêm" not in a.action.lower()


def test_search_queries_safe() -> None:
    career = {"title": "Data Analyst", "seed_market": {"top_skills": ["SQL"]}, "title_patterns": ["data analyst"]}
    qs = pathways.build_search_queries(career, ["SQL"])
    assert 2 <= len(qs) <= 4
    blob = " ".join(qs).lower()
    assert "giới tính" not in blob
    assert "gpa" not in blob
    assert "con gái" not in blob


def test_region_does_not_change_readiness_band() -> None:
    p1 = _launch_profile_excel()
    p1.constraints.region_pref = "hanoi"
    p2 = _launch_profile_excel()
    p2.session_id = "launch-excel-2"
    p2.constraints.region_pref = "danang"
    career = next(c for c in load_careers() if c["career_id"] == "data-analyst")
    b1 = pathways.build_job_readiness(p1, career)
    b2 = pathways.build_job_readiness(p2, career)
    assert b1 is not None and b2 is not None
    assert b1.band == b2.band
    assert {m.skill for m in b1.matched_skills} == {m.skill for m in b2.matched_skills}


def test_market_demand_does_not_raise_band_for_empty_skills() -> None:
    """Low evidence profile stays build_foundation even if career has huge demand."""
    p = Profile(
        session_id="empty-launch",
        journey_mode="launch",
        skills=[],
        experiences=[],
        interests=[],
    )
    career = {
        "title": "Hot Job",
        "seed_market": {
            "top_skills": ["SQL", "Python", "Spark", "Airflow"],
            "demand_count_90d": 99999,
            "trend_pct": 200,
        },
    }
    jr = pathways.build_job_readiness(p, career)
    assert jr is not None
    assert jr.band == "build_foundation"
    assert jr.matched_skills == []
    assert set(jr.missing_skills) <= set(career["seed_market"]["top_skills"])


@pytest.mark.parametrize(
    "short,long_unrelated",
    [
        ("C", "CI/CD"),
        ("C", "C#"),
        ("Go", "Google"),
        ("AI", "Amazon Web Services"),
        ("R", "HR"),
    ],
)
def test_skill_match_short_tokens_require_exact_match(short: str, long_unrelated: str) -> None:
    """1c: a bare short skill label must not spuriously containment-match an unrelated
    longer label just because the short string happens to be a substring of it."""
    assert pathways.skill_match(short, long_unrelated) is False


def test_skill_match_exact_short_tokens_still_match() -> None:
    assert pathways.skill_match("Go", "go") is True
    assert pathways.skill_match("C#", "c#") is True


def test_skill_match_long_tokens_still_use_containment() -> None:
    assert pathways.skill_match("Excel", "Microsoft Excel nâng cao") is True


def test_check_routes_script_logic() -> None:
    """Mirror scripts/check_routes.py on current seed."""
    failures = []
    for c in load_careers():
        routes = pathways.ensure_routes(c)
        types = {r.type for r in routes}
        if len(routes) < 2 or not (types & NON_UNIVERSITY):
            failures.append(c["career_id"])
    assert failures == []
