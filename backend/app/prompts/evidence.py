# v1 — 2026-07-17 — grounded evidence verbalization (PR-06)
"""Prompts for evidence wording. Numbers MUST come only from provided stats.

Code validates every digit after generation; failure → template fallback.
"""

EVIDENCE_PROMPT_VERSION = "evidence-v1"

EVIDENCE_SYSTEM = """
Bạn viết lời giải thích ngắn (tiếng Việt, thân thiện "mình/bạn") cho gợi ý nghề.

CẤM TUYỆT ĐỐI:
- Bịa số mới (lương, số tin tuyển, %). Chỉ dùng đúng các số trong `allowed_stats`.
- Bịa trích dẫn. Chỉ dùng đúng `allowed_quotes`.
- Hứa đỗ việc, phán quyết "nghề tốt nhất", gợi ý theo giới tính.

Output JSON thuần:
{
  "from_you": [{"quote": "...", "reason": "..."}],
  "from_market": [{"stat": "...", "stat_key": "demand_count|salary|trend|entry_level"}],
  "counterfactual": "..."
}
- from_you: 1–2 mục; quote ∈ allowed_quotes
- from_market: 1–2 mục; mọi chữ số trong stat phải nằm trong allowed_stats
- counterfactual: diễn đạt lại `counterfactual_fact` (đã tính bằng code), không đổi tên nghề/số
""".strip()


def build_evidence_user_payload(
    *,
    career_title: str,
    allowed_quotes: list[str],
    allowed_stats: dict,
    counterfactual_fact: str,
) -> str:
    import json

    return json.dumps(
        {
            "career_title": career_title,
            "allowed_quotes": allowed_quotes,
            "allowed_stats": allowed_stats,
            "counterfactual_fact": counterfactual_fact,
        },
        ensure_ascii=False,
    )
