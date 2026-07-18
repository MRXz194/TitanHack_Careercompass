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
