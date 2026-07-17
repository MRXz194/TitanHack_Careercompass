"""PR-10 integration: no consecutive duplicate assistant questions; cleaner interests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.integration


def test_chat_does_not_repeat_same_question_consecutively(client: TestClient) -> None:
    sid = "q-repeat"
    replies: list[str] = []
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "explore"})
    # pull opening from get via second call pattern — re-open by new messages
    # First response already stored; continue conversation
    messages = [
        "Em học lớp 12",
        "Em hay sửa đồ điện",
        "Thích tìm chỗ hỏng",
        "Được khen hàn dây",
        "Dùng mỏ hàn",
        "Gần nhà, ngân sách hạn chế",
    ]
    # re-fetch by replaying: get first reply from first user turn chain
    # Opening already happened; send user turns
    r0 = client.post(
        "/api/chat",
        json={"session_id": sid + "-b", "message": None, "journey_mode": "explore"},
    )
    replies.append(r0.json()["reply"])
    for msg in messages:
        r = client.post(
            "/api/chat",
            json={"session_id": sid + "-b", "message": msg, "journey_mode": "explore"},
        )
        assert r.status_code == 200
        replies.append(r.json()["reply"])
    for a, b in zip(replies, replies[1:]):
        assert a != b, f"consecutive duplicate question: {a!r}"


def test_chat_interests_not_full_sentence_dump(client: TestClient) -> None:
    sid = "q-interest"
    client.post("/api/chat", json={"session_id": sid, "message": None, "journey_mode": "explore"})
    long_msg = (
        "Em hay sửa quạt và đồ điện trong nhà mỗi cuối tuần "
        "và thỉnh thoảng giúp hàng xóm luôn"
    )
    r = client.post(
        "/api/chat",
        json={"session_id": sid, "message": long_msg, "journey_mode": "explore"},
    )
    interests = r.json()["profile"]["interests"]
    assert interests
    assert all(len(i) <= 48 for i in interests)
