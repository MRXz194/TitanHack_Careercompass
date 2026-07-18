"""PR-13 — wire bounded agent into /api/chat for discover/confirm_profile only.

- AGENT_MODE=deterministic | DEMO_MODE=replay → classic profiler path (no graph).
- AGENT_MODE=langgraph → invoke StateGraph/plain tools then merge evidence.
- API ChatResponse shape unchanged; no CoT/trace in response.
- Session persists only via SQLAlchemy session_store (no graph checkpointer).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from app.core.config import get_settings
from app.models.agent_schemas import AgentPlan, AgentStage
from app.models.profiler_io import ProfileDelta
from app.models.schemas import JourneyMode, Phase, Profile
from app.services import agent_graph, agent_policy
from app.services.agent_tools import get_registry
from app.services.llm import chat_json
from app.services.session_store import SessionState

log = logging.getLogger("agent_chat")

CHAT_PLANNER_PROMPT_VERSION = "chat-tool-router-v1"
CHAT_PLANNER_SYSTEM = """
Bạn là bộ định tuyến tool an toàn cho CareerCompass, không phải người xếp hạng nghề.
Chọn đúng một tool trong allowlist được cung cấp và trả JSON AgentPlan.
- Có nội dung mới cụ thể về hoạt động/kỹ năng/điều kiện/project: extract_profile_evidence.
- User rút lại/sửa điều đã lưu: apply_profile_correction.
- Câu trả lời quá mơ hồ và cần biết slot còn thiếu: inspect_profile_gaps.
- Cần hỏi đúng một câu theo slot đã biết: ask_clarifying_question.
- get_market_context chỉ ở confirm_profile và chỉ khi user hỏi rõ về một nghề đã có context.
Không chọn tool recommendation/retrieval, không thêm gender/GPA/tên trường/tên thật, không
đưa raw reasoning. public_rationale là một câu ngắn; thought_summary tối đa 3 từ; luôn đặt
stop_after_tool=true để giữ một tool call cho mỗi chat turn trong release MVP.
""".strip()


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
        settings = get_settings()

        def deterministic_plan() -> AgentPlan:
            # Safe fallback: content is always extracted; classic profiler still asks
            # the adaptive question and merges correction precedence independently.
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

        if not settings.chat_api_key or settings.demo_mode == "replay":
            return deterministic_plan()

        allowed = sorted(agent_policy.AGENT_SELECTABLE.get(stage, frozenset()))
        payload = {
            "prompt_version": CHAT_PLANNER_PROMPT_VERSION,
            "stage": stage.value,
            "journey_mode": journey_mode,
            "phase": phase,
            "turn": turn,
            "allowed_tools": allowed,
            "user_message": msg,
            "profile_summary": {
                "completeness": profile.completeness,
                "skills": [agent_policy.strip_privacy_text(item.name) for item in profile.skills[:8]],
                "interests": [agent_policy.strip_privacy_text(item) for item in profile.interests[:8]],
                "experience_titles": [
                    agent_policy.strip_privacy_text(item.title) for item in profile.experiences[:5]
                ],
                "job_goal": agent_policy.strip_privacy_text(profile.job_goal or ""),
            },
        }
        try:
            plan = chat_json(
                CHAT_PLANNER_SYSTEM,
                [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
                AgentPlan,
                max_retries=0,
            )
            # Code owns identity/current-turn fields; the model may choose only the
            # tool-specific semantic arguments inside the policy boundary.
            plan.stop_after_tool = True
            plan.thought_summary = (plan.thought_summary or "route")[:40]
            plan.arguments = dict(plan.arguments or {})
            plan.arguments["session_id_hash"] = sid_hash
            if plan.next_tool == "extract_profile_evidence":
                plan.arguments.update(
                    message=msg,
                    journey_mode=journey_mode,
                    phase=phase,
                    turn=turn,
                )
            elif plan.next_tool == "inspect_profile_gaps":
                plan.arguments.update(
                    stage=stage.value,
                    journey_mode=journey_mode,
                    phase=phase,
                    completeness=profile.completeness,
                    interest_count=len(profile.interests),
                    skill_count=len(profile.skills),
                    experience_count=len(profile.experiences),
                )
            elif plan.next_tool == "ask_clarifying_question":
                plan.arguments.update(
                    journey_mode=journey_mode,
                    phase=phase,
                    focus_slot=plan.arguments.get("focus_slot") or phase,
                    turn_index=turn,
                )
            elif plan.next_tool == "apply_profile_correction":
                # The model may choose the correction tool, but it does not own the
                # mutation arguments. Rebuild removals from the current user turn and
                # canonical profile so a hallucinated field cannot erase profile data.
                from app.services.profiler import deterministic_turn

                correction = deterministic_turn(
                    journey_mode=journey_mode,
                    phase=phase,
                    message=msg,
                    turn=turn,
                    fallback_index=0,
                    profile=profile,
                ).profile_delta.corrections
                safe_args: dict[str, Any] = {"session_id_hash": sid_hash}
                if correction is not None:
                    safe_args.update(
                        remove_skills=correction.remove_skills,
                        remove_interests=correction.remove_interests,
                    )
                plan.arguments = safe_args
            return plan
        except Exception as exc:  # noqa: BLE001 — planner is optional, fallback is mandatory
            log.warning("chat planner fallback err=%s", type(exc).__name__)
            return deterministic_plan()

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
    # Extraction tools own profile evidence, not conversational wording. Using the
    # deterministic tool's reply_hint here used to overwrite the validated adaptive
    # LLM reply produced by profiler._produce_turn_output on every LangGraph turn.
    reply: str | None = None
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
