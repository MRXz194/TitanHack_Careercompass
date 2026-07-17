"""Shared test fixtures. No fixture may require a live model provider or network."""
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core import db as db_module
from app.core.config import get_settings
from app.main import app
from app.services import session_store


@pytest.fixture(autouse=True)
def isolated_sessions_db(tmp_path: Path) -> Iterator[None]:
    """Each test gets a fresh SQLite sessions DB; never touch the dev sessions.db."""
    url = f"sqlite:///{tmp_path / 'test_sessions.db'}"
    db_module.rebind_sessions_engine(url)
    session_store.clear_all_sessions()
    yield
    session_store.clear_all_sessions()
    get_settings.cache_clear()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
