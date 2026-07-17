"""[Bước 4] Market stats — task MI-04/MI-05. Công thức: docs/AI_DESIGN.md §3.

Input:  data/processed/postings_enriched.jsonl
Output: backend/market.db (SQLite) — 3 bảng:
  career_stats(career_id, region, demand_count, salary_p25, salary_p50, salary_p75,
               trend_pct, low_confidence, top_skills_json, updated_at)
  skill_stats(skill, region, demand_count, trend_pct, gap_score, related_careers_json)
  meta(postings_count, window_days, built_at, sources_json)

Guard bắt buộc (MI-08):
- < 5 mẫu lương → salary_* = NULL (không bịa số!)
- < 10 postings → low_confidence = 1
- trend_pct mẫu số dùng max(count_45d_đầu, 5) để tránh ±1000%
Sau khi chạy: đổi routers/market.py từ seed sang đọc market.db (giữ nguyên response shape).
"""


def main() -> None:
    raise NotImplementedError("Task MI-04 — xem docstring")


if __name__ == "__main__":
    main()
