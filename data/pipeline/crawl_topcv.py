"""[Bước 1] Crawler TopCV — task D-02. Đọc docs/DATA_PIPELINE.md §[1] trước khi code.

Output: data/raw/topcv_<YYYYMMDD>.jsonl — MỌI crawler phải ra đúng RAW SCHEMA
(xem DATA_PIPELINE.md). Crawler nguồn #2 (D-03) copy file này đổi phần parse.

Rules bắt buộc:
- delay 1–2s giữa các request, User-Agent thật, KHÔNG chạy song song 1 domain
- resume được: id đã có trong file output → skip
- gặp 403/429 → dừng, in cảnh báo, KHÔNG retry dồn dập
"""
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

OUT = Path(__file__).resolve().parents[1] / "raw" / f"topcv_{datetime.now():%Y%m%d}.jsonl"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# D-01: điền danh mục ngành × vùng cần crawl (cả nghề phổ thông, không chỉ IT!)
CATEGORIES: list[str] = []  # TODO D-01: URL/slug danh mục
REGIONS: list[str] = []     # TODO D-01: slug vùng (HN/HCM/ĐN)


def load_seen_ids() -> set[str]:
    if not OUT.exists():
        return set()
    return {json.loads(line)["id"] for line in OUT.open(encoding="utf-8")}


def save(posting: dict) -> None:
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(posting, ensure_ascii=False) + "\n")


def main() -> None:
    seen = load_seen_ids()
    print(f"resume: {len(seen)} postings đã có")
    # TODO D-02:
    # for category, region: phân trang danh sách job
    #   → parse từng posting đúng RAW SCHEMA (id, source, url, title, company,
    #     region_raw, salary_raw, posted_date_raw, description, crawled_at)
    #   → if id in seen: continue
    #   → save(posting); time.sleep(random.uniform(1, 2))
    raise NotImplementedError("Task D-02 — xem docstring và docs/DATA_PIPELINE.md")


if __name__ == "__main__":
    main()
