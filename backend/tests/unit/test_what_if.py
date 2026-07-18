from __future__ import annotations

import pytest

from app.models.schemas import Profile, ProfileSkill
from app.services.what_if import preview_added_skill


pytestmark = pytest.mark.unit


def test_what_if_does_not_mutate_original_profile() -> None:
    profile = Profile(
        session_id="what-if",
        skills=[ProfileSkill(name="Excel", source_quote="project dashboard")],
        interests=["dữ liệu"],
    )
    before = profile.model_dump_json()
    response = preview_added_skill(profile, "SQL")
    assert profile.model_dump_json() == before
    assert response.original_profile_unchanged is True
    assert response.preview.recommendations
    assert "mô phỏng" in response.disclaimer.lower()


def test_what_if_rejects_prohibited_attribute() -> None:
    with pytest.raises(ValueError):
        preview_added_skill(Profile(session_id="x"), "GPA 3.8")
