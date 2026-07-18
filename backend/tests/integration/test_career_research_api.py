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
    evidence = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "Em thích phân tích dữ liệu và đã dùng Excel.",
            "journey_mode": "explore",
        },
    )
    assert evidence.status_code == 200


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


def test_research_rejects_blank_profile_before_generic_candidates(
    client: TestClient,
) -> None:
    sid = "research-blank"
    opened = client.post(
        "/api/chat",
        json={"session_id": sid, "message": None, "journey_mode": "explore"},
    )
    assert opened.status_code == 200

    response = client.post(
        "/api/research/careers",
        json={
            "session_id": sid,
            "career_ids": ["data-analyst"],
            "intent": "overview",
            "region": "all",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "409"


def test_research_off_mode_returns_grounded_local_block(client: TestClient) -> None:
    _open_session(client, "research-ok")
    rec_response = client.post(
        "/api/recommendations", json={"session_id": "research-ok"}
    )
    assert rec_response.status_code == 200
    recs = rec_response.json()
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
