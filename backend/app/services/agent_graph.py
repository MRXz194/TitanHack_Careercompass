"""Bounded ReAct orchestration — PR-12.

LangGraph StateGraph is only built when AGENT_MODE=langgraph (spike gate).
AGENT_MODE=deterministic uses plain_python_orchestrator and must never compile graph.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Optional, TypedDict

from app.core.config import get_settings
from app.models.agent_schemas import (
    AgentObservation,
    AgentPlan,
    AgentStage,
    AgentTraceMeta,
    PolicyCode,
    TurnBudget,
)
from app.services import agent_policy
from app.services.agent_tools import TOOL_REGISTRY_VERSION, get_registry

# Module-level graph cache — only populated in langgraph mode
_GRAPH = None
_GRAPH_COMPILED = False


class AgentState(TypedDict, total=False):
    session_id: str
    session_id_hash: str
    stage: str
    plan: dict
    policy: dict
    observations: list[dict]
    budget: dict
    reply: str
    fallback: bool
    public_rationale: str
    planner: Any  # injectable for tests: Callable[[AgentState], AgentPlan]


def agent_mode() -> str:
    return (get_settings().agent_mode or "deterministic").lower()


def should_use_graph() -> bool:
    return agent_mode() == "langgraph"


def _default_fake_planner(state: AgentState) -> AgentPlan:
    """Offline default planner used in spike tests (no network)."""
    stage = AgentStage(state.get("stage") or "discover")
    if stage == AgentStage.confirm_profile:
        tool = "inspect_profile_gaps"
    else:
        tool = "ask_clarifying_question"
    return AgentPlan(
        intent="collect_evidence",
        next_tool=tool,
        arguments={
            "session_id_hash": state.get("session_id_hash") or "",
            "journey_mode": "explore",
            "phase": "interests",
            "turn_index": 0,
        },
        public_rationale="Mình đang cập nhật hồ sơ theo thông tin bạn chia sẻ.",
        stop_after_tool=True,
        thought_summary="pick_safe_tool",
    )


def plain_python_orchestrator(
    *,
    session_id: str,
    stage: AgentStage = AgentStage.discover,
    planner: Optional[Callable[[AgentState], AgentPlan]] = None,
    budget: Optional[TurnBudget] = None,
) -> dict[str, Any]:
    """Bounded orchestrator without LangGraph (deterministic / fallback path)."""
    t0 = time.perf_counter()
    budget = budget or agent_policy.budget_start()
    sid_hash = agent_policy.session_id_hash(session_id)
    state: AgentState = {
        "session_id": session_id,
        "session_id_hash": sid_hash,
        "stage": stage.value,
        "observations": [],
        "fallback": False,
        "budget": budget.model_dump(),
    }
    plan_fn = planner or _default_fake_planner
    registry = get_registry()
    denies = 0

    for _ in range(2):  # max 2 agent-selected tools
        if agent_policy.budget_expired(budget):
            state["fallback"] = True
            break
        plan = plan_fn(state)
        if not isinstance(plan, AgentPlan):
            plan = AgentPlan.model_validate(plan)
        decision = agent_policy.authorize_plan(plan, stage, budget, agent_selected=True)
        state["plan"] = plan.model_dump()
        state["policy"] = decision.model_dump()
        if decision.code != PolicyCode.ALLOW:
            denies += 1
            budget = agent_policy.record_deny(budget)
            state["budget"] = budget.model_dump()
            if (
                decision.code == PolicyCode.STOP_FALLBACK
                or denies >= budget.max_policy_denies
            ):
                state["fallback"] = True
                break
            continue
        try:
            result = registry.invoke(decision.tool or plan.next_tool, decision.sanitized_args)
        except Exception as exc:  # noqa: BLE001
            result = {"error": type(exc).__name__}
            state["fallback"] = True
            obs = AgentObservation(
                tool=plan.next_tool,
                ok=False,
                policy_code=PolicyCode.DENY_TOOL.value,
                result=result,
            )
            state["observations"] = list(state.get("observations") or []) + [obs.model_dump()]
            break
        post = agent_policy.authorize_observation(plan.next_tool, result, budget)
        if post.code != PolicyCode.ALLOW:
            budget = agent_policy.record_deny(budget)
            state["fallback"] = True
            obs = AgentObservation(
                tool=plan.next_tool,
                ok=False,
                policy_code=post.code.value,
                result=result,
            )
            state["observations"] = list(state.get("observations") or []) + [obs.model_dump()]
            break
        budget = agent_policy.record_tool_use(budget)
        state["budget"] = budget.model_dump()
        obs = AgentObservation(
            tool=plan.next_tool,
            ok=True,
            policy_code=PolicyCode.ALLOW.value,
            result=post.sanitized_args or result,
            provenance={"tool_registry": TOOL_REGISTRY_VERSION},
        )
        state["observations"] = list(state.get("observations") or []) + [obs.model_dump()]
        if plan.stop_after_tool:
            break

    # compose
    if state.get("fallback") or not state.get("observations"):
        from app.prompts.profiler import get_fallback_question

        state["reply"] = get_fallback_question("explore", "interests", 0)
        state["fallback"] = True
        state["public_rationale"] = "Mình hỏi thêm để hiểu bạn hơn."
    else:
        last = (state.get("observations") or [])[-1]
        res = last.get("result") or {}
        state["reply"] = res.get("question") or res.get("reply_hint") or (
            "Mình đã cập nhật hồ sơ theo thông tin bạn chia sẻ."
        )
        state["public_rationale"] = (state.get("plan") or {}).get("public_rationale") or ""

    latency = (time.perf_counter() - t0) * 1000
    trace = AgentTraceMeta(
        session_id_hash=sid_hash,
        stage=stage,
        tools=[o.get("tool", "") for o in (state.get("observations") or [])],
        policy_codes=[o.get("policy_code", "") for o in (state.get("observations") or [])],
        fallback=bool(state.get("fallback")),
        latency_ms=latency,
        tool_policy_version=agent_policy.TOOL_POLICY_VERSION,
    )
    return {
        "reply": state.get("reply") or "",
        "public_rationale": state.get("public_rationale") or "",
        "fallback": bool(state.get("fallback")),
        "observations": state.get("observations") or [],
        "trace": trace.model_dump(),
        "engine": "plain_python",
    }


def build_graph():
    """Compile LangGraph StateGraph. Only call when AGENT_MODE=langgraph."""
    from langgraph.graph import END, START, StateGraph

    registry = get_registry()

    def plan_node(state: AgentState) -> AgentState:
        planner = state.get("planner") or _default_fake_planner
        plan = planner(state)
        if not isinstance(plan, AgentPlan):
            plan = AgentPlan.model_validate(plan)
        return {**state, "plan": plan.model_dump()}

    def policy_node(state: AgentState) -> AgentState:
        budget = TurnBudget.model_validate(state.get("budget") or agent_policy.budget_start().model_dump())
        plan = AgentPlan.model_validate(state.get("plan") or {})
        stage = AgentStage(state.get("stage") or "discover")
        decision = agent_policy.authorize_plan(plan, stage, budget, agent_selected=True)
        if decision.code != PolicyCode.ALLOW:
            budget = agent_policy.record_deny(budget)
        return {
            **state,
            "policy": decision.model_dump(),
            "budget": budget.model_dump(),
        }

    def route_policy(state: AgentState) -> str:
        code = (state.get("policy") or {}).get("code")
        if code == PolicyCode.ALLOW.value:
            return "allow"
        return "fallback"

    def tool_node(state: AgentState) -> AgentState:
        budget = TurnBudget.model_validate(state.get("budget") or {})
        plan = AgentPlan.model_validate(state.get("plan") or {})
        decision = state.get("policy") or {}
        args = decision.get("sanitized_args") or plan.arguments
        tool_name = decision.get("tool") or plan.next_tool
        try:
            result = registry.invoke(tool_name, args)
        except Exception as exc:  # noqa: BLE001
            result = {"error": type(exc).__name__}
            obs = AgentObservation(
                tool=tool_name,
                ok=False,
                policy_code=PolicyCode.DENY_TOOL.value,
                result=result,
            )
            return {
                **state,
                "fallback": True,
                "observations": list(state.get("observations") or []) + [obs.model_dump()],
            }
        post = agent_policy.authorize_observation(tool_name, result, budget)
        if post.code != PolicyCode.ALLOW:
            budget = agent_policy.record_deny(budget)
            obs = AgentObservation(
                tool=tool_name,
                ok=False,
                policy_code=post.code.value,
                result=result,
            )
            return {
                **state,
                "fallback": True,
                "budget": budget.model_dump(),
                "observations": list(state.get("observations") or []) + [obs.model_dump()],
            }
        budget = agent_policy.record_tool_use(budget)
        obs = AgentObservation(
            tool=tool_name,
            ok=True,
            policy_code=PolicyCode.ALLOW.value,
            result=post.sanitized_args or result,
            provenance={"tool_registry": TOOL_REGISTRY_VERSION},
        )
        return {
            **state,
            "budget": budget.model_dump(),
            "observations": list(state.get("observations") or []) + [obs.model_dump()],
        }

    def compose_node(state: AgentState) -> AgentState:
        obs_list = state.get("observations") or []
        if state.get("fallback") or not obs_list:
            from app.prompts.profiler import get_fallback_question

            return {
                **state,
                "fallback": True,
                "reply": get_fallback_question("explore", "interests", 0),
                "public_rationale": "Mình hỏi thêm để hiểu bạn hơn.",
            }
        last = obs_list[-1].get("result") or {}
        reply = last.get("question") or last.get("reply_hint") or (
            "Mình đã cập nhật hồ sơ theo thông tin bạn chia sẻ."
        )
        return {
            **state,
            "reply": reply,
            "public_rationale": (state.get("plan") or {}).get("public_rationale") or "",
        }

    def fallback_node(state: AgentState) -> AgentState:
        from app.prompts.profiler import get_fallback_question

        return {
            **state,
            "fallback": True,
            "reply": get_fallback_question("explore", "interests", 0),
            "public_rationale": "Mình hỏi thêm để hiểu bạn hơn.",
        }

    g = StateGraph(AgentState)
    g.add_node("plan", plan_node)
    g.add_node("policy", policy_node)
    g.add_node("tool", tool_node)
    g.add_node("compose", compose_node)
    g.add_node("fallback", fallback_node)
    g.add_edge(START, "plan")
    g.add_edge("plan", "policy")
    g.add_conditional_edges(
        "policy",
        route_policy,
        {"allow": "tool", "fallback": "fallback"},
    )
    g.add_edge("tool", "compose")
    g.add_edge("fallback", END)
    g.add_edge("compose", END)
    return g.compile()


def get_compiled_graph():
    """Compile once when langgraph mode; raises if deterministic mode calls this."""
    global _GRAPH, _GRAPH_COMPILED
    if not should_use_graph():
        raise RuntimeError("GRAPH_DISABLED: AGENT_MODE is not langgraph")
    if _GRAPH is None:
        _GRAPH = build_graph()
        _GRAPH_COMPILED = True
    return _GRAPH


def reset_graph_cache() -> None:
    global _GRAPH, _GRAPH_COMPILED
    _GRAPH = None
    _GRAPH_COMPILED = False


def graph_was_compiled() -> bool:
    return _GRAPH_COMPILED


def invoke_agent_turn(
    *,
    session_id: str,
    stage: AgentStage = AgentStage.discover,
    planner: Optional[Callable[[AgentState], AgentPlan]] = None,
) -> dict[str, Any]:
    """Entry used by tests/spike. Routes by AGENT_MODE."""
    if not should_use_graph():
        return plain_python_orchestrator(
            session_id=session_id, stage=stage, planner=planner
        )
    t0 = time.perf_counter()
    graph = get_compiled_graph()
    budget = agent_policy.budget_start()
    init: AgentState = {
        "session_id": session_id,
        "session_id_hash": agent_policy.session_id_hash(session_id),
        "stage": stage.value,
        "observations": [],
        "fallback": False,
        "budget": budget.model_dump(),
        "planner": planner,
    }
    out = graph.invoke(init)
    latency = (time.perf_counter() - t0) * 1000
    trace = AgentTraceMeta(
        session_id_hash=init["session_id_hash"],
        stage=stage,
        tools=[o.get("tool", "") for o in (out.get("observations") or [])],
        policy_codes=[o.get("policy_code", "") for o in (out.get("observations") or [])],
        fallback=bool(out.get("fallback")),
        latency_ms=latency,
        tool_policy_version=agent_policy.TOOL_POLICY_VERSION,
    )
    return {
        "reply": out.get("reply") or "",
        "public_rationale": out.get("public_rationale") or "",
        "fallback": bool(out.get("fallback")),
        "observations": out.get("observations") or [],
        "trace": trace.model_dump(),
        "engine": "langgraph",
    }
