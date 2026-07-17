"""[Bước 2] Normalize — task D-04. Spec đầy đủ: docs/DATA_PIPELINE.md §[2].

Input:  data/raw/*.jsonl (mọi nguồn, chung raw schema)
Output: data/processed/postings.jsonl + report in ra console (paste vào PR!)

Việc chính:
- parse salary_raw → salary_min_trieu / salary_max_trieu (triệu VND; "Thỏa thuận" → null)
- map region_raw → hanoi | hcm | danang | other
- posted_date_raw → posted_date (ISO, tuyệt đối, tính từ crawled_at nếu dạng "3 ngày trước")
- dedupe fuzzy (title+company, cửa sổ 30 ngày, dùng rapidfuzz) — giữ bản mới nhất
- lọc rác (description < 100 ký tự)

⚠️ Phải có unit test cho parse salary + map region (TEAM_RULES.md §4) — sai ở đây
là mọi con số trên UI sai âm thầm.
"""

REGION_MAP = {
    # TODO D-04: mở rộng bảng này khi gặp biến thể mới trong dữ liệu thật
    "hà nội": "hanoi", "ha noi": "hanoi", "hanoi": "hanoi",
    "hồ chí minh": "hcm", "tp hcm": "hcm", "tp. hcm": "hcm", "hcm": "hcm", "thủ đức": "hcm",
    "đà nẵng": "danang", "da nang": "danang",
}


def parse_salary(salary_raw: str) -> tuple[float | None, float | None]:
    """'9 - 15 triệu' → (9, 15) · 'Đến 20 triệu' → (None, 20) · 'Thỏa thuận' → (None, None)
    '$800-1200' → quy đổi 25.5k VND/USD rồi /1e6, làm tròn 1 số lẻ."""
    raise NotImplementedError("Task D-04")


def main() -> None:
    raise NotImplementedError("Task D-04 — xem docstring")


if __name__ == "__main__":
    main()
