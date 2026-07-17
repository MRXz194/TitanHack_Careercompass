"""PR-13 integration — chat API with agent modes; recommend has no planner."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.services import agent_graph


pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _reset(monkeypatch: pytest.MonkeyPatch):
    agent_graph.reset_graph_cache()
    monkeypatch.setenv("AGENT_MODE", "deterministic")
    monkeypatch.setenv("DEMO_MODE", "off")
    get_settings.cache_clear()
    yield
    agent_graph.reset_graph_cache()
    get_settings.cache_clear()


def test_chat_api_deterministic_ten_turns_explore(client: TestClient) -> None:
    sid = "ag-ex-10"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "explore"})
    msgs = [
        "Em học lớp 12",
        "Em hay sửa đồ điện",
        "Thích tìm chỗ hỏng",
        "Khen hàn dây",
        "Dùng mỏ hàn",
        "Ngân sách hạn chế gần nhà",
        "Ổn rồi",
        "Sẵn sàng xem hướng",
        "Ok",
        "Được",
    ]
    last = None
    for m in msgs:
        last = client.post(
            "/api/chat",
            json={"session_id": sid, "message": m, "journey_mode": "explore"},
        )
        assert last.status_code == 200
        body = last.json()
        # contract only public fields
        assert set(body.keys()) >= {"reply", "phase", "turn", "done", "profile"}
        assert "trace" not in body
        assert "observations" not in body
        assert "thought_summary" not in body
    assert last is not None
    assert last.json()["turn"] >= 10
    assert agent_graph.graph_was_compiled() is False


def test_chat_api_langgraph_mode_still_contract(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MODE", "langgraph")
    get_settings.cache_clear()
    agent_graph.reset_graph_cache()
    sid = "ag-lg-1"
    r0 = client.post(
        "/api/chat", json={"session_id": sid, "message": None, "journey_mode": "launch"}
    )
    assert r0.status_code == 200
    r1 = client.post(
        "/api/chat",
        json={
            "session_id": sid,
            "message": "Em năm cuối làm dashboard Excel",
            "journey_mode": "launch",
        },
    )
    assert r1.status_code == 200
    body = r1.json()
    assert body["profile"]["journey_mode"] == "launch"
    assert "trace" not in body
    assert body["reply"]


def test_chat_replay_mode_no_graph(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MODE", "langgraph")
    monkeypatch.setenv("DEMO_MODE", "replay")
    get_settings.cache_clear()
    agent_graph.reset_graph_cache()
    sid = "ag-replay"
    client.post("/api/chat", json={"session_id": sid, "message": None})
    client.post("/api/chat", json={"session_id": sid, "message": "Em thích vẽ"})
    assert agent_graph.graph_was_compiled() is False


def test_recommendations_have_no_agent_planner(client: TestClient) -> None:
    """Recommendation path must stay deterministic — no agent stage/plan fields."""
    sid = "ag-rec"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "explore"})
    client.post(
        "/api/chat",
        json={"session_id": sid, "message": "Em hay sửa điện", "journey_mode": "explore"},
    )
    r = client.post("/api/recommendations", json={"session_id": sid})
    assert r.status_code == 200
    body = r.json()
    assert "recommendations" in body and "stretch" in body
    assert "plan" not in body
    assert "trace" not in body
    assert "agent" not in body
