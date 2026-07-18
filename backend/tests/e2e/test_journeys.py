"""Offline release journeys: real API contract, no provider/network dependency."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.services import agent_graph, profiler

pytestmark = pytest.mark.e2e


def _chat(client: TestClient, session_id: str, mode: str, messages: list[str]) -> dict:
    opening = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": None, "journey_mode": mode},
    )
    assert opening.status_code == 200
    body = opening.json()
    for message in messages:
        response = client.post(
            "/api/chat",
            json={"session_id": session_id, "message": message, "journey_mode": mode},
        )
        assert response.status_code == 200
        body = response.json()
    return body


def _assert_recommendation_contract(payload: dict, *, launch: bool) -> None:
    assert len(payload["recommendations"]) == 5
    assert payload["stretch"]["is_stretch"] is True
    assert "quyết định là của em" in payload["disclaimer"].lower()
    for recommendation in payload["recommendations"]:
        assert len(recommendation["routes"]) >= 2
        assert any(
            route["type"] in {"vocational", "college", "certificate"}
            for route in recommendation["routes"]
        )
        assert recommendation["why"]["from_you"]
        assert recommendation["market"]["source_note"]
        if launch:
            assert recommendation["job_readiness"] is not None
        else:
            assert recommendation["job_readiness"] is None


def test_explore_langgraph_profile_correction_recommend_and_market(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AGENT_MODE", "langgraph")
    monkeypatch.setenv("DEMO_MODE", "off")
    monkeypatch.setenv("CHAT_API_KEY", "")
    get_settings.cache_clear()
    agent_graph.reset_graph_cache()

    session_id = "e2e-explore"
    last = _chat(
        client,
        session_id,
        "explore",
        [
            "Em học lớp 12 và thích sửa đồ điện trong nhà.",
            "Em từng tự hàn lại dây quạt và tìm chỗ hỏng bằng đồng hồ đo.",
            "Em cũng thích phân tích số liệu bằng Excel.",
            "Em muốn học trong khoảng một năm, ngân sách hạn chế và ưu tiên gần nhà.",
        ],
    )
    assert last["profile"]["journey_mode"] == "explore"
    assert agent_graph.graph_was_compiled() is True

    correction = client.patch(
        f"/api/profile/{session_id}",
        json={"remove_skills": ["Excel"], "add_interests": ["máy móc"]},
    )
    assert correction.status_code == 200
    assert all(
        skill["name"].lower() != "excel"
        for skill in correction.json()["profile"]["skills"]
    )

    rec = client.post("/api/recommendations", json={"session_id": session_id})
    assert rec.status_code == 200
    _assert_recommendation_contract(rec.json(), launch=False)

    market = client.get("/api/market/overview?region=all")
    assert market.status_code == 200
    assert market.json()["source_note"]


def test_launch_replay_completes_without_model_provider(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AGENT_MODE", "langgraph")
    monkeypatch.setenv("DEMO_MODE", "replay")
    monkeypatch.setenv("CHAT_API_KEY", "would-not-be-used")
    get_settings.cache_clear()
    agent_graph.reset_graph_cache()

    def provider_must_not_run(*args, **kwargs):
        raise AssertionError("replay journey attempted a model call")

    monkeypatch.setattr(profiler, "chat_json", provider_must_not_run)
    session_id = "e2e-launch-replay"
    last = _chat(
        client,
        session_id,
        "launch",
        [
            "Em là sinh viên năm cuối và muốn tìm việc dữ liệu entry-level.",
            "Em làm project dashboard bằng Excel và SQL cho dữ liệu bán hàng.",
            "Em có thể học thêm buổi tối trong 30 ngày và muốn tìm việc tại Hà Nội.",
        ],
    )
    assert last["profile"]["journey_mode"] == "launch"
    assert agent_graph.graph_was_compiled() is False

    rec = client.post("/api/recommendations", json={"session_id": session_id})
    assert rec.status_code == 200
    _assert_recommendation_contract(rec.json(), launch=True)
