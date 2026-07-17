import pytest

from app.main import app
from app.models.schemas import ChatResponse, Profile, RecommendationResponse


pytestmark = pytest.mark.contract


def test_core_response_models_keep_expected_top_level_fields() -> None:
    assert set(ChatResponse.model_fields) == {"reply", "phase", "turn", "done", "profile"}
    assert set(RecommendationResponse.model_fields) == {
        "generated_at",
        "disclaimer",
        "recommendations",
        "stretch",
    }


def test_openapi_profile_matches_ethics_boundary() -> None:
    schemas = app.openapi()["components"]["schemas"]
    profile_schemas = [
        schema for name, schema in schemas.items()
        if name == "Profile" or name.startswith("Profile-")
    ]

    assert profile_schemas
    for profile_schema in profile_schemas:
        assert "gender" not in profile_schema["properties"]
        assert set(profile_schema["properties"]) == set(Profile.model_fields)

