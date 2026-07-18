"""Recommendation endpoint — PR-05 wires real matching; evidence templates (PR-06 polish)."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.models.schemas import RecommendationResponse
from app.services import matching, session_store

router = APIRouter(prefix="/api", tags=["recommendations"])

DISCLAIMER = (
    "Đây là gợi ý tham khảo dựa trên hồ sơ của em và dữ liệu thị trường — quyết định là của em."
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
