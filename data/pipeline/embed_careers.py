"""[Bước 5] Embed careers — task MI-06.

Mỗi career trong careers_seed.json: text = title + description + top_skills (từ stats nếu có)
→ gọi embed() trong backend/app/services/llm.py (KHÔNG gọi SDK trực tiếp ở đây)
→ lưu data/processed/careers.npy (row i) + data/processed/career_ids.json (thứ tự).

Loader + hàm top_k_careers(profile_text) đặt ở backend/app/services/matching.py (MI-06/PR-05).
"""


def main() -> None:
    raise NotImplementedError("Task MI-06")


if __name__ == "__main__":
    main()
