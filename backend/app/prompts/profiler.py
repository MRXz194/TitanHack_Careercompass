# v1 — 2026-07-17 — Explore/Graduate Launch skeleton; PR-02 iterates with eval evidence
"""System prompts for the conversational profiler. Design: docs/AI_DESIGN.md §1.

HARD RULES baked into every prompt version:
- Never ask about or infer gender; if the student mentions it, do not store it,
  and respond by widening options, not confirming stereotypes.
- One question per turn, ≤3 sentences, warm Vietnamese ("mình"/"bạn"), no jargon.
- Output ONLY JSON: {"reply": str, "profile_delta": {...}, "phase_done": bool}.
- Explore and Launch share tone/schema; mode changes questions/completeness only.
- A school name, GPA or degree title is not proof of a skill. Launch skill evidence
  must come from a described project, internship, work, volunteer or coursework action.
"""

PROFILER_SYSTEM = """(PR-02: implement versioned shared rules + mode section per AI_DESIGN.md §1)"""

# Deterministic fallback questions per phase — used when LLM structured output
# fails after retries. The conversation must NEVER die in front of a judge.
FALLBACK_QUESTIONS = {
    "warmup": ["Bạn đang học lớp mấy, và điều gì khiến bạn nghĩ đến chuyện chọn nghề lúc này?"],
    "interests": ["Kể mình nghe một việc bạn làm mà quên cả thời gian?",
                  "Cuối tuần rảnh, bạn thường tự chọn làm gì?"],
    "abilities": ["Bạn bè hay thầy cô thường khen bạn làm tốt việc gì?",
                  "Môn nào bạn học thấy nhẹ nhàng hơn các bạn?"],
    "constraints": ["Về việc học sau này, gia đình bạn có mong muốn hay điều kiện gì không?"],
    "wrapup": ["Bạn xem hồ sơ bên cạnh có đúng là bạn không? Muốn sửa gì cứ bấm vào nhé."],
}

LAUNCH_FALLBACK_QUESTIONS = {
    "warmup": ["Bạn đang ở giai đoạn nào và muốn bắt đầu tìm loại công việc gì, dù mới chỉ là ý tưởng ban đầu?"],
    "interests": ["Trong các project, môn học, việc làm thêm hoặc hoạt động từng làm, việc nào khiến bạn thấy muốn làm tiếp?"],
    "abilities": ["Chọn một project gần đây nhé: bạn đã trực tiếp làm phần nào và dùng công cụ hay kỹ năng gì?"],
    "constraints": ["Bạn muốn tìm việc ở khu vực hoặc trong khoảng thời gian nào? Chia sẻ được đến đâu hay đến đó nhé."],
    "wrapup": ["Bạn xem lại kỹ năng và trải nghiệm bên cạnh nhé — chỗ nào chưa đúng, bạn có thể sửa trước khi xem nhóm việc phù hợp."],
}
