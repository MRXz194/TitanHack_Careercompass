"""Chat profiling endpoints.

STATUS: STUB (task PR-03 replaces the mock logic with the real profiler service).
The mock walks through phases with canned questions and fake profile growth so
FE (F1-02..05) can integrate against the exact contract shape from hour 1.
"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import (ChatRequest, ChatResponse, ExperienceEvidence, JourneyMode,
                                Profile, ProfilePatch, ProfileSkill)

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

_MOCK_LAUNCH_SCRIPT = [
    ("warmup", "Bạn đang ở giai đoạn nào và muốn bắt đầu tìm loại công việc gì, dù mới chỉ là ý tưởng ban đầu?"),
    ("interests", "Trong project, môn học, việc làm thêm hoặc hoạt động từng làm, việc nào khiến bạn muốn làm tiếp?"),
    ("abilities", "Với project đó, bạn đã trực tiếp làm phần nào và dùng công cụ gì?"),
    ("abilities", "Có output nào bạn có thể đưa cho người khác xem hoặc kiểm tra không?"),
    ("constraints", "Bạn muốn tìm việc ở khu vực hoặc trong khoảng thời gian nào?"),
    ("wrapup", "Bạn xem lại kỹ năng và trải nghiệm bên cạnh nhé — chỗ nào chưa đúng, hãy sửa trước khi xem nhóm việc phù hợp."),
]


def _mock_profile(session_id: str, turn: int, journey_mode: JourneyMode = "explore") -> Profile:
    script_length = len(_MOCK_LAUNCH_SCRIPT) if journey_mode == "launch" else len(_MOCK_SCRIPT)
    growth = min(turn / script_length, 1.0)
    p = Profile(session_id=session_id, journey_mode=journey_mode, completeness=round(growth, 2))
    if journey_mode == "launch":
        p.education_stage = "final_year"
        p.job_goal = "tìm vai trò dữ liệu entry-level"
        p.dimensions = {"ky_thuat": round(0.2 * growth, 2), "phan_tich": round(0.8 * growth, 2),
                        "sang_tao": round(0.4 * growth, 2), "xa_hoi": round(0.3 * growth, 2),
                        "quan_ly": round(0.4 * growth, 2)}
    else:
        p.education_stage = "high_school"
        p.dimensions = {"ky_thuat": round(0.7 * growth, 2), "phan_tich": round(0.4 * growth, 2),
                        "sang_tao": round(0.8 * growth, 2), "xa_hoi": round(0.3 * growth, 2),
                        "quan_ly": round(0.2 * growth, 2)}
    if turn >= 2:
        p.interests = ["phân tích dữ liệu"] if journey_mode == "launch" else ["vẽ", "sửa chữa đồ điện"][: max(1, turn - 1)]
    if turn >= 4:
        p.skills = ([ProfileSkill(name="Excel", level="đã dùng trong project", source_quote="(mock) em đã làm dashboard bằng Excel")]
                    if journey_mode == "launch" else
                    [ProfileSkill(name="vẽ tay", level="tự đánh giá khá", source_quote="(mock) em thích vẽ")])
        if journey_mode == "launch":
            p.experiences = [ExperienceEvidence(
                title="Dashboard bán hàng", kind="project", description="Dashboard từ dữ liệu mở",
                skills=["Excel"], source_quote="(mock) em đã làm dashboard bán hàng bằng Excel",
            )]
    return p


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    state = _sessions.setdefault(req.session_id, {"turn": 0, "journey_mode": req.journey_mode})
    script = _MOCK_LAUNCH_SCRIPT if state["journey_mode"] == "launch" else _MOCK_SCRIPT
    turn = state["turn"] = min(state["turn"] + 1, len(script))
    phase, reply = script[turn - 1]
    return ChatResponse(reply=reply, phase=phase, turn=turn,
                        done=turn >= len(script),
                        profile=_mock_profile(req.session_id, turn, state["journey_mode"]))


@router.get("/profile/{session_id}")
def get_profile(session_id: str) -> dict:
    if session_id not in _sessions:
        raise HTTPException(404, detail="session not found")
    state = _sessions[session_id]
    return {"profile": _mock_profile(session_id, state["turn"], state["journey_mode"]).model_dump()}


@router.patch("/profile/{session_id}")
def patch_profile(session_id: str, patch: ProfilePatch) -> dict:
    # STUB: PR-03/F1-04 — apply patch to stored profile. For now echo current.
    if session_id not in _sessions:
        raise HTTPException(404, detail="session not found")
    state = _sessions[session_id]
    profile = _mock_profile(session_id, state["turn"], state["journey_mode"])
    profile.dimensions.update(patch.dimensions)
    if "education_stage" in patch.model_fields_set:
        profile.education_stage = patch.education_stage
    if "job_goal" in patch.model_fields_set:
        profile.job_goal = patch.job_goal
    remove_titles = set(patch.remove_experience_titles)
    profile.experiences = [e for e in profile.experiences if e.title not in remove_titles]
    profile.experiences.extend(patch.add_experiences)
    return {"profile": profile.model_dump()}
