# DATA SNAPSHOT CARD — điền tại D-10

> Status: `BUILT`. Dữ liệu snapshot hiring thực tế được xử lý thành công.

| Field | Value |
|---|---|
| Snapshot ID / SHA-256 | `real_jobs_snapshot_20260718` / `c6c1db099370db28c10ccd032ceb173078930349191ccdd09939b70676831dfd` |
| Built at / window | 2026-07-18T02:43:13.736836+00:00 / 90 days |
| Sources + terms/license URLs | TopCV ([dieu-khoan](https://www.topcv.vn/dieu-khoan-bao-mat)), VietnamWorks ([chinh-sach](https://www.vietnamworks.com/chinh-sach-bao-mat)), ITViec ([privacy](https://itviec.com/privacy-policy)) |
| Raw / normalized / enriched count | Raw: 300 | Normalized: 298 | Enriched (has skills[], MI-02 hybrid dict+LLM-fallback): 261/298 (87.6%) |
| Count theo source và region | Nguồn: itviec: 99 (33.2%), topcv: 100 (33.6%), vietnamworks: 99 (33.2%) <br> Vùng: hanoi: 158 (53.0%), hcm: 38 (12.8%), other: 100 (33.6%), danang: 2 (0.7%) |
| Salary coverage | 127/298 (42.6%) |
| Experience/seniority coverage + entry-level count | Exp: 199/298 (66.8%) <br> Seniority: {"entry": 76, "mid": 59, "senior": 86, "unknown": 77} <br> Entry-level: 76 |
| Dedupe/drop rate | Deduped: 2 (0.67%) |
| Skill extraction version | skills_vi_v1.0 |
| Career mapping coverage | 89/298 (29.9%) — title-pattern-only against the 25-career KB (`data/pipeline/map_careers.py --provisional`); bounded LLM fallback not configured (no live API key), so titles outside the KB's `title_patterns` stay unmapped. Unmapped postings are excluded from `career_stats` but counted in `market_meta`. |

## Allowed use và attribution

- Dữ liệu thu thập từ các nguồn công khai: TopCV, VietnamWorks, ITViec.
- Mục đích sử dụng: Phân tích giáo dục hướng nghiệp trong khuôn khổ Hackathon. Không kinh doanh, không xuất bản lại mô tả công việc (job descriptions) chi tiết của nhà tuyển dụng.
- Ghi nhận nguồn gốc trên giao diện: Tất cả số liệu hiển thị đi kèm chú thích nguồn gốc tương ứng.

## Known limitations

- Posting count không bằng vacancy count (một tin có thể tuyển nhiều người hoặc đã đóng).
- Nguồn/region coverage không đại diện hoàn bộ thị trường Việt Nam (phần lớn tập trung ở Hà Nội/HCM, thiếu các tỉnh lẻ).
- Salary chỉ phản ánh tin có công khai lương (hơn 50% tin ghi Thỏa thuận).
- Trend chỉ có ý nghĩa khi đủ cửa sổ thời gian và số lượng mẫu lớn hơn — dataset hiện tại gần như 1 lần crawl duy nhất (posted_date cụm quanh 2026-07-17), nên `build_market_stats.py` đúng thiết kế trả `trend_pct = NULL` cho mọi career/skill (`career_stats`/`skill_stats` đã build, `/api/market/*` wired với fallback seed khi thiếu dữ liệu vùng).
- **2 bản vá dữ liệu đã áp dụng trước khi build** (không sửa nội dung tin tuyển, chỉ sửa lỗi ID/ngày parse):
  1. Trùng `id` (`itviec_5804` xuất hiện 2 lần cho 2 tin khác nhau — crawler lấy số cuối URL làm ID, bị trùng ngẫu nhiên) → đổi ID bản ghi thứ 2 thành `itviec_5804-dup1`.
  2. 50/298 tin có `posted_date_raw = "Hạn DD/MM/YYYY"` (hạn nộp hồ sơ) bị `normalize.py` hiểu nhầm thành ngày đăng → `posted_date` rơi vào tương lai (tới 2027-01-20), khiến `window_end` (tính bằng max(posted_date)) lệch hẳn và loại gần như toàn bộ 298 tin khỏi cửa sổ 90 ngày. Đã clamp `posted_date` về ngày crawl (`crawled_at`) cho 50 dòng này — **cần M2 sửa gốc `normalize.py`** để phân biệt "Hạn nộp" khỏi ngày đăng thật, đây chỉ là vá tạm ở tầng dữ liệu.
