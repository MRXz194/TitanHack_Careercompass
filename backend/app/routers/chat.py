"""Chat profiling endpoints — wired to profiler service (PR-03)."""
from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse, ProfilePatch
from app.services import profiler

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    return profiler.handle_turn(req.session_id, req.message, req.journey_mode)


@router.get("/profile/{session_id}")
def get_profile(session_id: str) -> dict:
    try:
        profile = profiler.get_profile(session_id)
    except KeyError:
        raise HTTPException(404, detail="session not found") from None
    return {"profile": profile.model_dump()}


@router.patch("/profile/{session_id}")
def patch_profile(session_id: str, patch: ProfilePatch) -> dict:
    try:
        profile = profiler.patch_profile(session_id, patch)
    except KeyError:
        raise HTTPException(404, detail="session not found") from None
    return {"profile": profile.model_dump()}


@router.delete("/profile/{session_id}")
def delete_profile(session_id: str) -> dict:
    """Additive endpoint — clear session for privacy (SECURITY_PRIVACY)."""
    if not profiler.delete_session(session_id):
        raise HTTPException(404, detail="session not found")
    return {"ok": True}
