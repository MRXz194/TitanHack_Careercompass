import pytest

from app.main import app
from app.models.schemas import (
    ChatResponse,
    Profile,
    ProfilePatch,
    Recommendation,
    RecommendationResponse,
)


pytestmark = pytest.mark.contract

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


def test_core_response_models_keep_expected_top_level_fields() -> None:
    assert set(ChatResponse.model_fields) == {"reply", "phase", "turn", "done", "profile"}
    assert set(RecommendationResponse.model_fields) == {
        "generated_at",
        "disclaimer",
        "recommendations",
        "stretch",
    }
    assert "job_readiness" in Recommendation.model_fields


def test_openapi_profile_matches_ethics_boundary() -> None:
    schemas = app.openapi()["components"]["schemas"]
    profile_schemas = [
        schema
        for name, schema in schemas.items()
        if name == "Profile" or name.startswith("Profile-")
    ]

    assert profile_schemas
    for profile_schema in profile_schemas:
        props = set(profile_schema.get("properties", {}))
        assert props == set(Profile.model_fields)
        assert FORBIDDEN.isdisjoint(props)


def test_openapi_profile_patch_has_no_forbidden_fields() -> None:
    schemas = app.openapi()["components"]["schemas"]
    patch_schemas = [
        schema
        for name, schema in schemas.items()
        if name == "ProfilePatch" or name.startswith("ProfilePatch-")
    ]
    assert patch_schemas
    for schema in patch_schemas:
        props = set(schema.get("properties", {}))
        assert props == set(ProfilePatch.model_fields)
        assert FORBIDDEN.isdisjoint(props)
