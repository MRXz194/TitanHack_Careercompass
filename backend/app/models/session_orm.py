"""SQLAlchemy ORM for chat sessions (sessions.db). PR-03."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChatSessionRow(Base):
    __tablename__ = "chat_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    journey_mode: Mapped[str] = mapped_column(String(16), default="explore")
    phase: Mapped[str] = mapped_column(String(32), default="warmup")
    turn: Mapped[int] = mapped_column(Integer, default=0)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_json: Mapped[str] = mapped_column(Text, default="{}")
    corrections_json: Mapped[str] = mapped_column(Text, default="{}")
    messages_json: Mapped[str] = mapped_column(Text, default="[]")
    turns_in_phase: Mapped[int] = mapped_column(Integer, default=0)
    constraint_declined: Mapped[bool] = mapped_column(Boolean, default=False)
    fallback_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
