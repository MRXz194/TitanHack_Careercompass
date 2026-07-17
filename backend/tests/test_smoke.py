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
