"""Integration: PR-03 profiler session engine via HTTP (no live LLM)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.integration


def test_mode_locked_after_opening(client: TestClient) -> None:
    client.post("/api/chat", json={"session_id": "lock-1", "message": None, "journey_mode": "launch"})
    # Later call tries to flip mode — ignored
    r = client.post(
        "/api/chat",
        json={"session_id": "lock-1", "message": "Em năm cuối CNTT", "journey_mode": "explore"},
    )
    assert r.status_code == 200
    assert r.json()["profile"]["journey_mode"] == "launch"


def test_patch_persists_and_survives_next_get(client: TestClient) -> None:
    sid = "patch-persist"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "launch"})
    client.post(
        "/api/chat",
        json={"session_id": sid, "message": "Em năm cuối muốn làm data", "journey_mode": "launch"},
    )
    pr = client.patch(
        f"/api/profile/{sid}",
        json={"education_stage": "final_year", "job_goal": "analyst intern"},
    )
    assert pr.status_code == 200
    assert pr.json()["profile"]["job_goal"] == "analyst intern"

    gr = client.get(f"/api/profile/{sid}")
    assert gr.status_code == 200
    assert gr.json()["profile"]["job_goal"] == "analyst intern"

    # Clear via null
    pr2 = client.patch(f"/api/profile/{sid}", json={"job_goal": None})
    assert pr2.json()["profile"]["job_goal"] is None
    assert client.get(f"/api/profile/{sid}").json()["profile"]["job_goal"] is None


def test_delete_session(client: TestClient) -> None:
    sid = "del-1"
    client.post("/api/chat", json={"session_id": sid, "message": None})
    assert client.delete(f"/api/profile/{sid}").status_code == 200
    assert client.get(f"/api/profile/{sid}").status_code == 404
    assert client.delete(f"/api/profile/{sid}").status_code == 404


def test_ten_turn_explore_reaches_later_phase(client: TestClient) -> None:
    sid = "explore-10"
    messages = [
        None,
        "Em học lớp 12 ở Đà Nẵng",
        "Em hay sửa quạt và đồ điện trong nhà",
        "Thích lúc tìm ra chỗ hỏng",
        "Mọi người khen em hàn dây cẩn thận",
        "Em dùng mỏ hàn và đồng hồ vạn năng",
        "Gia đình muốn em học gần nhà, ngân sách hạn chế",
        "Em cũng thích vẽ tay khi rảnh",
        "Thầy khen em khéo tay thực hành",
        "Hồ sơ vậy ổn, em sẵn sàng xem hướng đi",
        "Ok xem gợi ý đi",
        "Được rồi",
    ]
    last = None
    for msg in messages:
        body: dict = {"session_id": sid, "journey_mode": "explore"}
        body["message"] = msg
        last = client.post("/api/chat", json=body)
        assert last.status_code == 200, last.text
    assert last is not None
    data = last.json()
    assert data["turn"] >= 10
    assert data["phase"] in ("constraints", "wrapup")
    profile = data["profile"]
    assert profile["journey_mode"] == "explore"
    assert len(profile["interests"]) >= 1 or len(profile["skills"]) >= 1
    # Should not invent gender
    assert "gender" not in profile


def test_ten_turn_launch_builds_experience_signals(client: TestClient) -> None:
    sid = "launch-10"
    messages = [
        None,
        "Em năm cuối, muốn tìm việc data entry-level",
        "Em làm dashboard bán hàng từ CSV",
        "Em clean data và vẽ biểu đồ bằng Excel",
        "Cũng biết chút Python để đọc file",
        "Muốn làm ở Đà Nẵng sau tốt nghiệp",
        "Chưa có thực tập chính thức",
        "Project dashboard là evidence chính",
        "Dùng VS Code khi viết script nhỏ",
        "Hồ sơ ổn, sẵn sàng xem nhóm việc",
        "Ok",
    ]
    last = None
    for msg in messages:
        last = client.post(
            "/api/chat",
            json={"session_id": sid, "message": msg, "journey_mode": "launch"},
        )
        assert last.status_code == 200
    data = last.json()
    assert data["turn"] >= 10
    profile = data["profile"]
    assert profile["journey_mode"] == "launch"
    # Expect some launch signals from deterministic extractor
    assert profile["education_stage"] in ("final_year", "recent_graduate", None) or profile[
        "job_goal"
    ]
    skill_names = " ".join(s["name"].lower() for s in profile["skills"])
    assert "excel" in skill_names or "python" in skill_names or profile["experiences"]


def test_correction_not_overwritten_by_later_chat(client: TestClient) -> None:
    sid = "corr-1"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "explore"})
    client.post(
        "/api/chat",
        json={"session_id": sid, "message": "Em giỏi Excel và hay làm bảng tính", "journey_mode": "explore"},
    )
    client.patch(f"/api/profile/{sid}", json={"remove_skills": ["Excel"]})
    r = client.post(
        "/api/chat",
        json={"session_id": sid, "message": "Em lại dùng Excel nữa", "journey_mode": "explore"},
    )
    names = [s["name"].lower() for s in r.json()["profile"]["skills"]]
    assert "excel" not in names
