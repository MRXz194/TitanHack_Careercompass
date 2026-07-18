"""Persona-driven release tests for the workflows a judge/student actually uses.

These tests are deliberately offline and exercise HTTP boundaries, persistence,
profiling, matching, evidence, pathways, research fallback and what-if immutability.
"""
from __future__ import annotations

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings

pytestmark = pytest.mark.e2e


EXPLORE_PERSONAS = {
    "technical": {
        "dimension": "ky_thuat",
        "messages": [
            "Em học lớp 12 và hay sửa quạt, sửa đồ điện trong nhà.",
            "Em tự lắp ráp máy móc nhỏ và hàn dây cho mô hình.",
            "Em thích nhất lúc sửa xe và tìm được bộ phận bị hỏng.",
            "Ngân sách học hạn chế, em ưu tiên lộ trình thực hành.",
        ],
        "family": {
            "ky-thuat-vien-dien-lanh", "co-khi-cnc", "ky-thuat-vien-sua-chua-o-to",
            "ky-thuat-vien-dien-dan-dung", "quan-tri-mang-an-ninh",
        },
    },
    "analytical": {
        "dimension": "phan_tich",
        "messages": [
            "Em thích phân tích dữ liệu bán hàng bằng Excel.",
            "Em làm dashboard số liệu và tự viết câu SQL để kiểm tra.",
            "Em thích bài toán logic và tìm nguyên nhân khi số liệu sai.",
            "Em muốn học theo dự án và có output kiểm tra được.",
        ],
        "family": {"data-analyst", "ke-toan", "kiem-thu-phan-mem", "lap-trinh-vien-web"},
    },
    "creative": {
        "dimension": "sang_tao",
        "messages": [
            "Em thích vẽ tranh và thiết kế poster bằng Figma.",
            "Em hay viết content và quay video cho câu lạc bộ.",
            "Em dùng Photoshop để thiết kế màu sắc cho một bộ nhận diện.",
            "Em muốn thử cả chứng chỉ ngắn hạn và cao đẳng.",
        ],
        "family": {"thiet-ke-do-hoa", "viet-content-copywriter", "chup-anh-quay-phim", "digital-marketing"},
    },
    "social": {
        "dimension": "xa_hoi",
        "messages": [
            "Em thích dạy học và giúp bạn hiểu bài.",
            "Em tham gia tình nguyện chăm sóc người cao tuổi.",
            "Em thích tư vấn, giao tiếp và hướng dẫn người khác.",
            "Em muốn xem cả lộ trình nghề và đại học, không chỉ một lựa chọn.",
        ],
        "family": {
            "dieu-duong", "cham-soc-khach-hang", "tu-van-tuyen-sinh",
            "giao-vien-tieng-anh", "nhan-vien-ban-hang",
        },
    },
    "organizer": {
        "dimension": "quan_ly",
        "messages": [
            "Em thích tổ chức nhóm và chia việc cho sự kiện trường.",
            "Em điều phối lịch, nhắc tiến độ và xử lý việc phát sinh.",
            "Em từng quản lý gian hàng nhỏ và thích kinh doanh.",
            "Em muốn lộ trình có thể vừa học vừa làm.",
        ],
        "family": {
            "nhan-vien-chuyen-phat-logistics", "nhan-vien-hanh-chinh",
            "logistics-van-hanh", "nhan-vien-nhan-su", "quan-tri-nha-hang-khach-san",
        },
    },
}


def _configure_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_MODE", "replay")
    monkeypatch.setenv("AGENT_MODE", "deterministic")
    monkeypatch.setenv("CHAT_API_KEY", "")
    get_settings.cache_clear()


def _chat(client: TestClient, session_id: str, mode: str, messages: list[str]) -> dict:
    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": None, "journey_mode": mode},
    )
    assert response.status_code == 200
    body = response.json()
    for message in messages:
        response = client.post(
            "/api/chat",
            json={"session_id": session_id, "message": message, "journey_mode": mode},
        )
        assert response.status_code == 200, response.text
        body = response.json()
    return body


def test_signal_rich_personas_do_not_collapse_to_one_ranking(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_offline(monkeypatch)
    top_ones: dict[str, str] = {}
    top_threes: dict[str, tuple[str, ...]] = {}

    for name, persona in EXPLORE_PERSONAS.items():
        session_id = f"persona-{name}"
        chat = _chat(client, session_id, "explore", persona["messages"])
        dimensions = chat["profile"]["dimensions"]
        assert max(dimensions, key=dimensions.get) == persona["dimension"]

        response = client.post("/api/recommendations", json={"session_id": session_id})
        assert response.status_code == 200, response.text
        payload = response.json()
        ids = tuple(item["career_id"] for item in payload["recommendations"])
        assert len(ids) == 5 and len(set(ids)) == 5
        assert set(ids[:3]) & persona["family"], (name, ids)
        assert payload["stretch"]["career_id"] not in ids
        assert payload["stretch"]["is_stretch"] is True
        for item in payload["recommendations"] + [payload["stretch"]]:
            assert item["why"]["from_you"]
            assert all(evidence["quote"] for evidence in item["why"]["from_you"])
            assert len(item["routes"]) >= 2
            assert any(
                route["type"] in {"vocational", "college", "certificate"}
                for route in item["routes"]
            )
        top_ones[name] = ids[0]
        top_threes[name] = ids[:3]

    # Market signal may create an occasional shared first place, but five clearly
    # different profiles must not collapse into the same canned ordering.
    assert len(set(top_ones.values())) >= 4, top_ones
    assert len(set(top_threes.values())) == len(EXPLORE_PERSONAS), top_threes


@pytest.mark.parametrize(
    "name,messages,expected_stage,expected_experience",
    [
        (
            "data-project",
            [
                "Em là sinh viên năm cuối muốn tìm việc dữ liệu entry-level.",
                "Em làm project dashboard bán hàng bằng Excel và SQL.",
                "Output là file dashboard và ba insight em có thể gửi link.",
                "Em muốn tìm việc tại Hà Nội trong 30 ngày tới.",
            ],
            "final_year",
            True,
        ),
        (
            "creative-portfolio",
            [
                "Em mới tốt nghiệp và muốn làm thiết kế entry-level.",
                "Em có project thiết kế poster bằng Figma và Photoshop.",
                "Output là portfolio PDF có ba case study.",
                "Em muốn tìm việc tại Đà Nẵng.",
            ],
            "recent_graduate",
            True,
        ),
        (
            "no-experience",
            [
                "Em mới tốt nghiệp và muốn tìm việc data nhưng chưa rõ vai trò.",
                "Em chưa có project, chưa từng thực tập và chưa biết Python.",
                "Em mới học Excel cơ bản, chưa có output để gửi.",
                "Em có thể dành 30 ngày để xây nền tảng.",
            ],
            "recent_graduate",
            False,
        ),
    ],
)
def test_graduate_launch_personas_preserve_evidence_boundaries(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    messages: list[str],
    expected_stage: str,
    expected_experience: bool,
) -> None:
    _configure_offline(monkeypatch)
    session_id = f"launch-{name}"
    chat = _chat(client, session_id, "launch", messages)
    profile = chat["profile"]
    assert profile["education_stage"] == expected_stage
    assert bool(profile["experiences"]) is expected_experience
    if not expected_experience:
        assert all(skill["name"].lower() != "python" for skill in profile["skills"])

    response = client.post("/api/recommendations", json={"session_id": session_id})
    assert response.status_code == 200
    for item in response.json()["recommendations"]:
        readiness = item["job_readiness"]
        assert readiness is not None
        assert readiness["band"] in {"ready_now", "near_ready", "build_foundation"}
        assert len(readiness["actions_30d"]) == 4
        assert all(action["deliverable"] for action in readiness["actions_30d"])
        if not expected_experience:
            assert all("Python" not in match["evidence"] for match in readiness["matched_skills"])


def test_research_and_what_if_never_mutate_profile_or_reorder_core_result(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _configure_offline(monkeypatch)
    session_id = "persona-research-what-if"
    _chat(client, session_id, "explore", EXPLORE_PERSONAS["analytical"]["messages"])
    before_profile = deepcopy(client.get(f"/api/profile/{session_id}").json()["profile"])
    original = client.post("/api/recommendations", json={"session_id": session_id}).json()
    original_ids = [item["career_id"] for item in original["recommendations"]]

    research = client.post(
        "/api/research/careers",
        json={
            "session_id": session_id,
            "career_ids": original_ids[:2],
            "intent": "local_market",
            "region": "hcm",
        },
    )
    assert research.status_code == 200
    assert research.json()["status"] in {"replay", "cached", "unavailable", "live"}

    preview = client.post(
        "/api/recommendations/what-if",
        json={"session_id": session_id, "skill": "Power BI"},
    )
    assert preview.status_code == 200
    assert preview.json()["original_profile_unchanged"] is True

    after_profile = client.get(f"/api/profile/{session_id}").json()["profile"]
    after_ids = [
        item["career_id"]
        for item in client.post("/api/recommendations", json={"session_id": session_id}).json()["recommendations"]
    ]
    assert after_profile == before_profile
    assert after_ids == original_ids
