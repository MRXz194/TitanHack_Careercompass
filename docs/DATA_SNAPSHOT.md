# DATA SNAPSHOT CARD — điền tại D-10

> Status: `BUILT`. Dữ liệu snapshot hiring thực tế được xử lý thành công.

## Go/no-go decision (L-06, M1) — 2026-07-17

- **Quyết định: Plan A — tiếp tục crawl nguồn hiện tại (topcv/vietnamworks/itviec).** Snapshot hiện tại (298/298 normalized, raw_count đúng 100/nguồn) là batch test, chưa phải giới hạn thật của nguồn; chưa tới mốc H+10 nên còn thời gian để đạt ≥1k. Plan B (dataset mở/Kaggle) không cần kích hoạt lúc này.
- **Action cho M2**: gỡ giới hạn 100 posting/nguồn, chạy full crawl D-02/D-03 theo `docs/DATA_PIPELINE.md`, target tổng ≥3k theo `TASKS.md` D-03.
- **Re-check**: M1 xem lại `data/processed/manifest.json` tại H+10; nếu vẫn <1k hoặc nguồn bị block (403/429), chuyển Plan B ngay, không cố gắng bypass.
- **Watch item (không chặn quyết định go/no-go)**: phân bố vùng hiện lệch — HCM 12.8% (< 15% target của D-06), Đà Nẵng 0.7%. Chưa cần hành động ở H+0→5, nhưng D-06 (H+20→26) cần crawl bù nếu vẫn lệch.

| Field | Value |
|---|---|
| Snapshot ID / SHA-256 | `real_jobs_snapshot_20260717` / `192e492fa2984f908525ac556a893767ab19a431831e7ea144558d0f8383a430` |
| Built at / window | 2026-07-17T15:39:29.791113+00:00 / 90 days |
| Sources + terms/license URLs | TopCV ([dieu-khoan](https://www.topcv.vn/dieu-khoan-bao-mat)), VietnamWorks ([chinh-sach](https://www.vietnamworks.com/chinh-sach-bao-mat)), ITViec ([privacy](https://itviec.com/privacy-policy)) |
| Raw / normalized / enriched count | Raw: 300 | Normalized: 298 | Enriched: TBD |
| Count theo source và region | Nguồn: itviec: 99 (33.2%), topcv: 100 (33.6%), vietnamworks: 99 (33.2%) <br> Vùng: hanoi: 158 (53.0%), hcm: 38 (12.8%), other: 100 (33.6%), danang: 2 (0.7%) |
| Salary coverage | 127/298 (42.6%) |
| Experience/seniority coverage + entry-level count | Exp: 199/298 (66.8%) <br> Seniority: {"entry": 76, "mid": 59, "senior": 86, "unknown": 77} <br> Entry-level: 76 |
| Dedupe/drop rate | Deduped: 2 (0.67%) |
| Skill extraction version | skills_vi_v1.0 |
| Career mapping coverage | TBD (filled in MI-03) |

## Allowed use và attribution

- Dữ liệu thu thập từ các nguồn công khai: TopCV, VietnamWorks, ITViec.
- Mục đích sử dụng: Phân tích giáo dục hướng nghiệp trong khuôn khổ Hackathon. Không kinh doanh, không xuất bản lại mô tả công việc (job descriptions) chi tiết của nhà tuyển dụng.
- Ghi nhận nguồn gốc trên giao diện: Tất cả số liệu hiển thị đi kèm chú thích nguồn gốc tương ứng.

## Known limitations

- Posting count không bằng vacancy count (một tin có thể tuyển nhiều người hoặc đã đóng).
- Nguồn/region coverage không đại diện hoàn bộ thị trường Việt Nam (phần lớn tập trung ở Hà Nội/HCM, thiếu các tỉnh lẻ).
- Salary chỉ phản ánh tin có công khai lương (hơn 50% tin ghi Thỏa thuận).
- Trend chỉ có ý nghĩa khi đủ cửa sổ thời gian và số lượng mẫu lớn hơn.
