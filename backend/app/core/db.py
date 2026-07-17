"""SQLAlchemy engine/session — market.db (read) and sessions.db (chat state).

Use this module for ALL DB access (PR-03 sessions, MI-04 market reads).
Do not use raw sqlite3 — SQLAlchemy keeps the Postgres upgrade path open.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models.session_orm import Base

_settings = get_settings()

market_engine = create_engine(
    _settings.database_url, connect_args={"check_same_thread": False}
)
sessions_engine: Engine = create_engine(
    _settings.sessions_db_url, connect_args={"check_same_thread": False}
)

MarketSession = sessionmaker(bind=market_engine)
ChatSessionLocal = sessionmaker(bind=sessions_engine, expire_on_commit=False)


def init_sessions_schema(engine: Engine | None = None) -> None:
    """Create chat session tables if missing."""
    eng = engine or sessions_engine
    Base.metadata.create_all(bind=eng)


def rebind_sessions_engine(database_url: str) -> Engine:
    """Test helper: point sessions at a fresh SQLite URL and recreate schema."""
    global sessions_engine, ChatSessionLocal
    sessions_engine = create_engine(
        database_url, connect_args={"check_same_thread": False}
    )
    ChatSessionLocal = sessionmaker(bind=sessions_engine, expire_on_commit=False)
    Base.metadata.drop_all(bind=sessions_engine)
    Base.metadata.create_all(bind=sessions_engine)
    return sessions_engine


def get_chat_db() -> Session:
    return ChatSessionLocal()


# Ensure schema exists on import for local/dev (idempotent).
init_sessions_schema()
