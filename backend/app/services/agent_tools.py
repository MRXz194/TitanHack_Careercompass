"""LangChain-typed local tools + registry — PR-12.

Tools are local/read-only or call existing CareerCompass services.
No browser/shell/arbitrary HTTP/config/KB write.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.data.seed_loader import get_career, load_careers
from app.models.agent_schemas import AgentStage
from app.models.schemas import Profile, ProfilePatch, ProfileSkill, Region, ResearchIntent
from app.prompts.profiler import get_fallback_question
from app.services import matching, pathways
from app.services.agent_policy import strip_privacy_text

TOOL_REGISTRY_VERSION = "agent-tools-v2-research"


# ---------- arg schemas ----------


class SessionStageInput(BaseModel):
    session_id_hash: str = Field(description="Opaque session ref")
    stage: str = Field(default="discover")
    journey_mode: str = Field(default="explore")
    phase: str = Field(default="interests")
    completeness: float = Field(default=0.0)
    interest_count: int = 0
    skill_count: int = 0
    experience_count: int = 0


class AskQuestionInput(BaseModel):
    session_id_hash: str = ""
    journey_mode: str = "explore"
    phase: str = "interests"
    focus_slot: str = "interests"
    turn_index: int = 0


class ExtractEvidenceInput(BaseModel):
    session_id_hash: str = ""
    message: str = ""
    journey_mode: str = "explore"
    phase: str = "interests"
    turn: int = 1


class ApplyCorrectionInput(BaseModel):
    session_id_hash: str = ""
    remove_skills: list[str] = Field(default_factory=list)
    add_interests: list[str] = Field(default_factory=list)
    job_goal: Optional[str] = None
    education_stage: Optional[str] = None


class MarketContextInput(BaseModel):
    session_id_hash: str = ""
    career_id: str = ""
    region: str = "all"


class RetrieveCandidatesInput(BaseModel):
    session_id_hash: str = ""
    # compact profile fields only — caller must not pass gender/region into embedding path
    dimensions: dict[str, float] = Field(default_factory=dict)
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    journey_mode: str = "explore"
    k: int = 20


class DiversifyInput(BaseModel):
    session_id_hash: str = ""
    ranked_ids: list[str] = Field(default_factory=list)
    ranked_scores: list[float] = Field(default_factory=list)
    dimensions: dict[str, float] = Field(default_factory=dict)


class LaunchReadinessInput(BaseModel):
    session_id_hash: str = ""
    career_id: str = ""
    journey_mode: str = "launch"
    skills: list[dict[str, str]] = Field(default_factory=list)
    experience_skills: list[str] = Field(default_factory=list)
    experience_quote: str = ""


class ComposeExplanationInput(BaseModel):
    session_id_hash: str = ""
    career_id: str = ""
    quote: str = ""
    demand_count_90d: int = 0
    salary_p50_trieu: Optional[float] = None


class PrepareResultInput(BaseModel):
    session_id_hash: str = ""
    top5_ids: list[str] = Field(default_factory=list)
    stretch_id: str = ""


class SearchCareerSourcesInput(BaseModel):
    session_id_hash: str = ""
    career_ids: list[str] = Field(min_length=1, max_length=2)
    intent: ResearchIntent = "overview"
    region: Region = "all"


# ---------- implementations ----------


def _inspect_profile_gaps(
    session_id_hash: str,
    stage: str = "discover",
    journey_mode: str = "explore",
    phase: str = "interests",
    completeness: float = 0.0,
    interest_count: int = 0,
    skill_count: int = 0,
    experience_count: int = 0,
) -> dict:
    missing: list[str] = []
    if journey_mode == "launch":
        if skill_count < 2:
            missing.append("sourced_skills")
        if experience_count < 1:
            missing.append("experiences_or_none")
        if completeness < 0.5:
            missing.append("job_goal_or_constraints")
    else:
        if interest_count < 2:
            missing.append("interests")
        if skill_count < 2:
            missing.append("sourced_skills")
        if completeness < 0.4:
            missing.append("constraints")
    return {
        "session_id_hash": session_id_hash,
        "stage": stage,
        "phase": phase,
        "missing_slots": missing,
        "completeness": completeness,
    }


def _ask_clarifying_question(
    session_id_hash: str = "",
    journey_mode: str = "explore",
    phase: str = "interests",
    focus_slot: str = "interests",
    turn_index: int = 0,
) -> dict:
    q = get_fallback_question(journey_mode, phase or focus_slot, turn_index)
    q = strip_privacy_text(q)
    return {
        "session_id_hash": session_id_hash,
        "question": q,
        "focus_slot": focus_slot,
    }


def _extract_profile_evidence(
    session_id_hash: str = "",
    message: str = "",
    journey_mode: str = "explore",
    phase: str = "interests",
    turn: int = 1,
) -> dict:
    from app.services.profiler import deterministic_turn

    msg = strip_privacy_text(message)
    out = deterministic_turn(
        journey_mode=journey_mode,  # type: ignore[arg-type]
        phase=phase,  # type: ignore[arg-type]
        message=msg,
        turn=turn,
        fallback_index=0,
    )
    return {
        "session_id_hash": session_id_hash,
        "reply_hint": out.reply,
        "profile_delta": out.profile_delta.model_dump(),
        "phase_done": out.phase_done,
    }


def _apply_profile_correction(
    session_id_hash: str = "",
    remove_skills: list[str] | None = None,
    add_interests: list[str] | None = None,
    job_goal: Optional[str] = None,
    education_stage: Optional[str] = None,
) -> dict:
    patch = ProfilePatch(
        remove_skills=remove_skills or [],
        add_interests=[strip_privacy_text(x) for x in (add_interests or [])],
        job_goal=strip_privacy_text(job_goal) if job_goal else None,
        education_stage=education_stage,  # type: ignore[arg-type]
    )
    return {
        "session_id_hash": session_id_hash,
        "applied_patch": patch.model_dump(),
        "note": "caller must merge via profiler.apply_patch with correction precedence",
    }


def _get_market_context(
    session_id_hash: str = "",
    career_id: str = "",
    region: str = "all",
) -> dict:
    career = get_career(career_id) if career_id else None
    if not career and load_careers():
        career = load_careers()[0]
        career_id = career["career_id"]
    if not career:
        return {"error": "no_career", "session_id_hash": session_id_hash}
    m = career.get("seed_market") or {}
    return {
        "session_id_hash": session_id_hash,
        "career_id": career_id,
        "region": region,
        "demand_count_90d": m.get("demand_count_90d", 0),
        "salary_p50_trieu": m.get("salary_p50_trieu"),
        "trend_pct": m.get("trend_pct"),
        "top_skills": m.get("top_skills") or [],
        "provenance": {
            "source": "seed_market",
            "snapshot": "careers_seed",
            "confidence": "seed",
        },
    }


def _retrieve_career_candidates(
    session_id_hash: str = "",
    dimensions: dict[str, float] | None = None,
    skills: list[str] | None = None,
    interests: list[str] | None = None,
    journey_mode: str = "explore",
    k: int = 20,
) -> dict:
    p = Profile(
        session_id=session_id_hash or "tool",
        journey_mode=journey_mode,  # type: ignore[arg-type]
        dimensions=dimensions or {},
        skills=[ProfileSkill(name=s, source_quote=f"tool:{s}") for s in (skills or [])],
        interests=list(interests or []),
    )
    ranked = matching.top_k_careers(p, k=k)
    return {
        "session_id_hash": session_id_hash,
        "ranked": [{"career_id": cid, "score": sc} for cid, sc, _ in ranked],
    }


def _diversify_with_stretch(
    session_id_hash: str = "",
    ranked_ids: list[str] | None = None,
    ranked_scores: list[float] | None = None,
    dimensions: dict[str, float] | None = None,
) -> dict:
    ids = ranked_ids or []
    scores = ranked_scores or [0.0] * len(ids)
    ranked = [(i, float(s), {}) for i, s in zip(ids, scores)]
    if not ranked:
        return {"error": "empty_ranked", "session_id_hash": session_id_hash}
    p = Profile(session_id=session_id_hash or "tool", dimensions=dimensions or {})
    top5 = [cid for cid, _, _ in ranked[:5]]
    stretch_id, stretch_score = matching.pick_stretch(ranked, p, set(top5))
    return {
        "session_id_hash": session_id_hash,
        "top5_ids": top5,
        "stretch_id": stretch_id,
        "stretch_score": stretch_score,
    }


def _assess_launch_readiness(
    session_id_hash: str = "",
    career_id: str = "",
    journey_mode: str = "launch",
    skills: list[dict[str, str]] | None = None,
    experience_skills: list[str] | None = None,
    experience_quote: str = "",
) -> dict:
    career = get_career(career_id) or (load_careers()[0] if load_careers() else None)
    if not career:
        return {"error": "no_career"}
    from app.models.schemas import ExperienceEvidence

    p = Profile(
        session_id=session_id_hash or "tool",
        journey_mode=journey_mode,  # type: ignore[arg-type]
        skills=[
            ProfileSkill(name=s.get("name", ""), source_quote=s.get("source_quote", "e"))
            for s in (skills or [])
            if s.get("name")
        ],
        experiences=(
            [
                ExperienceEvidence(
                    title="exp",
                    kind="project",
                    skills=list(experience_skills or []),
                    source_quote=experience_quote or "exp",
                )
            ]
            if experience_skills
            else []
        ),
    )
    jr = pathways.build_job_readiness(p, career)
    return {
        "session_id_hash": session_id_hash,
        "job_readiness": jr.model_dump() if jr else None,
    }


def _compose_grounded_explanation(
    session_id_hash: str = "",
    career_id: str = "",
    quote: str = "",
    demand_count_90d: int = 0,
    salary_p50_trieu: Optional[float] = None,
) -> dict:
    from app.models.schemas import MarketStats
    from app.services.evidence import template_why

    career = get_career(career_id) or {"title": career_id or "nghề", "career_id": career_id}
    p = Profile(
        session_id=session_id_hash or "tool",
        skills=[ProfileSkill(name="x", source_quote=quote)] if quote else [],
    )
    market = MarketStats(
        demand_count_90d=demand_count_90d,
        salary_p50_trieu=salary_p50_trieu,
        salary_sample_count=30 if salary_p50_trieu is not None else 0,
    )
    why = template_why(
        profile=p,
        career=career if isinstance(career, dict) else {"title": "nghề"},
        market=market,
        counterfactual="Nếu hồ sơ đổi, gợi ý có thể thay đổi — chỉ mang tính tham khảo.",
    )
    return {"session_id_hash": session_id_hash, "why": why.model_dump()}


def _prepare_result(
    session_id_hash: str = "",
    top5_ids: list[str] | None = None,
    stretch_id: str = "",
) -> dict:
    top5_ids = top5_ids or []
    # structural check only
    ok_routes = True
    for cid in top5_ids + ([stretch_id] if stretch_id else []):
        c = get_career(cid)
        if not c:
            continue
        routes = pathways.ensure_routes(c)
        types = {r.type for r in routes}
        if len(routes) < 2 or not (types & {"vocational", "college", "certificate"}):
            ok_routes = False
    return {
        "session_id_hash": session_id_hash,
        "top5_ids": top5_ids,
        "stretch_id": stretch_id,
        "invariants_ok": ok_routes and bool(stretch_id) and len(top5_ids) == 5,
    }


def _search_career_sources(
    session_id_hash: str = "",
    career_ids: list[str] | None = None,
    intent: str = "overview",
    region: str = "all",
) -> dict:
    """Bounded research tool. The router remains responsible for session authorization."""
    from app.services.career_research import research_careers

    response = research_careers(
        career_ids=career_ids or [],
        intent=intent,
        region=region,
    )
    payload = response.model_dump()
    payload["session_id_hash"] = session_id_hash
    return payload


def _structured(name: str, description: str, schema: type[BaseModel], fn: Callable) -> StructuredTool:
    return StructuredTool.from_function(
        name=name,
        description=description,
        func=fn,
        args_schema=schema,
    )


def build_tool_registry() -> dict[str, StructuredTool]:
    """Registry of bounded CareerCompass tools."""
    tools = [
        _structured(
            "inspect_profile_gaps",
            "Return missing evidence slots for the current profiling stage.",
            SessionStageInput,
            _inspect_profile_gaps,
        ),
        _structured(
            "ask_clarifying_question",
            "Return exactly one clarifying Vietnamese question for a focus slot.",
            AskQuestionInput,
            _ask_clarifying_question,
        ),
        _structured(
            "extract_profile_evidence",
            "Extract typed profile evidence candidates from a user message.",
            ExtractEvidenceInput,
            _extract_profile_evidence,
        ),
        _structured(
            "apply_profile_correction",
            "Build an allowlisted profile correction patch (user corrections win).",
            ApplyCorrectionInput,
            _apply_profile_correction,
        ),
        _structured(
            "get_market_context",
            "Read-only market stats for a career with provenance.",
            MarketContextInput,
            _get_market_context,
        ),
        _structured(
            "retrieve_career_candidates",
            "Deterministic top-K career retrieval from profile signals.",
            RetrieveCandidatesInput,
            _retrieve_career_candidates,
        ),
        _structured(
            "diversify_with_stretch",
            "Pick top5 + stretch from ranked candidates.",
            DiversifyInput,
            _diversify_with_stretch,
        ),
        _structured(
            "assess_launch_readiness",
            "Deterministic Launch readiness for a career.",
            LaunchReadinessInput,
            _assess_launch_readiness,
        ),
        _structured(
            "compose_grounded_explanation",
            "Build grounded why block from quote + stats.",
            ComposeExplanationInput,
            _compose_grounded_explanation,
        ),
        _structured(
            "prepare_result",
            "Validate top5+stretch structural invariants for response assembly.",
            PrepareResultInput,
            _prepare_result,
        ),
        _structured(
            "search_career_sources",
            "Search bounded current career sources; never changes recommendation ranking.",
            SearchCareerSourcesInput,
            _search_career_sources,
        ),
    ]
    reg = {t.name: t for t in tools}
    assert len(reg) == 11
    return reg


class AgentToolRegistry:
    def __init__(self) -> None:
        self._tools = build_tool_registry()

    def get(self, name: str) -> StructuredTool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools.keys())

    def json_schema(self, name: str) -> dict[str, Any]:
        tool = self._tools[name]
        # langchain StructuredTool exposes args_schema
        schema = tool.args_schema
        if schema is None:
            return {}
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            return schema.model_json_schema()
        return {}

    def invoke(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(name)
        raw = tool.invoke(args)
        if isinstance(raw, dict):
            return raw
        return {"result": raw}


_REGISTRY: AgentToolRegistry | None = None


def get_registry() -> AgentToolRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = AgentToolRegistry()
    return _REGISTRY
