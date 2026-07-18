"""Integration: PR-03 profiler session engine via HTTP (no live LLM)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services import session_store


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


def test_reopening_existing_session_is_idempotent(client: TestClient) -> None:
    sid = "resume-without-rewind"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "explore"})
    before = client.post(
        "/api/chat",
        json={
            "session_id": sid,
            "message": "Em thích vẽ tranh và thiết kế poster.",
            "journey_mode": "explore",
        },
    ).json()

    reopened = client.post(
        "/api/chat",
        json={"session_id": sid, "message": None, "journey_mode": "explore"},
    ).json()

    assert reopened["turn"] == before["turn"]
    assert reopened["phase"] == before["phase"]
    assert reopened["done"] == before["done"]
    assert reopened["profile"] == before["profile"]
    assert "đang làm dở" in reopened["reply"]

    blank = client.post(
        "/api/chat",
        json={"session_id": sid, "message": "   ", "journey_mode": "explore"},
    ).json()
    assert blank["turn"] == before["turn"]
    assert blank["profile"] == before["profile"]


def test_removed_interest_stays_removed_after_later_chat(client: TestClient) -> None:
    sid = "remove-interest-durable"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "explore"})
    added = client.patch(
        f"/api/profile/{sid}",
        json={"add_interests": ["vẽ tranh"]},
    )
    assert "vẽ tranh" in added.json()["profile"]["interests"]

    removed = client.patch(
        f"/api/profile/{sid}",
        json={"remove_interests": ["vẽ tranh"]},
    )
    assert "vẽ tranh" not in removed.json()["profile"]["interests"]

    later = client.post(
        "/api/chat",
        json={"session_id": sid, "message": "Em lại nhắc đến vẽ tranh.", "journey_mode": "explore"},
    )
    assert not any("vẽ tranh" in interest.lower() for interest in later.json()["profile"]["interests"])


def test_two_personas_never_share_profile_state(client: TestClient) -> None:
    for sid, message in (
        ("persona-tech", "Em hay sửa quạt, lắp ráp máy móc và hàn dây."),
        ("persona-creative", "Em thích vẽ tranh, thiết kế poster bằng Figma."),
    ):
        client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "explore"})
        response = client.post(
            "/api/chat",
            json={"session_id": sid, "message": message, "journey_mode": "explore"},
        )
        assert response.status_code == 200

    tech = client.get("/api/profile/persona-tech").json()["profile"]
    creative = client.get("/api/profile/persona-creative").json()["profile"]
    assert tech["session_id"] != creative["session_id"]
    assert tech["dimensions"]["ky_thuat"] > tech["dimensions"]["sang_tao"]
    assert creative["dimensions"]["sang_tao"] > creative["dimensions"]["ky_thuat"]
    assert all(skill["name"] != "Figma" for skill in tech["skills"])


def test_uncertainty_outside_constraints_does_not_mark_constraints_declined(
    client: TestClient,
) -> None:
    sid = "uncertainty-not-decline"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "explore"})
    client.post(
        "/api/chat",
        json={"session_id": sid, "message": "Em chưa biết mình thích nghề gì.", "journey_mode": "explore"},
    )
    state = session_store.get_session(sid)
    assert state is not None
    assert state.constraint_declined is False


def test_chat_redacts_direct_identifiers_before_persistence(client: TestClient) -> None:
    sid = "privacy-redaction"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "explore"})
    response = client.post(
        "/api/chat",
        json={
            "session_id": sid,
            "message": (
                "Em là nữ, GPA 3.8, email student@example.com, số 0912 345 678; "
                "em thích sửa đồ điện."
            ),
            "journey_mode": "explore",
        },
    )
    assert response.status_code == 200
    state = session_store.get_session(sid)
    assert state is not None
    persisted = str(state.messages) + state.profile.model_dump_json()
    assert "student@example.com" not in persisted
    assert "0912 345 678" not in persisted
    assert "GPA" not in persisted
    assert "3.8" not in persisted
    assert "nữ" not in persisted.lower()
    assert "sửa đồ điện" in persisted


@pytest.mark.parametrize(
    "case_name,message",
    [
        ("gender", "Em là nữ"),
        (
            "combined-contact",
            "Tên em là An, em là nữ, email của em là an@example.com, "
            "liên hệ qua số điện thoại 0912345678, API key là sk-abcdefgh123",
        ),
    ],
)
def test_identifier_only_turn_does_not_advance_or_persist_user_text(
    client: TestClient, case_name: str, message: str
) -> None:
    sid = f"privacy-only-turn-{case_name}"
    opened = client.post(
        "/api/chat",
        json={"session_id": sid, "message": None, "journey_mode": "explore"},
    ).json()
    response = client.post(
        "/api/chat",
        json={"session_id": sid, "message": message, "journey_mode": "explore"},
    ).json()
    assert response["turn"] == opened["turn"]
    assert response["phase"] == opened["phase"]
    assert response["profile"] == opened["profile"]
    state = session_store.get_session(sid)
    assert state is not None
    assert not any(item.get("role") == "user" for item in state.messages)
    assert "không dùng thông tin nhận dạng" in response["reply"]
