from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_uses_seed_data() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["data_loaded"] is True
    assert body["postings_count"] > 0


def test_framework_404_uses_error_contract() -> None:
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "404"


def test_career_detail_matches_contract() -> None:
    response = client.get("/api/market/careers/data-analyst")
    assert response.status_code == 200
    body = response.json()
    assert {"career_id", "title", "description", "market", "routes"} <= body.keys()
    assert len(body["routes"]) >= 2


def test_launch_opening_preserves_mode_in_profile() -> None:
    response = client.post(
        "/api/chat",
        json={"session_id": "launch-smoke", "message": None, "journey_mode": "launch"},
    )
    assert response.status_code == 200
    profile = response.json()["profile"]
    assert profile["journey_mode"] == "launch"
    assert profile["education_stage"] is None
    assert profile["job_goal"] is None
    assert all(value == 0.0 for value in profile["dimensions"].values())
    assert profile["experiences"] == []
