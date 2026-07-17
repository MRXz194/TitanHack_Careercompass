# 🔄 DATA PIPELINE — Crawl → Normalize → Extract → Stats

> Người đọc chính: M2 (bước 1–2), M3 (bước 3–5). Mỗi bước là 1 script độc lập, đọc file của bước trước — chạy lại từng bước được, không bước nào phụ thuộc "state trong đầu" của bước khác.

## Sơ đồ

```
[1] crawl_*.py        → data/raw/{source}_{date}.jsonl          (M2)
[2] normalize.py      → data/processed/postings.jsonl           (M2)
[3] extract_skills.py → data/processed/postings_enriched.jsonl  (M3)
[4] build_market_stats.py → backend/market.db (SQLite)          (M3)
[5] embed_careers.py  → data/processed/careers.npy + ids.json   (M3)
```

Chạy toàn pipeline: theo thứ tự 1→5. Chỉ đổi taxonomy: chạy lại từ 3. Chỉ thêm nghề vào KB: chạy lại 5 (và 4 nếu đổi mapping).

## [1] Source go/no-go + Crawl (M2)

Trước khi viết selector: ghi URL robots/terms/license và quyết định `allowed | unclear | blocked` vào Notes. Chỉ crawl nguồn `allowed`; `unclear` phải được M1 duyệt và có phương án dataset mở. Không bypass login, CAPTCHA hoặc access control; không thu dữ liệu ứng viên/cá nhân.

**Nguồn ưu tiên:** TopCV (nhiều posting đại trà + nghề phổ thông) → VietnamWorks (văn phòng, có lương nhiều hơn) → ITviec/CareerViet (dự phòng). Mục tiêu: **≥3.000 postings, ≥2 nguồn, mỗi vùng HN/HCM/ĐN ≥15%**. Cần cả nghề phổ thông/kỹ thuật (điện lạnh, cơ khí, bếp, làm đẹp, logistics) chứ không chỉ IT — sản phẩm hướng nghiệp cho MỌI học sinh.

**Schema output raw (JSONL — 1 posting/dòng, MỌI crawler phải ra đúng schema này):**
```json
{
  "id": "topcv_123456",
  "source": "topcv",
  "url": "https://...",
  "title": "Nhân viên kỹ thuật điện lạnh",
  "company": "Công ty ABC",
  "region_raw": "Đà Nẵng",
  "salary_raw": "9 - 15 triệu",
  "experience_raw": "Không yêu cầu kinh nghiệm",
  "posted_date_raw": "Đăng 3 ngày trước",
  "description": "toàn bộ text mô tả + yêu cầu công việc",
  "crawled_at": "2026-07-17T20:00:00+07:00"
}
```

**Rules:**
- Delay 1–2s/request, User-Agent thật, không crawl song song 1 domain. Bị 403/429 → dừng nguồn đó 15', đổi nguồn.
- Crawl theo (danh mục ngành × vùng), phân trang đến hết hoặc đủ quota.
- Script resume được: đã có `id` trong file raw → skip.
- **Plan B (M1 kích hoạt tại H+10 nếu tổng < 1k):** dataset Kaggle "Vietnam job posting" + crawl bổ sung nguồn dễ nhất; các bước sau không đổi vì schema raw không đổi.
- Mỗi snapshot có `manifest.json`: nguồn/license/terms URL, crawled_at, count, hash và caveat. UI chỉ hiện aggregate + attribution, không republish toàn bộ mô tả.

## [2] Normalize (M2)

Input `data/raw/*.jsonl` → Output `data/processed/postings.jsonl`:

| Trường | Xử lý |
|---|---|
| `salary_min/max_trieu` | parse range; ngoại tệ dùng `exchange_rate` cấu hình kèm source/date trong manifest, không hardcode “tỉ giá hiện tại” |
| `experience_min_years` | “không yêu cầu/fresher”→0; “1–2 năm”→1; không rõ→null; không suy ra từ tuổi |
| `seniority` | `entry|mid|senior|unknown` từ title + experience; dùng rule deterministic, lưu confidence/reason để QA |
| `region` | map `region_raw` → `hanoi/hcm/danang/other` (bảng map trong script; "Hồ Chí Minh", "TP HCM", "Thủ Đức"→hcm...) |
| `posted_date` | "Đăng 3 ngày trước" → date tuyệt đối (từ `crawled_at`); parse các format dd/mm/yyyy |
| dedupe | fuzzy: normalize(title)+normalize(company) trùng trong cửa sổ 30 ngày → giữ bản mới nhất |
| lọc rác | description < 100 ký tự, title toàn ký tự lạ → bỏ, đếm vào report |

Cuối script in report: tổng in/out, % có lương/experience, phân bố vùng/ngày/seniority, drop/dedupe. **Report này paste vào PR** — là bằng chứng chất lượng data khi pitch và là guardrail cho Launch mode.

## [3] Extract skills (M3) — thiết kế chi tiết ở [AI_DESIGN.md §2](AI_DESIGN.md)

Thêm vào mỗi posting: `skills: string[]` (tên chuẩn trong taxonomy), `career_id: string | "unmapped"`.
Bắt buộc: cache LLM theo hash, resume được, log chi phí ước tính ra console.

## [4] Market stats (M3) — công thức ở [AI_DESIGN.md §3](AI_DESIGN.md)

Ghi vào `backend/market.db` các bảng:
- `career_stats(career_id, region, demand_count, entry_level_count, salary_p25, salary_p50, salary_p75, trend_pct, low_confidence, top_skills_json, updated_at)`
- `skill_stats(skill, region, demand_count, trend_pct, gap_score, related_careers_json)`
- `meta(postings_count, window_days, built_at, sources_json)` — FE hiện "từ N tin tuyển dụng" lấy ở đây.

## [5] Embed careers (M3)

Mỗi career trong `data/seed/careers_seed.json`: text = `title + description + top skills từ stats` → OpenAI `text-embedding-3-small` → `careers.npy` (row i) + `career_ids.json` (thứ tự). Loader trong `backend/app/services/matching.py`.

## Career KB — `data/seed/careers_seed.json` (M2+M4 mở rộng ở D-07)

File này **commit vào repo**. Mỗi career cần canonical title, `title_patterns`, `entry_role_aliases`, description, top skills, routes và roadmap/action templates. P0 ≥25 nghề cân bằng university/vocational, IT/phi-IT và có alias entry-level; P2 mới mở rộng 40–60.
