"""[Bước 3] Extract skills + map career — tasks MI-02/MI-03. Thiết kế: docs/AI_DESIGN.md §2.

Input:  data/processed/postings.jsonl + data/taxonomy/skills_vi.json + careers_seed.json
Output: data/processed/postings_enriched.jsonl (thêm skills[], career_id)

Kiến trúc hybrid 2 tầng (làm ĐÚNG thứ tự này):
  Tầng 1 — dictionary match (0 đồng, vài giây): match aliases trên title+description
           (lowercase + unicode NFC normalize trước khi match)
  Tầng 2 — LLM catch-up: CHỈ posting có < 3 skills sau tầng 1, batch 10 postings/call,
           trả thêm new_skills (ngoài taxonomy) để M3 duyệt bổ sung taxonomy

Bắt buộc:
- cache LLM theo hash(posting_id + taxonomy_version) vào backend/.cache/ — chạy lại không tốn tiền
- resume được khi đứt giữa chừng
- log chi phí ước tính ra console
- map career: rule theo title_patterns trong careers_seed.json, fallback LLM;
  không map được → career_id="unmapped" (nhóm unmapped ≥50 postings → báo D-07 thêm nghề)
"""


def main() -> None:
    raise NotImplementedError("Tasks MI-02 (prototype 50 postings) rồi MI-03 (toàn dataset)")


if __name__ == "__main__":
    main()
