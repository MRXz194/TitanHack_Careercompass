"""PR-13 — wire bounded agent into /api/chat for discover/confirm_profile only.

- AGENT_MODE=deterministic | DEMO_MODE=replay → classic profiler path (no graph).
- AGENT_MODE=langgraph → invoke StateGraph/plain tools then merge evidence.
- API ChatResponse shape unchanged; no CoT/trace in response.
- Session persists only via SQLAlchemy session_store (no graph checkpointer).
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from app.core.config import get_settings
from app.models.agent_schemas import AgentPlan, AgentStage
from app.models.profiler_io import ProfileDelta
from app.models.schemas import JourneyMode, Phase, Profile
from app.services import agent_graph, agent_policy
from app.services.agent_tools import get_registry
from app.services.session_store import SessionState

log = logging.getLogger("agent_chat")


def map_phase_to_agent_stage(phase: Phase, *, done: bool = False) -> AgentStage:
    """Internal stage safety rail → discover | confirm_profile for chat agent."""
    if done or phase == "wrapup":
        return AgentStage.confirm_profile
    return AgentStage.discover


def agent_enabled_for_chat() -> bool:
    """LangGraph (or agent tools) only when explicitly enabled and not replay."""
    s = get_settings()
    if (s.demo_mode or "").lower() == "replay":
        return False
    return (s.agent_mode or "deterministic").lower() == "langgraph"


def build_chat_planner(
    *,
    user_message: str,
    profile: Profile,
    phase: Phase,
    journey_mode: JourneyMode,
    stage: AgentStage,
    turn: int,
):
    """Return a planner callable that picks at most one primary tool for this turn."""

    def _planner(state: dict[str, Any]) -> AgentPlan:
        sid_hash = state.get("session_id_hash") or agent_policy.session_id_hash(
            state.get("session_id") or ""
        )
        msg = agent_policy.strip_privacy_text(user_message or "")
        # Prefer extract when user sent content; else inspect/ask
        if msg:
            return AgentPlan(
                intent="collect_evidence",
                next_tool="extract_profile_evidence",
                arguments={
                    "session_id_hash": sid_hash,
                    "message": msg,
                    "journey_mode": journey_mode,
                    "phase": phase,
                    "turn": turn,
                },
                public_rationale="Mình đang cập nhật hồ sơ theo điều bạn vừa chia sẻ.",
                stop_after_tool=True,
                thought_summary="extract",
            )
        if stage == AgentStage.confirm_profile:
            return AgentPlan(
                intent="confirm",
                next_tool="inspect_profile_gaps",
                arguments={
                    "session_id_hash": sid_hash,
                    "stage": stage.value,
                    "journey_mode": journey_mode,
                    "phase": phase,
                    "completeness": profile.completeness,
                    "interest_count": len(profile.interests),
                    "skill_count": len(profile.skills),
                    "experience_count": len(profile.experiences),
                },
                public_rationale="Mình đang kiểm tra hồ sơ còn thiếu gì.",
                stop_after_tool=True,
                thought_summary="inspect",
            )
        return AgentPlan(
            intent="collect_evidence",
            next_tool="ask_clarifying_question",
            arguments={
                "session_id_hash": sid_hash,
                "journey_mode": journey_mode,
                "phase": phase,
                "focus_slot": phase,
                "turn_index": turn,
            },
            public_rationale="Mình hỏi thêm để hiểu bạn hơn.",
            stop_after_tool=True,
            thought_summary="ask",
        )

    return _planner


def run_agent_enrichment(
    state: SessionState,
    user_message: str,
) -> dict[str, Any]:
    """
    Run bounded agent for discover/confirm only.
    Returns {delta, reply, fallback, trace} — never raises 5xx to caller.
    """
    stage = map_phase_to_agent_stage(state.phase, done=state.done)
    if stage not in (AgentStage.discover, AgentStage.confirm_profile):
        return {"delta": None, "reply": None, "fallback": True, "trace": {}}

    planner = build_chat_planner(
        user_message=user_message,
        profile=state.profile,
        phase=state.phase,
        journey_mode=state.journey_mode,
        stage=stage,
        turn=state.turn,
    )
    try:
        out = agent_graph.invoke_agent_turn(
            session_id=state.session_id,
            stage=stage,
            planner=planner,
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("agent_chat invoke failed: %s", type(exc).__name__)
        return {"delta": None, "reply": None, "fallback": True, "trace": {"error": type(exc).__name__}}

    # Sanitize: strip any accidental private keys from trace before logging metadata only
    trace = out.get("trace") or {}
    for bad in ("messages", "cot", "transcript", "raw"):
        trace.pop(bad, None)

    delta: ProfileDelta | None = None
    applied_patch: dict[str, Any] | None = None
    reply: str | None = out.get("reply")
    for obs in out.get("observations") or []:
        if not obs.get("ok"):
            continue
        res = obs.get("result") or {}
        if "profile_delta" in res:
            try:
                delta = ProfileDelta.model_validate(res["profile_delta"])
            except Exception:  # noqa: BLE001
                delta = None
        if "applied_patch" in res:
            # apply_profile_correction builds a patch but never merges it itself —
            # the caller (profiler.handle_turn) must merge it with correction precedence.
            applied_patch = res["applied_patch"]
        if res.get("question"):
            reply = res["question"]
        if res.get("reply_hint"):
            reply = res["reply_hint"]

    return {
        "delta": delta,
        "reply": reply,
        "fallback": bool(out.get("fallback")),
        "trace": trace,
        "public_rationale": out.get("public_rationale") or "",
        "engine": out.get("engine"),
        "applied_patch": applied_patch,
    }


def maybe_run_extract_tools_only(
    state: SessionState,
    user_message: str,
) -> ProfileDelta | None:
    """
    Even in deterministic mode, optionally run local extract tool (no graph)
    for better evidence merge — still no network/planner LLM.
    Controlled: only when message non-empty and not replay.
    """
    s = get_settings()
    if (s.demo_mode or "").lower() == "replay":
        return None
    if not (user_message or "").strip():
        return None
    # deterministic path: call tool registry directly (not agent loop) for extract
    if (s.agent_mode or "deterministic").lower() != "deterministic":
        return None
    try:
        reg = get_registry()
        res = reg.invoke(
            "extract_profile_evidence",
            {
                "session_id_hash": agent_policy.session_id_hash(state.session_id),
                "message": agent_policy.strip_privacy_text(user_message),
                "journey_mode": state.journey_mode,
                "phase": state.phase,
                "turn": state.turn,
            },
        )
        if "profile_delta" in res:
            return ProfileDelta.model_validate(res["profile_delta"])
    except Exception as exc:  # noqa: BLE001
        log.warning("deterministic extract tool failed: %s", type(exc).__name__)
    return None
