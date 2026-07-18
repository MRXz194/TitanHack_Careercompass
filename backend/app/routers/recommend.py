"""Recommendation endpoint — PR-05 wires real matching; evidence templates (PR-06 polish)."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.models.schemas import Profile, RecommendationResponse, WhatIfRequest, WhatIfResponse
from app.services import matching, session_store, what_if

router = APIRouter(prefix="/api", tags=["recommendations"])

DISCLAIMER = (
    "Đây là gợi ý tham khảo dựa trên hồ sơ của em và dữ liệu thị trường — quyết định là của em."
)


def _has_personal_signal(profile: Profile) -> bool:
    """Never label a market-only ordering as personalized for a blank profile."""
    return bool(
        profile.skills
        or profile.interests
        or profile.experiences
        or profile.job_goal
        or max(profile.dimensions.values(), default=0.0) >= 0.3
    )


@router.post("/recommendations", response_model=RecommendationResponse)
def recommendations(body: dict) -> RecommendationResponse:
    session_id = (body or {}).get("session_id")
    if not session_id or not isinstance(session_id, str):
        raise HTTPException(422, detail="session_id required")

    state = session_store.get_session(session_id)
    if state is None:
        raise HTTPException(404, detail="session not found; complete profiling first")
    profile = state.profile
    if not _has_personal_signal(profile):
        raise HTTPException(
            409,
            detail="profile has insufficient personal evidence; continue profiling first",
        )

    try:
        top5, stretch = matching.recommend(profile)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, detail="recommendation failed") from exc

    return RecommendationResponse(
        generated_at=datetime.now(timezone.utc).isoformat(),
        disclaimer=DISCLAIMER,
        recommendations=top5,
        stretch=stretch,
    )


@router.post("/recommendations/what-if", response_model=WhatIfResponse)
def preview_what_if(body: WhatIfRequest) -> WhatIfResponse:
    state = session_store.get_session(body.session_id)
    if state is None:
        raise HTTPException(404, detail="session not found; complete profiling first")
    try:
        return what_if.preview_added_skill(state.profile, body.skill)
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc
