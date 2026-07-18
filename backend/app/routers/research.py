"""Bounded post-recommendation career research endpoint (N4-05)."""
from fastapi import APIRouter, HTTPException

from app.models.agent_schemas import AgentPlan, AgentStage, PolicyCode
from app.models.schemas import CareerResearchRequest, CareerResearchResponse
from app.services import agent_policy, matching, session_store
from app.services.agent_tools import get_registry

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("/careers", response_model=CareerResearchResponse)
def research_careers(body: CareerResearchRequest) -> CareerResearchResponse:
    state = session_store.get_session(body.session_id)
    if state is None:
        raise HTTPException(404, detail="session not found; complete profiling first")
    if not matching.has_personal_signal(state.profile):
        raise HTTPException(
            409,
            detail="profile has insufficient personal evidence; continue profiling first",
        )

    top5, stretch = matching.recommend(state.profile)
    allowed_ids = {item.career_id for item in top5} | {stretch.career_id}
    requested_ids = list(dict.fromkeys(body.career_ids))
    if any(career_id not in allowed_ids for career_id in requested_ids):
        raise HTTPException(422, detail="career_ids must come from this session's recommendations")

    # Explicit user intent is the plan. It still goes through the same pre/post
    # CareerCompass policy gates and typed registry as the chat agent tools.
    budget = agent_policy.budget_start(deadline_ms=8_000)
    plan = AgentPlan(
        intent="research",
        next_tool="search_career_sources",
        arguments={
            "session_id_hash": agent_policy.session_id_hash(body.session_id),
            "career_ids": requested_ids,
            "intent": body.intent,
            "region": body.region,
        },
    )
    decision = agent_policy.authorize_plan(plan, AgentStage.research, budget)
    if decision.code != PolicyCode.ALLOW:
        raise HTTPException(422, detail="research request was blocked by policy")
    agent_policy.record_tool_use(budget)
    result = get_registry().invoke("search_career_sources", decision.sanitized_args)
    observation = agent_policy.authorize_observation("search_career_sources", result, budget)
    if observation.code != PolicyCode.ALLOW:
        raise HTTPException(422, detail="research result failed provenance policy")
    return CareerResearchResponse.model_validate(observation.sanitized_args)
