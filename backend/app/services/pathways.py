"""Study pathways + Graduate Launch readiness — PR-07.

Design: docs/GRADUATE_LAUNCH.md, docs/AI_DESIGN.md §4.
Explore: job_readiness is always null.
Launch: matched/missing/band/queries/actions with hard invariants.

Invariants (enforced in code + tests):
- routes.length >= 2 and >=1 type in {vocational, college, certificate}
- matched ∩ missing = ∅
- missing ⊆ role market top_skills
- every matched skill has evidence from profile skills.source_quote or experiences
- exactly 4 actions, weeks 1..4, each with non-empty deliverable
- search queries 2..4, no gender/age/school prestige terms
- readiness band never uses gender/school/GPA/region as input
- market demand does not raise readiness band for low skill coverage
"""
from __future__ import annotations

import re
from typing import Optional

from app.core.config import get_settings
from app.models.schemas import (
    JobReadiness,
    LaunchAction,
    Profile,
    Route,
    SkillEvidence,
    SkillRoadmapItem,
)

NON_UNIVERSITY = frozenset({"vocational", "college", "certificate"})
SENSITIVE_QUERY_PATTERNS = (
    r"\bnam\b",
    r"\bnữ\b",
    r"giới\s*tính",
    r"\btuổi\b",
    r"\bGPA\b",
    r"đại\s*học\s+bách",
    r"NEU\b",
    r"FTU\b",
    r"con\s+gái",
    r"con\s+trai",
)


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def skill_match(a: str, b: str) -> bool:
    """Soft equality for skill labels (substring either way)."""
    an, bn = _normalize(a), _normalize(b)
    if not an or not bn:
        return False
    return an == bn or an in bn or bn in an


def ensure_routes(career: dict, *, journey_mode: str = "explore") -> list[Route]:
    """Guarantee ≥2 routes and ≥1 non-university; Launch reorders entry-friendly first."""
    raw = list(career.get("routes") or [])
    routes = [Route(**r) if not isinstance(r, Route) else r for r in raw]

    if len(routes) < 2:
        routes.append(
            Route(
                type="certificate",
                label="Chứng chỉ / khóa nghề ngắn hạn",
                detail="Bổ sung kỹ năng thực hành, ưu tiên portfolio",
                first_steps=["Chọn một kỹ năng cốt lõi và làm 1 output nhỏ có thể khoe"],
            )
        )
    if not any(r.type in NON_UNIVERSITY for r in routes):
        routes.append(
            Route(
                type="vocational",
                label="Lộ trình nghề / trung cấp",
                detail="Đường không bắt buộc đại học 4 năm",
                first_steps=["Tìm hiểu chương trình nghề gần nơi bạn sống"],
            )
        )

    # Deterministic roadmap fallback labels only — no invented school/company brands
    if journey_mode == "launch":
        # Prefer certificate / vocational / college before university for entry launch
        order = {"certificate": 0, "vocational": 1, "college": 2, "university": 3}
        routes = sorted(routes, key=lambda r: order.get(r.type, 9))

    return routes


def ensure_skill_roadmap(career: dict) -> list[SkillRoadmapItem]:
    items = career.get("skill_roadmap") or []
    out = [SkillRoadmapItem(**s) if not isinstance(s, SkillRoadmapItem) else s for s in items]
    if out:
        return out
    # Fallback from top_skills — status generic, no fake course names
    tops = list((career.get("seed_market") or {}).get("top_skills") or [])[:4]
    return [
        SkillRoadmapItem(skill=s, status="nen-hoc-truoc" if i == 0 else "hoc-trong-truong")
        for i, s in enumerate(tops)
    ]


def collect_evidenced_skills(profile: Profile) -> list[tuple[str, str]]:
    """(skill_name, evidence_text) only when evidence exists."""
    out: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(name: str, evidence: str) -> None:
        n = (name or "").strip()
        e = (evidence or "").strip()
        if not n or not e:
            return
        key = _normalize(n)
        if key in seen:
            return
        seen.add(key)
        out.append((n, e[:240]))

    for s in profile.skills:
        if s.source_quote:
            add(s.name, s.source_quote)
    for exp in profile.experiences:
        ev = exp.source_quote or exp.title
        for sk in exp.skills or []:
            add(sk, ev)
        # title alone is not a market skill match target unless listed in skills
    return out


def compute_matched_missing(
    profile: Profile, role_top_skills: list[str]
) -> tuple[list[SkillEvidence], list[str], float, int]:
    """Return matched, missing, coverage, evidence_strength."""
    tops = [s for s in role_top_skills if (s or "").strip()]
    evidenced = collect_evidenced_skills(profile)

    matched: list[SkillEvidence] = []
    matched_norm: set[str] = set()
    for role_skill in tops:
        rn = _normalize(role_skill)
        for name, evidence in evidenced:
            if skill_match(name, role_skill):
                if rn not in matched_norm:
                    matched.append(SkillEvidence(skill=role_skill, evidence=evidence))
                    matched_norm.add(rn)
                break

    missing = [s for s in tops if _normalize(s) not in matched_norm]
    # invariants
    matched_set = {_normalize(m.skill) for m in matched}
    missing_set = {_normalize(s) for s in missing}
    assert matched_set.isdisjoint(missing_set)
    top_set = {_normalize(s) for s in tops}
    assert missing_set <= top_set
    for m in matched:
        assert (m.evidence or "").strip()

    coverage = len(matched) / max(1, len(tops))
    # evidence_strength: matched skills backed by project/internship/work experience when possible
    exp_backed = 0
    for m in matched:
        for exp in profile.experiences:
            if exp.kind in ("project", "internship", "work", "volunteer", "coursework"):
                if any(skill_match(sk, m.skill) for sk in (exp.skills or [])) or skill_match(
                    exp.title, m.skill
                ):
                    exp_backed += 1
                    break
        else:
            # still counts if skill has source_quote
            if any(skill_match(s.name, m.skill) and s.source_quote for s in profile.skills):
                exp_backed += 1
    evidence_strength = max(exp_backed, len(matched))
    return matched, missing, coverage, evidence_strength


def readiness_band(
    coverage: float,
    evidence_strength: int,
    *,
    ready_coverage: float,
    near_coverage: float,
    min_evidence: int,
) -> tuple[str, str]:
    """Deterministic band — NOT hiring probability. Market must not boost this."""
    if coverage >= ready_coverage and evidence_strength >= min_evidence:
        return (
            "ready_now",
            "Bạn đã có bằng chứng cho nhiều kỹ năng vai trò thường yêu cầu — đây là mức chuẩn bị, không phải xác suất được tuyển.",
        )
    if coverage >= near_coverage:
        return (
            "near_ready",
            "Bạn đã có nền tảng; còn một số kỹ năng/role skills chưa có evidence trong hồ sơ.",
        )
    return (
        "build_foundation",
        "Hướng này cần thêm project/evidence kỹ năng cốt lõi trước khi tập trung ứng tuyển.",
    )


def build_search_queries(career: dict, missing: list[str]) -> list[str]:
    title = (career.get("title") or "việc entry-level").strip()
    aliases = list(career.get("entry_role_aliases") or career.get("title_patterns") or [])[:2]
    queries = [
        f"{title} fresher",
        f"{title} entry level",
        f"{title} thực tập",
    ]
    if aliases:
        queries.append(f"{aliases[0]} junior")
    if missing:
        queries.append(f"{title} {missing[0]}")
    # sanitize + unique, 2..4
    clean: list[str] = []
    seen: set[str] = set()
    for q in queries:
        qn = re.sub(r"\s+", " ", q).strip()
        if not qn or qn.lower() in seen:
            continue
        if any(re.search(p, qn, re.I) for p in SENSITIVE_QUERY_PATTERNS):
            continue
        seen.add(qn.lower())
        clean.append(qn)
        if len(clean) >= 4:
            break
    while len(clean) < 2:
        clean.append(f"{title} junior")
        break
    return clean[:4]


def build_actions_30d(missing: list[str], matched: list[SkillEvidence]) -> list[LaunchAction]:
    """Exactly 4 weeks; each action has a concrete deliverable (no bare 'học thêm')."""
    actions: list[LaunchAction] = []
    for week in range(1, 5):
        if week - 1 < len(missing):
            focus = missing[week - 1]
            action = f"Làm một mini-project/minh chứng tập trung vào «{focus}»"
            deliverable = f"1 link hoặc file tuần {week} (repo/notebook/PDF) thể hiện «{focus}»"
            why = f"Bổ sung evidence còn thiếu so với kỹ năng vai trò thường nêu: {focus}"
        elif matched:
            focus = matched[(week - 1) % len(matched)].skill
            action = f"Chỉnh portfolio để làm nổi bật «{focus}» đã có evidence"
            deliverable = f"1 bản cập nhật README/portfolio tuần {week} nêu rõ «{focus}» + link chứng minh"
            why = f"Tăng độ rõ của evidence đã có cho «{focus}» khi ứng tuyển entry-level"
        else:
            focus = "kỹ năng cốt lõi của vai trò"
            action = f"Chọn 1 kỹ năng role và tạo output nhỏ kiểm chứng được ({focus})"
            deliverable = f"1 artifact tuần {week} (file/link) + 3 bullet mô tả việc bạn đã làm"
            why = "Tạo bằng chứng đầu tiên thay vì chỉ liệt kê kỹ năng chung chung"
        # ban vague phrases
        assert "học thêm" not in action
        assert deliverable.strip()
        actions.append(
            LaunchAction(week=week, action=action, deliverable=deliverable, why=why)
        )
    assert len(actions) == 4
    assert {a.week for a in actions} == {1, 2, 3, 4}
    return actions


def build_job_readiness(profile: Profile, career: dict) -> Optional[JobReadiness]:
    """Explore → None. Launch → full JobReadiness object."""
    if profile.journey_mode != "launch":
        return None

    settings = get_settings()
    top_skills = list((career.get("seed_market") or {}).get("top_skills") or [])
    if not top_skills:
        # still return a conservative band with empty sets
        return JobReadiness(
            band="build_foundation",
            band_reason="Chưa có top skills thị trường cho vai trò này trong snapshot — hãy bổ sung project minh chứng chung.",
            matched_skills=[],
            missing_skills=[],
            search_queries=build_search_queries(career, []),
            actions_30d=build_actions_30d([], []),
        )

    matched, missing, coverage, evidence_strength = compute_matched_missing(profile, top_skills)
    band, reason = readiness_band(
        coverage,
        evidence_strength,
        ready_coverage=settings.readiness_ready_coverage,
        near_coverage=settings.readiness_near_coverage,
        min_evidence=settings.readiness_min_evidence_skills,
    )
    return JobReadiness(
        band=band,  # type: ignore[arg-type]
        band_reason=reason,
        matched_skills=matched,
        missing_skills=missing[:8],
        search_queries=build_search_queries(career, missing),
        actions_30d=build_actions_30d(missing, matched),
    )


def validate_job_readiness(jr: JobReadiness, role_top_skills: list[str]) -> None:
    """Raise AssertionError if invariants fail (used by tests)."""
    tops = {_normalize(s) for s in role_top_skills}
    matched_n = {_normalize(m.skill) for m in jr.matched_skills}
    missing_n = {_normalize(s) for s in jr.missing_skills}
    assert matched_n.isdisjoint(missing_n)
    assert missing_n <= tops
    for m in jr.matched_skills:
        assert (m.evidence or "").strip()
    assert len(jr.actions_30d) == 4
    assert {a.week for a in jr.actions_30d} == {1, 2, 3, 4}
    for a in jr.actions_30d:
        assert a.deliverable.strip()
        assert "học thêm" not in a.action.lower()
    assert 2 <= len(jr.search_queries) <= 4
    for q in jr.search_queries:
        assert not any(re.search(p, q, re.I) for p in SENSITIVE_QUERY_PATTERNS)
    assert jr.band in ("ready_now", "near_ready", "build_foundation")
