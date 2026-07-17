import pytest

from app.models.profiler_io import ProfileDelta, ProfilerTurnOutput


pytestmark = pytest.mark.unit

FORBIDDEN = {
    "gender",
    "sex",
    "name",
    "full_name",
    "school",
    "school_name",
    "school_prestige",
    "gpa",
    "email",
    "phone",
}


def test_profiler_io_has_no_forbidden_fields() -> None:
    assert FORBIDDEN.isdisjoint(ProfileDelta.model_fields)
    assert FORBIDDEN.isdisjoint(ProfilerTurnOutput.model_fields)


def test_profiler_turn_output_parses_example() -> None:
    raw = {
        "reply": "Bạn thích nhất phần nào khi sửa đồ điện?",
        "profile_delta": {
            "interests": ["sửa chữa đồ điện"],
            "dimensions": {"ky_thuat": 0.6},
            "skills": [],
            "evidence_quotes": [
                {"turn": 2, "quote": "em hay sửa quạt", "mapped_to": "ky_thuat"}
            ],
        },
        "phase_done": False,
    }
    out = ProfilerTurnOutput.model_validate(raw)
    assert "sửa chữa" in out.reply or "?" in out.reply
    assert out.profile_delta.interests == ["sửa chữa đồ điện"]
    assert out.profile_delta.dimensions["ky_thuat"] == 0.6
    assert out.phase_done is False


def test_profile_delta_ignores_forbidden_extras() -> None:
    delta = ProfileDelta.model_validate(
        {
            "interests": ["vẽ"],
            "gender": "female",
            "school_prestige": "top",
            "gpa": 3.9,
            "name": "An",
        }
    )
    dumped = delta.model_dump()
    for key in FORBIDDEN:
        assert key not in dumped
    assert delta.interests == ["vẽ"]


def test_profiler_turn_defaults_isolated() -> None:
    a = ProfilerTurnOutput(reply="a?")
    b = ProfilerTurnOutput(reply="b?")
    a.profile_delta.interests.append("x")
    assert b.profile_delta.interests == []


def test_launch_delta_with_experience() -> None:
    out = ProfilerTurnOutput.model_validate(
        {
            "reply": "Bạn dùng Excel phần nào trong dashboard đó?",
            "profile_delta": {
                "education_stage": "final_year",
                "job_goal": "data entry-level",
                "experiences": [
                    {
                        "title": "Dashboard bán hàng",
                        "kind": "project",
                        "description": "dashboard từ dữ liệu mở",
                        "skills": ["Excel"],
                        "source_quote": "em làm dashboard bằng Excel",
                    }
                ],
                "skills": [
                    {
                        "name": "Excel",
                        "level": "đã dùng trong project",
                        "source_quote": "em làm dashboard bằng Excel",
                    }
                ],
            },
            "phase_done": True,
        }
    )
    assert out.profile_delta.education_stage == "final_year"
    assert out.profile_delta.experiences[0].kind == "project"
    assert out.phase_done is True
