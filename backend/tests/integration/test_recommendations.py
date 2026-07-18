"""PR-05 integration — /api/recommendations uses matching engine."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.integration


def test_recommendations_without_session_returns_404(client: TestClient) -> None:
    """A session that never chatted has no profile to ground evidence in — must not
    fabricate a "personalized" recommendation from an empty profile (docs/API_CONTRACT.md
    §recommendations: 404 -> FE sends the user back to /explore)."""
    r = client.post("/api/recommendations", json={"session_id": "no-prior-chat"})
    assert r.status_code == 404
    body = r.json()
    assert "error" in body


def test_opened_but_blank_session_returns_409_instead_of_fake_personalization(
    client: TestClient,
) -> None:
    sid = "blank-opened-session"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "explore"})
    response = client.post("/api/recommendations", json={"session_id": sid})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "409"


def test_recommendations_after_chat_reflect_profile(client: TestClient) -> None:
    sid = "rec-chat-1"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "explore"})
    client.post(
        "/api/chat",
        json={
            "session_id": sid,
            "message": "Em hay sửa quạt điện lạnh và hàn dây điện",
            "journey_mode": "explore",
        },
    )
    r = client.post("/api/recommendations", json={"session_id": sid})
    assert r.status_code == 200
    body = r.json()
    assert len(body["recommendations"]) == 5
    for rec in body["recommendations"]:
        assert len(rec["routes"]) >= 2
        types = {rt["type"] for rt in rec["routes"]}
        assert types & {"vocational", "college", "certificate"}
        assert rec["why"]["counterfactual"]
        assert rec["market"]["demand_count_90d"] >= 0


def test_launch_recommendations_include_job_readiness(client: TestClient) -> None:
    sid = "rec-launch-1"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "launch"})
    client.post(
        "/api/chat",
        json={
            "session_id": sid,
            "message": "Em năm cuối làm dashboard Excel và biết chút Python",
            "journey_mode": "launch",
        },
    )
    r = client.post("/api/recommendations", json={"session_id": sid})
    assert r.status_code == 200
    recs = r.json()["recommendations"]
    assert any(rec.get("job_readiness") is not None for rec in recs)


def test_missing_session_id_422(client: TestClient) -> None:
    r = client.post("/api/recommendations", json={})
    assert r.status_code == 422


def test_what_if_invalid_skill_returns_422_not_500(client: TestClient) -> None:
    sid = "what-if-invalid"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "explore"})
    client.post(
        "/api/chat",
        json={
            "session_id": sid,
            "message": "Em thích phân tích dữ liệu bằng Excel.",
            "journey_mode": "explore",
        },
    )
    response = client.post(
        "/api/recommendations/what-if",
        json={"session_id": sid, "skill": "GPA 3.8"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "422"


def test_what_if_rejects_blank_profile_before_generic_preview(client: TestClient) -> None:
    sid = "what-if-blank"
    client.post(
        "/api/chat",
        json={"session_id": sid, "message": None, "journey_mode": "explore"},
    )

    response = client.post(
        "/api/recommendations/what-if",
        json={"session_id": sid, "skill": "SQL"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "409"
