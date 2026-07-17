import pytest
from pydantic import ValidationError

from app.models.schemas import ChatRequest, ExperienceEvidence, Profile, ProfilePatch


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

PROFILE_FIELDS = {
    "session_id",
    "journey_mode",
    "education_stage",
    "job_goal",
    "dimensions",
    "skills",
    "interests",
    "constraints",
    "evidence_quotes",
    "experiences",
    "completeness",
}

PATCH_FIELDS = {
    "dimensions",
    "remove_skills",
    "add_interests",
    "education_stage",
    "job_goal",
    "add_experiences",
    "remove_experience_titles",
}

DIMENSION_KEYS = {"ky_thuat", "phan_tich", "sang_tao", "xa_hoi", "quan_ly"}


def test_profile_field_set_matches_frozen_contract() -> None:
    assert set(Profile.model_fields) == PROFILE_FIELDS
    assert FORBIDDEN.isdisjoint(Profile.model_fields)


def test_profile_patch_field_set_matches_frozen_contract() -> None:
    assert set(ProfilePatch.model_fields) == PATCH_FIELDS
    assert FORBIDDEN.isdisjoint(ProfilePatch.model_fields)


def test_profile_does_not_accept_or_expose_gender() -> None:
    profile = Profile(session_id="unit-profile", gender="female")

    assert "gender" not in Profile.model_fields
    assert "gender" not in profile.model_dump()


def test_profile_ignores_other_forbidden_extras() -> None:
    profile = Profile(
        session_id="unit-forbidden",
        school_prestige="top",
        gpa=3.9,
        name="Minh",
        email="x@y.z",
    )
    dumped = profile.model_dump()
    for key in FORBIDDEN:
        assert key not in dumped


def test_opening_profile_has_no_unsupported_inference() -> None:
    profile = Profile(session_id="unit-opening", journey_mode="launch")

    assert profile.education_stage is None
    assert profile.job_goal is None
    assert profile.skills == []
    assert profile.interests == []
    assert profile.experiences == []
    assert profile.completeness == 0.0
    assert set(profile.dimensions) == DIMENSION_KEYS
    assert all(value == 0.0 for value in profile.dimensions.values())


def test_profile_collection_defaults_are_isolated() -> None:
    first = Profile(session_id="first")
    second = Profile(session_id="second")

    first.interests.append("dữ liệu")

    assert second.interests == []


def test_chat_request_defaults_journey_mode_to_explore() -> None:
    req = ChatRequest(session_id="explore-default")
    assert req.journey_mode == "explore"
    assert req.message is None


def test_api_contract_profile_example_parses() -> None:
    """Minimal full example aligned with docs/API_CONTRACT.md Profile schema."""
    example = {
        "session_id": "uuid-example",
        "journey_mode": "explore",
        "education_stage": "high_school",
        "job_goal": None,
        "dimensions": {
            "ky_thuat": 0.7,
            "phan_tich": 0.4,
            "sang_tao": 0.8,
            "xa_hoi": 0.3,
            "quan_ly": 0.2,
        },
        "skills": [
            {
                "name": "vẽ tay",
                "level": "tự đánh giá khá",
                "source_quote": "em thích vẽ",
            }
        ],
        "interests": ["vẽ", "sửa chữa đồ điện"],
        "constraints": {
            "region_pref": "danang",
            "study_budget": "hạn chế",
            "study_duration_pref": "ngắn",
            "notes": "gia đình muốn em học gần nhà",
        },
        "evidence_quotes": [
            {
                "turn": 3,
                "quote": "em hay sửa đồ điện trong nhà",
                "mapped_to": "ky_thuat",
            }
        ],
        "experiences": [],
        "completeness": 0.6,
    }
    profile = Profile.model_validate(example)
    assert profile.journey_mode == "explore"
    assert profile.skills[0].name == "vẽ tay"
    assert profile.constraints.region_pref == "danang"


def test_launch_profile_example_with_experience_parses() -> None:
    example = {
        "session_id": "launch-example",
        "journey_mode": "launch",
        "education_stage": "final_year",
        "job_goal": "tìm vai trò dữ liệu entry-level",
        "dimensions": {
            "ky_thuat": 0.2,
            "phan_tich": 0.8,
            "sang_tao": 0.4,
            "xa_hoi": 0.3,
            "quan_ly": 0.4,
        },
        "skills": [
            {
                "name": "Excel",
                "level": "đã dùng trong project",
                "source_quote": "em đã làm dashboard bán hàng bằng Excel",
            }
        ],
        "interests": ["phân tích dữ liệu"],
        "constraints": {
            "region_pref": "danang",
            "study_budget": None,
            "study_duration_pref": None,
            "notes": "",
        },
        "evidence_quotes": [
            {
                "turn": 2,
                "quote": "em đã làm dashboard bán hàng bằng Excel",
                "mapped_to": "phan_tich",
            }
        ],
        "experiences": [
            {
                "title": "Dashboard bán hàng",
                "kind": "project",
                "description": "dashboard từ dữ liệu mở",
                "skills": ["Excel"],
                "source_quote": "em đã làm dashboard bán hàng bằng Excel",
            }
        ],
        "completeness": 0.7,
    }
    profile = Profile.model_validate(example)
    assert profile.journey_mode == "launch"
    assert profile.experiences[0].kind == "project"


def test_profile_patch_tracks_null_clear_fields() -> None:
    patch = ProfilePatch.model_validate(
        {"education_stage": None, "job_goal": None}
    )
    assert "education_stage" in patch.model_fields_set
    assert "job_goal" in patch.model_fields_set
    assert patch.education_stage is None
    assert patch.job_goal is None


def test_profile_patch_omit_does_not_mark_nullable_fields() -> None:
    patch = ProfilePatch.model_validate({"add_interests": ["thiết kế"]})
    assert "education_stage" not in patch.model_fields_set
    assert "job_goal" not in patch.model_fields_set
    assert patch.add_interests == ["thiết kế"]


def test_experience_kind_rejects_unknown() -> None:
    with pytest.raises(ValidationError):
        ExperienceEvidence(
            title="x",
            kind="not-a-real-kind",  # type: ignore[arg-type]
            source_quote="quote",
        )
