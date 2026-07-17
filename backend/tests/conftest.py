"""Shared test fixtures. No fixture may require a live model provider or network."""
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.chat import _sessions


@pytest.fixture(autouse=True)
def reset_stub_sessions() -> Iterator[None]:
    """Keep current in-memory chat stub isolated until PR-03 moves it to SQLite."""
    _sessions.clear()
    yield
    _sessions.clear()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client

