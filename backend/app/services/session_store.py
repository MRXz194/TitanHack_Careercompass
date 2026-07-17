"""Persist profiler sessions in SQLite (sessions.db)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.db import get_chat_db, init_sessions_schema
from app.models.schemas import JourneyMode, Phase, Profile
from app.models.session_orm import ChatSessionRow


@dataclass
class Corrections:
    """User corrections that outrank model inference on later merges."""

    removed_skills: set[str] = field(default_factory=set)
    removed_experience_titles: set[str] = field(default_factory=set)
    locked_education_stage: bool = False
    locked_job_goal: bool = False
    dimension_overrides: dict[str, float] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(
            {
                "removed_skills": sorted(self.removed_skills),
                "removed_experience_titles": sorted(self.removed_experience_titles),
                "locked_education_stage": self.locked_education_stage,
                "locked_job_goal": self.locked_job_goal,
                "dimension_overrides": self.dimension_overrides,
            },
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, raw: str) -> "Corrections":
        if not raw:
            return cls()
        data = json.loads(raw)
        return cls(
            removed_skills=set(data.get("removed_skills") or []),
            removed_experience_titles=set(data.get("removed_experience_titles") or []),
            locked_education_stage=bool(data.get("locked_education_stage")),
            locked_job_goal=bool(data.get("locked_job_goal")),
            dimension_overrides=dict(data.get("dimension_overrides") or {}),
        )


@dataclass
class SessionState:
    session_id: str
    journey_mode: JourneyMode
    phase: Phase
    turn: int
    done: bool
    profile: Profile
    corrections: Corrections
    messages: list[dict[str, str]]
    turns_in_phase: int
    constraint_declined: bool
    fallback_index: int


def _row_to_state(row: ChatSessionRow) -> SessionState:
    profile = Profile.model_validate(json.loads(row.profile_json or "{}"))
    profile.session_id = row.session_id
    profile.journey_mode = row.journey_mode  # type: ignore[assignment]
    return SessionState(
        session_id=row.session_id,
        journey_mode=row.journey_mode,  # type: ignore[arg-type]
        phase=row.phase,  # type: ignore[arg-type]
        turn=row.turn,
        done=row.done,
        profile=profile,
        corrections=Corrections.from_json(row.corrections_json or "{}"),
        messages=list(json.loads(row.messages_json or "[]")),
        turns_in_phase=row.turns_in_phase,
        constraint_declined=row.constraint_declined,
        fallback_index=row.fallback_index,
    )


def get_session(session_id: str) -> SessionState | None:
    init_sessions_schema()
    db = get_chat_db()
    try:
        row = db.get(ChatSessionRow, session_id)
        if row is None:
            return None
        return _row_to_state(row)
    finally:
        db.close()


def create_session(session_id: str, journey_mode: JourneyMode = "explore") -> SessionState:
    init_sessions_schema()
    profile = Profile(session_id=session_id, journey_mode=journey_mode)
    state = SessionState(
        session_id=session_id,
        journey_mode=journey_mode,
        phase="warmup",
        turn=0,
        done=False,
        profile=profile,
        corrections=Corrections(),
        messages=[],
        turns_in_phase=0,
        constraint_declined=False,
        fallback_index=0,
    )
    save_session(state)
    return state


def save_session(state: SessionState) -> None:
    init_sessions_schema()
    db = get_chat_db()
    try:
        row = db.get(ChatSessionRow, state.session_id)
        payload = {
            "journey_mode": state.journey_mode,
            "phase": state.phase,
            "turn": state.turn,
            "done": state.done,
            "profile_json": state.profile.model_dump_json(),
            "corrections_json": state.corrections.to_json(),
            "messages_json": json.dumps(state.messages, ensure_ascii=False),
            "turns_in_phase": state.turns_in_phase,
            "constraint_declined": state.constraint_declined,
            "fallback_index": state.fallback_index,
            "updated_at": datetime.now(timezone.utc),
        }
        if row is None:
            row = ChatSessionRow(session_id=state.session_id, **payload)
            db.add(row)
        else:
            for key, value in payload.items():
                setattr(row, key, value)
        db.commit()
    finally:
        db.close()


def delete_session(session_id: str) -> bool:
    init_sessions_schema()
    db = get_chat_db()
    try:
        row = db.get(ChatSessionRow, session_id)
        if row is None:
            return False
        db.delete(row)
        db.commit()
        return True
    finally:
        db.close()


def clear_all_sessions() -> None:
    """Test helper."""
    from sqlalchemy import delete

    init_sessions_schema()
    db = get_chat_db()
    try:
        db.execute(delete(ChatSessionRow))
        db.commit()
    finally:
        db.close()
