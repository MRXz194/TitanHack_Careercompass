import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.integration


def test_health_uses_seed_data(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["data_loaded"] is True
    assert body["postings_count"] > 0


def test_framework_404_uses_error_contract(client: TestClient) -> None:
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "404"


def test_validation_error_uses_error_contract(client: TestClient) -> None:
    response = client.post("/api/chat", json={"journey_mode": "explore"})

    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "422", "message": "Dữ liệu gửi lên không hợp lệ"}
    }


def test_chat_rejects_message_over_2000_characters(client: TestClient) -> None:
    response = client.post(
        "/api/chat",
        json={
            "session_id": "message-too-long",
            "message": "x" * 2001,
            "journey_mode": "explore",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "422", "message": "Dữ liệu gửi lên không hợp lệ"}
    }


def test_career_detail_matches_contract(client: TestClient) -> None:
    response = client.get("/api/market/careers/data-analyst")
    assert response.status_code == 200
    body = response.json()
    assert {"career_id", "title", "description", "market", "routes"} <= body.keys()
    assert len(body["routes"]) >= 2


def test_launch_opening_preserves_mode_without_inference(client: TestClient) -> None:
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


def test_chat_omitting_journey_mode_defaults_to_explore(client: TestClient) -> None:
    response = client.post(
        "/api/chat",
        json={"session_id": "explore-compat", "message": None},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["journey_mode"] == "explore"
    assert "gender" not in body["profile"]


def test_patch_null_clears_launch_optional_fields(client: TestClient) -> None:
    # Opening launch has nulls; second turn mock may fill stage/goal — clear them via PATCH.
    open_resp = client.post(
        "/api/chat",
        json={
            "session_id": "patch-clear",
            "message": None,
            "journey_mode": "launch",
        },
    )
    assert open_resp.status_code == 200

    # Advance one turn so stub may populate education_stage/job_goal (turn >= 2).
    client.post(
        "/api/chat",
        json={
            "session_id": "patch-clear",
            "message": "Em năm cuối, muốn làm data entry-level",
            "journey_mode": "launch",
        },
    )

    patch_resp = client.patch(
        "/api/profile/patch-clear",
        json={"education_stage": None, "job_goal": None},
    )
    assert patch_resp.status_code == 200
    profile = patch_resp.json()["profile"]
    assert profile["education_stage"] is None
    assert profile["job_goal"] is None
    assert profile["journey_mode"] == "launch"

