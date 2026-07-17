"""SQLAlchemy engine/session — market.db (read, built by data/pipeline) and sessions.db (chat state).

Use this module for ALL DB access (task PR-03 for sessions, MI-04 reads market.db).
Do not use raw sqlite3 — SQLAlchemy keeps the Postgres upgrade path open (ARCHITECTURE.md §5).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

_settings = get_settings()
market_engine = create_engine(_settings.database_url, connect_args={"check_same_thread": False})
sessions_engine = create_engine(_settings.sessions_db_url, connect_args={"check_same_thread": False})

MarketSession = sessionmaker(bind=market_engine)
ChatSession = sessionmaker(bind=sessions_engine)
