"""Chat profiling endpoints.

STATUS: STUB (task PR-03 replaces the mock logic with the real profiler service).
The mock walks through phases with canned questions and fake profile growth so
FE (F1-02..05) can integrate against the exact contract shape from hour 1.
"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse, Profile, ProfilePatch, ProfileSkill

router = APIRouter(prefix="/api", tags=["chat"])

# In-memory store for the stub. PR-03: move to SQLite session store.
_sessions: dict[str, dict] = {}

_MOCK_SCRIPT = [
    ("warmup", "Chào bạn! Mình là CareerCompass 🧭 Mình sẽ trò chuyện để hiểu bạn hơn — không phải bài kiểm tra đâu. Bạn đang học lớp mấy, và điều gì khiến bạn nghĩ đến chuyện chọn nghề lúc này?"),
    ("interests", "Kể mình nghe một việc bạn từng làm mà quên cả thời gian — học, chơi, hay việc nhà đều được!"),
    ("interests", "Nghe thú vị đó! Trong việc đó, bạn thích nhất khoảnh khắc nào?"),
    ("abilities", "Bạn bè hoặc thầy cô hay khen bạn làm tốt việc gì?"),
    ("abilities", "Có môn học hay hoạt động nào bạn thấy mình học nhanh hơn các bạn không?"),
    ("constraints", "Về chuyện học sau này, gia đình bạn có mong muốn hay điều kiện gì đặc biệt không? (Chia sẻ được đến đâu hay đến đó nhé)"),
    ("wrapup", "Cảm ơn bạn đã chia sẻ! Mình đã phác được hồ sơ bên cạnh — bạn xem thử có đúng là bạn không? Có thể bấm sửa trực tiếp đó. Sẵn sàng xem các hướng đi chưa?"),
]


def _mock_profile(session_id: str, turn: int) -> Profile:
    growth = min(turn / len(_MOCK_SCRIPT), 1.0)
    p = Profile(session_id=session_id, completeness=round(growth, 2))
    p.dimensions = {"ky_thuat": round(0.7 * growth, 2), "phan_tich": round(0.4 * growth, 2),
                    "sang_tao": round(0.8 * growth, 2), "xa_hoi": round(0.3 * growth, 2),
                    "quan_ly": round(0.2 * growth, 2)}
    if turn >= 2:
        p.interests = ["vẽ", "sửa chữa đồ điện"][: max(1, turn - 1)]
    if turn >= 4:
        p.skills = [ProfileSkill(name="vẽ tay", level="tự đánh giá khá", source_quote="(mock) em thích vẽ")]
    return p


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    state = _sessions.setdefault(req.session_id, {"turn": 0})
    turn = state["turn"] = min(state["turn"] + 1, len(_MOCK_SCRIPT))
    phase, reply = _MOCK_SCRIPT[turn - 1]
    return ChatResponse(reply=reply, phase=phase, turn=turn,
                        done=turn >= len(_MOCK_SCRIPT),
                        profile=_mock_profile(req.session_id, turn))


@router.get("/profile/{session_id}")
def get_profile(session_id: str) -> dict:
    if session_id not in _sessions:
        raise HTTPException(404, detail="session not found")
    return {"profile": _mock_profile(session_id, _sessions[session_id]["turn"]).model_dump()}


@router.patch("/profile/{session_id}")
def patch_profile(session_id: str, patch: ProfilePatch) -> dict:
    # STUB: PR-03/F1-04 — apply patch to stored profile. For now echo current.
    if session_id not in _sessions:
        raise HTTPException(404, detail="session not found")
    profile = _mock_profile(session_id, _sessions[session_id]["turn"])
    profile.dimensions.update(patch.dimensions)
    return {"profile": profile.model_dump()}
