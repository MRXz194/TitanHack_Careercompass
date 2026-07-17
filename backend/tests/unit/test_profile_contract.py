import pytest

from app.models.schemas import Profile


pytestmark = pytest.mark.unit


def test_profile_does_not_accept_or_expose_gender() -> None:
    profile = Profile(session_id="unit-profile", gender="female")

    assert "gender" not in Profile.model_fields
    assert "gender" not in profile.model_dump()


def test_opening_profile_has_no_unsupported_inference() -> None:
    profile = Profile(session_id="unit-opening", journey_mode="launch")

    assert profile.education_stage is None
    assert profile.job_goal is None
    assert profile.skills == []
    assert profile.interests == []
    assert profile.experiences == []
    assert profile.completeness == 0.0
    assert all(value == 0.0 for value in profile.dimensions.values())


def test_profile_collection_defaults_are_isolated() -> None:
    first = Profile(session_id="first")
    second = Profile(session_id="second")

    first.interests.append("dữ liệu")

    assert second.interests == []

