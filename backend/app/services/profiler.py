"""Conversational profiler — PR-03. Design: docs/AI_DESIGN.md §1.

Shared engine for journey_mode explore|launch; mode locked on opening turn.
Phase transitions decided by CODE from profile completeness (not the LLM).
LLM structured output optional; always falls back to deterministic path.
User corrections outrank model inference on later merges.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from app.core.config import get_settings
from app.models.profiler_io import ProfileDelta, ProfilerTurnOutput
from app.models.schemas import (
    ChatResponse,
    Constraints,
    EvidenceQuote,
    ExperienceEvidence,
    JourneyMode,
    Phase,
    Profile,
    ProfilePatch,
    ProfileSkill,
)
from app.prompts.profiler import (
    PHASES,
    build_profiler_system,
    get_fallback_question,
)
from app.services import session_store
from app.services.llm import LLMError, chat_json
from app.services.session_store import Corrections, SessionState

log = logging.getLogger("profiler")

PHASE_ORDER: list[Phase] = list(PHASES)  # type: ignore[arg-type]
DIM_KEYS = ("ky_thuat", "phan_tich", "sang_tao", "xa_hoi", "quan_ly")

# Soft keyword → dimension bumps for deterministic offline path (no live LLM).
_DIM_KEYWORDS: dict[str, tuple[str, ...]] = {
    "ky_thuat": ("sửa", "điện", "máy", "code", "lập trình", "react", "python", "cơ khí", "hàn"),
    "phan_tich": ("dữ liệu", "excel", "phân tích", "dashboard", "số liệu", "logic", "toán"),
    "sang_tao": ("vẽ", "thiết kế", "nhạc", "sáng tạo", "viết", "photoshop", "figma"),
    "xa_hoi": ("dạy", "giúp", "tình nguyện", "chăm", "tư vấn", "giao tiếp"),
    "quan_ly": ("tổ chức", "lịch", "nhóm", "quản lý", "điều phối", "kinh doanh"),
}


# ---------- merge / completeness / phase (pure) ----------


def merge_delta(
    profile: Profile,
    delta: ProfileDelta,
    corrections: Corrections,
    turn: int,
) -> Profile:
    """Merge validated delta into profile; corrections win."""
    # Dimensions
    for key, value in (delta.dimensions or {}).items():
        if key not in DIM_KEYS:
            continue
        if key in corrections.dimension_overrides:
            profile.dimensions[key] = corrections.dimension_overrides[key]
            continue
        try:
            v = float(value)
        except (TypeError, ValueError):
            continue
        v = max(0.0, min(1.0, v))
        profile.dimensions[key] = max(profile.dimensions.get(key, 0.0), v)
    for key, value in corrections.dimension_overrides.items():
        profile.dimensions[key] = value

    # Interests (union)
    seen_i = {i.lower() for i in profile.interests}
    for interest in delta.interests or []:
        text = (interest or "").strip()
        if text and text.lower() not in seen_i:
            profile.interests.append(text)
            seen_i.add(text.lower())

    # Skills — skip removed by user correction; require source_quote for new
    existing_skills = {s.name.lower(): s for s in profile.skills}
    for skill in delta.skills or []:
        name = (skill.name or "").strip()
        if not name or name.lower() in {r.lower() for r in corrections.removed_skills}:
            continue
        quote = (skill.source_quote or "").strip()
        if not quote:
            continue
        # Never store instruction-like "skills"
        if _looks_like_injection(name):
            continue
        if name.lower() in existing_skills:
            prev = existing_skills[name.lower()]
            if quote and not prev.source_quote:
                prev.source_quote = quote
            if skill.level and not prev.level:
                prev.level = skill.level
        else:
            item = ProfileSkill(name=name, level=skill.level or "", source_quote=quote)
            profile.skills.append(item)
            existing_skills[name.lower()] = item
    profile.skills = [
        s for s in profile.skills if s.name.lower() not in {r.lower() for r in corrections.removed_skills}
    ]

    # Experiences (max 3); respect removals
    titles = {e.title.lower() for e in profile.experiences}
    for exp in delta.experiences or []:
        title = (exp.title or "").strip()
        if not title:
            continue
        if title.lower() in {r.lower() for r in corrections.removed_experience_titles}:
            continue
        if title.lower() in titles:
            continue
        if len(profile.experiences) >= 3:
            break
        if not (exp.source_quote or "").strip():
            continue
        profile.experiences.append(
            ExperienceEvidence(
                title=title,
                kind=exp.kind,
                description=exp.description or "",
                skills=list(exp.skills or []),
                source_quote=exp.source_quote,
            )
        )
        titles.add(title.lower())
    profile.experiences = [
        e
        for e in profile.experiences
        if e.title.lower() not in {r.lower() for r in corrections.removed_experience_titles}
    ]

    # Constraints (partial)
    if delta.constraints is not None:
        c = profile.constraints
        if delta.constraints.region_pref is not None:
            c.region_pref = delta.constraints.region_pref
        if delta.constraints.study_budget is not None:
            c.study_budget = delta.constraints.study_budget
        if delta.constraints.study_duration_pref is not None:
            c.study_duration_pref = delta.constraints.study_duration_pref
        if delta.constraints.notes is not None and delta.constraints.notes != "":
            if c.notes:
                c.notes = f"{c.notes}; {delta.constraints.notes}"
            else:
                c.notes = delta.constraints.notes

    # Education / job goal — respect locks
    if not corrections.locked_education_stage and delta.education_stage is not None:
        profile.education_stage = delta.education_stage
    if not corrections.locked_job_goal and delta.job_goal is not None:
        profile.job_goal = delta.job_goal

    # Evidence quotes
    for eq in delta.evidence_quotes or []:
        quote = (eq.quote or "").strip()
        if not quote:
            continue
        profile.evidence_quotes.append(
            EvidenceQuote(turn=eq.turn or turn, quote=quote[:500], mapped_to=eq.mapped_to or "")
        )

    profile.completeness = compute_completeness(profile.journey_mode, profile)
    return profile


def apply_patch(profile: Profile, patch: ProfilePatch, corrections: Corrections) -> Profile:
    if patch.dimensions:
        for key, value in patch.dimensions.items():
            if key in DIM_KEYS:
                v = max(0.0, min(1.0, float(value)))
                profile.dimensions[key] = v
                corrections.dimension_overrides[key] = v

    if patch.remove_skills:
        remove = {n.lower() for n in patch.remove_skills}
        corrections.removed_skills.update(patch.remove_skills)
        profile.skills = [s for s in profile.skills if s.name.lower() not in remove]

    if patch.add_interests:
        seen = {i.lower() for i in profile.interests}
        for interest in patch.add_interests:
            t = interest.strip()
            if t and t.lower() not in seen:
                profile.interests.append(t)
                seen.add(t.lower())

    if "education_stage" in patch.model_fields_set:
        profile.education_stage = patch.education_stage
        corrections.locked_education_stage = True

    if "job_goal" in patch.model_fields_set:
        profile.job_goal = patch.job_goal
        corrections.locked_job_goal = True

    if patch.remove_experience_titles:
        corrections.removed_experience_titles.update(patch.remove_experience_titles)
        remove_t = {t.lower() for t in patch.remove_experience_titles}
        profile.experiences = [e for e in profile.experiences if e.title.lower() not in remove_t]

    if patch.add_experiences:
        titles = {e.title.lower() for e in profile.experiences}
        for exp in patch.add_experiences:
            if exp.title.lower() in titles:
                continue
            if len(profile.experiences) >= 3:
                break
            profile.experiences.append(exp)
            titles.add(exp.title.lower())
            corrections.removed_experience_titles.discard(exp.title)

    profile.completeness = compute_completeness(profile.journey_mode, profile)
    return profile


def _sourced_skills(profile: Profile) -> list[ProfileSkill]:
    return [s for s in profile.skills if (s.source_quote or "").strip()]


def _active_dimensions(profile: Profile) -> int:
    return sum(1 for v in profile.dimensions.values() if v and float(v) > 0.05)


def _has_constraint_signal(profile: Profile, declined: bool) -> bool:
    c = profile.constraints
    return bool(
        declined
        or c.region_pref
        or c.study_budget
        or c.study_duration_pref
        or (c.notes and c.notes.strip())
    )


def compute_completeness(mode: JourneyMode, profile: Profile, declined: bool = False) -> float:
    """0..1 progress for FE; mode-specific weights."""
    if mode == "launch":
        parts = [
            1.0 if profile.education_stage else 0.0,
            1.0 if profile.job_goal or "chưa" in (profile.constraints.notes or "").lower() else 0.0,
            min(1.0, len(profile.experiences) / 1.0) if profile.experiences else (
                0.5 if "chưa" in (profile.constraints.notes or "").lower() else 0.0
            ),
            min(1.0, len(_sourced_skills(profile)) / 2.0),
            1.0 if _has_constraint_signal(profile, declined) else 0.0,
        ]
    else:
        parts = [
            min(1.0, len(profile.interests) / 2.0),
            min(1.0, _active_dimensions(profile) / 2.0),
            min(1.0, len(_sourced_skills(profile)) / 2.0),
            1.0 if _has_constraint_signal(profile, declined) else 0.0,
        ]
    return round(sum(parts) / len(parts), 2)


def phase_goals_met(
    mode: JourneyMode,
    phase: Phase,
    profile: Profile,
    *,
    constraint_declined: bool = False,
    turns_in_phase: int = 0,
) -> bool:
    """Whether CODE should advance past this phase."""
    if phase == "warmup":
        return turns_in_phase >= 1
    if phase == "interests":
        if mode == "launch":
            return turns_in_phase >= 1 and (
                len(profile.interests) >= 1
                or bool(profile.job_goal)
                or turns_in_phase >= 2
            )
        return turns_in_phase >= 1 and (
            (len(profile.interests) >= 2 and _active_dimensions(profile) >= 1)
            or turns_in_phase >= 3
        )
    if phase == "abilities":
        return len(_sourced_skills(profile)) >= 2 or turns_in_phase >= 3
    if phase == "constraints":
        return _has_constraint_signal(profile, constraint_declined) or turns_in_phase >= 2
    if phase == "wrapup":
        return turns_in_phase >= 1
    return False


def advance_phase(
    mode: JourneyMode,
    phase: Phase,
    profile: Profile,
    *,
    constraint_declined: bool,
    turns_in_phase: int,
    force_done_signal: bool = False,
) -> tuple[Phase, bool, int]:
    """Return (new_phase, done, turns_in_phase)."""
    turns = turns_in_phase
    current = phase
    if current == "wrapup" and (force_done_signal or turns >= 1):
        if force_done_signal or turns >= 1:
            return "wrapup", True, turns

    while phase_goals_met(
        mode, current, profile, constraint_declined=constraint_declined, turns_in_phase=turns
    ):
        idx = PHASE_ORDER.index(current)
        if idx >= len(PHASE_ORDER) - 1:
            # stay on wrapup until confirmation
            return "wrapup", False, turns
        current = PHASE_ORDER[idx + 1]
        turns = 0
        if current == "wrapup":
            break
    return current, False, turns


def _looks_like_injection(text: str) -> bool:
    t = text.lower()
    bad = (
        "ignore previous",
        "api_key",
        "root_access",
        "system:",
        "you are dan",
        "sk-",
    )
    return any(b in t for b in bad)


def _user_declines_constraint(message: str) -> bool:
    m = message.lower()
    return any(
        p in m
        for p in (
            "không rõ",
            "khong ro",
            "chưa biết",
            "chua biet",
            "không có",
            "khong co",
            "tùy",
            "không quan trọng",
            "không ràng buộc",
        )
    )


def _wants_done(message: str) -> bool:
    m = message.lower()
    return any(
        p in m
        for p in (
            "ok",
            "được",
            "duoc",
            "sẵn sàng",
            "san sang",
            "xem hướng",
            "xem goi y",
            "đúng rồi",
            "dung roi",
            "ổn",
            "xon",
        )
    )


# ---------- deterministic LLM-free turn ----------


def _compact_interest_label(text: str) -> str | None:
    """PR-10: avoid dumping the full utterance as an interest (noise)."""
    raw = re.sub(r"\s+", " ", (text or "").strip())
    if len(raw) < 8 or _looks_like_injection(raw):
        return None
    lower = raw.lower()
    # Prefer activity-like phrases
    # Avoid false positives like "điện thoại"
    if "điện thoại" in lower and "sửa" not in lower and "hàn" not in lower:
        lower_for_activity = lower.replace("điện thoại", " ")
    else:
        lower_for_activity = lower
    activity_keys = (
        "sửa",
        "vẽ",
        "code",
        "lập trình",
        "dashboard",
        "excel",
        "nấu",
        "dạy",
        "thiết kế",
        "chăm",
        "phân tích",
        "máy móc",
        "đồ điện",
        "hàn",
        "game",
        "viết",
        "quay video",
        "edit",
    )
    if any(k in lower_for_activity for k in activity_keys):
        # keep a short clause, not the whole paragraph
        label = raw
        for sep in (".", "!", "?", ","):
            if sep in label:
                label = label.split(sep)[0].strip()
                break
        if len(label) > 40:
            label = label[:37] + "…"
        return label
    # Generic long answers: do not invent a fake interest from whole sentence
    if len(raw) > 60:
        return None
    if len(raw) > 40:
        return raw[:37] + "…"
    return raw


def _extract_job_goal(text: str, phase: Phase) -> str | None:
    """Only set job_goal on clear intent (not every message containing 'việc')."""
    lower = text.lower()
    if phase not in ("warmup", "interests", "constraints", "wrapup"):
        # abilities turns usually describe tools, not goals
        if not any(k in lower for k in ("muốn làm", "tìm việc", "ứng tuyển", "entry", "fresher")):
            return None
    goal_markers = (
        "muốn làm",
        "tìm việc",
        "muốn tìm",
        "entry-level",
        "entry level",
        "fresher",
        "thực tập",
        "data",
        "dữ liệu",
        "lập trình",
        "marketing",
        "kế toán",
        "thiết kế",
    )
    if not any(k in lower for k in goal_markers):
        return None
    # Prefer short canned goals when keywords match
    if "data" in lower or "dữ liệu" in lower or "excel" in lower or "dashboard" in lower:
        return "việc dữ liệu / phân tích entry-level"
    if any(k in lower for k in ("lập trình", "react", "python", "web", "code")):
        return "việc lập trình / web entry-level"
    if "marketing" in lower:
        return "việc digital marketing entry-level"
    # fallback: first 80 chars if short enough intent phrase
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned[:80] if len(cleaned) <= 80 else cleaned[:77] + "…"


def deterministic_turn(
    *,
    journey_mode: JourneyMode,
    phase: Phase,
    message: str,
    turn: int,
    fallback_index: int,
    recent_replies: list[str] | None = None,
) -> ProfilerTurnOutput:
    """Build a structured turn without calling a model provider."""
    text = (message or "").strip()
    delta = ProfileDelta()
    lower = text.lower()

    if journey_mode == "launch":
        if any(k in lower for k in ("năm cuối", "nam cuoi", "final year")):
            delta.education_stage = "final_year"
        if any(k in lower for k in ("mới tốt nghiệp", "moi tot nghiep", "tốt nghiệp")):
            delta.education_stage = "recent_graduate"
        goal = _extract_job_goal(text, phase)
        if goal:
            delta.job_goal = goal
        if any(k in lower for k in ("chưa có thực tập", "chưa có project", "chưa có kinh nghiệm", "không có project")):
            from app.models.profiler_io import ConstraintsDelta

            delta.constraints = ConstraintsDelta(notes="chưa có thực tập/project — explicit no experience")
        if any(k in lower for k in ("project", "dashboard", "app ", "thực tập", "internship")):
            title = "Project từ hội thoại"
            if "dashboard" in lower:
                title = "Dashboard"
            elif "todo" in lower or "react" in lower:
                title = "App todo"
            skills: list[str] = []
            for token in ("excel", "react", "python", "sql", "figma", "powerpoint", "word"):
                if token in lower:
                    skills.append(
                        token.upper()
                        if token == "sql"
                        else ("Excel" if token == "excel" else token.capitalize())
                    )
            delta.experiences = [
                ExperienceEvidence(
                    title=title,
                    kind="internship" if "thực tập" in lower or "internship" in lower else "project",
                    description=text[:200],
                    skills=skills,
                    source_quote=text[:240],
                )
            ]
            for s in skills:
                delta.skills.append(
                    ProfileSkill(name=s, level="đã đề cập", source_quote=text[:240])
                )
    else:
        if any(k in lower for k in ("lớp 12", "lớp 11", "cấp 3", "học sinh")):
            delta.education_stage = "high_school"

    # Interests: compact labels only (PR-10); skip pure ability/tool turns
    if phase in ("warmup", "interests", "constraints") or journey_mode == "launch" and phase == "interests":
        label = _compact_interest_label(text)
        if label:
            delta.interests = [label]
    elif phase == "abilities" and not any(
        k in lower for k in ("excel", "python", "react", "khen", "giỏi", "làm tốt")
    ):
        label = _compact_interest_label(text)
        if label:
            delta.interests = [label]

    # Dimension bumps from keywords
    dims: dict[str, float] = {}
    for dim, kws in _DIM_KEYWORDS.items():
        if any(k in lower for k in kws):
            dims[dim] = 0.55
    delta.dimensions = dims

    # Skills from tool keywords if not already added
    tool_map = {
        "excel": "Excel",
        "react": "React",
        "python": "Python",
        "figma": "Figma",
        "photoshop": "Photoshop",
        "javascript": "JavaScript",
        "sql": "SQL",
    }
    existing = {s.name.lower() for s in delta.skills}
    for key, name in tool_map.items():
        if key in lower and name.lower() not in existing and not _looks_like_injection(name):
            delta.skills.append(
                ProfileSkill(name=name, level="đã đề cập", source_quote=text[:240] or name)
            )

    if text and not _looks_like_injection(text):
        mapped = next(iter(dims.keys()), "interests")
        delta.evidence_quotes = [
            EvidenceQuote(turn=turn, quote=text[:240], mapped_to=mapped)
        ]

    # Soft constraints
    if any(k in lower for k in ("hà nội", "hanoi", "hcm", "sài gòn", "đà nẵng", "danang")):
        from app.models.profiler_io import ConstraintsDelta

        region = "hanoi" if "hà nội" in lower or "hanoi" in lower else (
            "hcm" if "hcm" in lower or "sài gòn" in lower else (
                "danang" if "đà nẵng" in lower or "danang" in lower else None
            )
        )
        if region:
            if delta.constraints is None:
                delta.constraints = ConstraintsDelta(region_pref=region)
            else:
                delta.constraints.region_pref = region

    if any(k in lower for k in ("hạn chế", "eo hẹp", "không có nhiều tiền", "ngân sách thấp")):
        from app.models.profiler_io import ConstraintsDelta

        if delta.constraints is None:
            delta.constraints = ConstraintsDelta(study_budget="hạn chế")
        else:
            delta.constraints.study_budget = "hạn chế"

    reply = get_fallback_question(
        journey_mode, phase, fallback_index, recent_replies=recent_replies
    )
    return ProfilerTurnOutput(reply=reply, profile_delta=delta, phase_done=False)


# ---------- public API ----------


def handle_turn(
    session_id: str,
    message: Optional[str],
    journey_mode: JourneyMode = "explore",
) -> ChatResponse:
    state = session_store.get_session(session_id)
    if state is None:
        state = session_store.create_session(session_id, journey_mode)
    else:
        # Mode locked after opening — ignore later journey_mode changes
        journey_mode = state.journey_mode

    def _recent_assistant() -> list[str]:
        return [
            m["content"]
            for m in state.messages
            if m.get("role") == "assistant" and m.get("content")
        ][-4:]

    # Opening turn (no user message yet)
    if message is None or (isinstance(message, str) and message.strip() == "" and state.turn == 0):
        state.turn = 1
        state.phase = "warmup"
        state.turns_in_phase = 0
        reply = get_fallback_question(
            state.journey_mode,
            "warmup",
            state.fallback_index,
            recent_replies=_recent_assistant(),
        )
        state.fallback_index += 1
        state.messages.append({"role": "assistant", "content": reply})
        state.profile.completeness = compute_completeness(
            state.journey_mode, state.profile, state.constraint_declined
        )
        session_store.save_session(state)
        return ChatResponse(
            reply=reply,
            phase=state.phase,
            turn=state.turn,
            done=False,
            profile=state.profile,
        )

    user_text = (message or "").strip()
    state.messages.append({"role": "user", "content": user_text})
    state.turn += 1
    state.turns_in_phase += 1

    if _user_declines_constraint(user_text):
        state.constraint_declined = True

    # PR-13: optional agent path for discover/confirm (langgraph mode only).
    # Classic path always remains fallback; API shape unchanged; no CoT in response.
    from app.services import agent_chat

    agent_reply: str | None = None
    agent_delta = None
    if agent_chat.agent_enabled_for_chat():
        enrich = agent_chat.run_agent_enrichment(state, user_text)
        agent_delta = enrich.get("delta")
        if not enrich.get("fallback"):
            agent_reply = enrich.get("reply")
        # never expose enrich["trace"] on ChatResponse
    else:
        # Deterministic: may still use local extract tool (no graph/network planner)
        agent_delta = agent_chat.maybe_run_extract_tools_only(state, user_text)

    turn_out = _produce_turn_output(state, user_text)
    # Prefer agent-extracted delta when present (then classic delta fills gaps)
    delta = turn_out.profile_delta
    if agent_delta is not None:
        # merge agent delta first so classic can add more signals
        state.profile = merge_delta(
            state.profile, agent_delta, state.corrections, state.turn
        )
    state.profile = merge_delta(
        state.profile, delta, state.corrections, state.turn
    )
    state.profile.session_id = session_id
    state.profile.journey_mode = state.journey_mode
    state.profile.completeness = compute_completeness(
        state.journey_mode, state.profile, state.constraint_declined
    )

    force_done = state.phase == "wrapup" and _wants_done(user_text)
    new_phase, done, turns_in_phase = advance_phase(
        state.journey_mode,
        state.phase,
        state.profile,
        constraint_declined=state.constraint_declined,
        turns_in_phase=state.turns_in_phase,
        force_done_signal=force_done,
    )
    if new_phase != state.phase:
        state.phase = new_phase
        state.turns_in_phase = turns_in_phase
        # After phase change, prefer a question for the new phase
        if not done and state.phase != "wrapup":
            turn_out.reply = get_fallback_question(
                state.journey_mode,
                state.phase,
                state.fallback_index,
                recent_replies=_recent_assistant() + [turn_out.reply],
            )
            state.fallback_index += 1
    else:
        state.turns_in_phase = turns_in_phase

    if done or force_done:
        state.done = True
        state.phase = "wrapup"

    # Cap runaway turns still allow wrapup CTA after many messages
    if state.turn >= 10 and state.phase in ("constraints", "wrapup"):
        state.phase = "wrapup"
        if state.turn >= 12:
            state.done = True

    # Prefer agent-composed reply only when non-empty and not done CTA phase
    if agent_reply and not state.done and state.phase != "wrapup":
        reply = agent_reply.strip()
    else:
        reply = turn_out.reply.strip() or get_fallback_question(
            state.journey_mode,
            state.phase,
            state.fallback_index,
            recent_replies=_recent_assistant(),
        )
    # Final de-dupe against last assistant message
    recent = _recent_assistant()
    if reply in recent:
        reply = get_fallback_question(
            state.journey_mode,
            state.phase,
            state.fallback_index + 1,
            recent_replies=recent,
        )
        state.fallback_index += 1
    state.messages.append({"role": "assistant", "content": reply})
    # Keep only last 16 messages in session (demo memory bound)
    state.messages = state.messages[-16:]
    session_store.save_session(state)

    return ChatResponse(
        reply=reply,
        phase=state.phase,
        turn=state.turn,
        done=state.done,
        profile=state.profile,
    )


def _produce_turn_output(state: SessionState, user_text: str) -> ProfilerTurnOutput:
    settings = get_settings()
    use_llm = bool(settings.chat_api_key) and settings.demo_mode != "replay"
    recent = [
        m["content"]
        for m in state.messages
        if m.get("role") == "assistant" and m.get("content")
    ][-4:]

    if use_llm:
        try:
            system = build_profiler_system(state.journey_mode, state.phase)
            # Only pass recent messages; do not log them.
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in state.messages[-8:]
                if m.get("role") in ("user", "assistant")
            ]
            return chat_json(system, history, ProfilerTurnOutput, max_retries=2)
        except LLMError as exc:
            log.warning("profiler LLM fallback session=%s err=%s", state.session_id, type(exc).__name__)

    out = deterministic_turn(
        journey_mode=state.journey_mode,
        phase=state.phase,
        message=user_text,
        turn=state.turn,
        fallback_index=state.fallback_index,
        recent_replies=recent,
    )
    state.fallback_index += 1
    return out


def get_profile(session_id: str) -> Profile:
    state = session_store.get_session(session_id)
    if state is None:
        raise KeyError(session_id)
    return state.profile


def patch_profile(session_id: str, patch: ProfilePatch) -> Profile:
    state = session_store.get_session(session_id)
    if state is None:
        raise KeyError(session_id)
    state.profile = apply_patch(state.profile, patch, state.corrections)
    state.profile.session_id = session_id
    state.profile.journey_mode = state.journey_mode
    session_store.save_session(state)
    return state.profile


def delete_session(session_id: str) -> bool:
    return session_store.delete_session(session_id)
