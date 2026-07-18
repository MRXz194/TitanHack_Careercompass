from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.integration


def _open_session(client: TestClient, session_id: str) -> None:
    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": None, "journey_mode": "explore"},
    )
    assert response.status_code == 200


def test_research_rejects_career_outside_session_recommendations(client: TestClient) -> None:
    _open_session(client, "research-deny")
    response = client.post(
        "/api/research/careers",
        json={
            "session_id": "research-deny",
            "career_ids": ["not-a-career"],
            "intent": "overview",
            "region": "all",
        },
    )
    assert response.status_code == 422


def test_research_off_mode_returns_grounded_local_block(client: TestClient) -> None:
    _open_session(client, "research-ok")
    recs = client.post("/api/recommendations", json={"session_id": "research-ok"}).json()
    career_id = recs["recommendations"][0]["career_id"]
    response = client.post(
        "/api/research/careers",
        json={
            "session_id": "research-ok",
            "career_ids": [career_id],
            "intent": "skills",
            "region": "all",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["careers"][0]["career_id"] == career_id
    assert body["careers"][0]["local_market"]["source_note"]
