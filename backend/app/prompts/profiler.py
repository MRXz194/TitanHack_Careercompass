# v0 — 2026-07-17 — initial skeleton (PR-02 fills in and iterates here, keep version comments)
"""System prompts for the conversational profiler. Design: docs/AI_DESIGN.md §1.

HARD RULES baked into every prompt version:
- Never ask about or infer gender; if the student mentions it, do not store it,
  and respond by widening options, not confirming stereotypes.
- One question per turn, ≤3 sentences, warm Vietnamese ("mình"/"bạn"), no jargon.
- Output ONLY JSON: {"reply": str, "profile_delta": {...}, "phase_done": bool}.
"""

PROFILER_SYSTEM = """(PR-02: viết prompt thật ở đây theo AI_DESIGN.md §1)"""

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
