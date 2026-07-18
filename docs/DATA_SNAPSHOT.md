# DATA SNAPSHOT CARD — release artifact

> Status: `BUILT_WITH_CAVEATS`. Đây là snapshot nhu cầu tuyển dụng quan sát được, không phải dữ liệu thời gian thực và không đo nguồn cung lao động.

| Field | Value |
|---|---|
| Snapshot / SHA-256 | `real_jobs_snapshot_20260718` / `c6c1db099370db28c10ccd032ceb173078930349191ccdd09939b70676831dfd` |
| Built at / analysis window | `2026-07-18T02:43:13Z` / tối đa 90 ngày |
| Raw / normalized | 300 / 298; 2 dòng drop hoặc dedupe (0,67%) |
| Sources | TopCV 100, VietnamWorks 99, ITViec 99 |
| Regions | Hà Nội 158, HCM 38, Đà Nẵng 2, other 100 |
| Salary evidence | 127/298 (42,62%); percentile null khi mẫu không đủ |
| Experience evidence | 199/298 (66,78%); entry-level 76 |
| Skill extraction | `skill-extraction-v1`; 261/298 có ít nhất 1 skill; 127 low-signal dùng dictionary fallback; live LLM success 0 |
| Career mapping | `career-mapping-v1-stub`; 89/298 (29,87%); title-pattern-only; accuracy `NOT_RUN` |
| Deploy artifact | `backend/market.db`: 43 career-stat rows, 548 skill-stat rows, 16 metadata rows; không chứa job description |
| Trend | `NULL` cho snapshot hiện tại vì chưa đủ hai cửa sổ thời gian đáng tin |

## Nguồn và quyền sử dụng

- Policy pages được ghi trong `data/processed/manifest.json`; `permission_status=unverified` cho cả ba nguồn. Privacy/terms page không được diễn giải thành giấy phép tái phân phối.
- Raw JSON, processed full text và auto-labeled gold không còn nằm trong Git HEAD. Chúng chỉ được giữ local/secure storage để tái chạy pipeline.
- Repo chỉ phát hành aggregate SQLite, manifest và report tái lập; không công bố lại nội dung mô tả việc làm.
- UI phải ghi “hiring-demand proxy / nhu cầu quan sát được”, không gọi là “thiếu hụt kỹ năng” nếu chưa có dữ liệu supply.

## Chất lượng và giới hạn

- Posting count không bằng vacancy count; một tin có thể tuyển nhiều người hoặc đã đóng.
- Mẫu nhỏ và lệch Hà Nội/IT, không đại diện toàn bộ Việt Nam. Đà Nẵng chỉ có 2 tin.
- 209/298 tin chưa map vào KB 25 career; aggregate theo career vì vậy chỉ phản ánh phần mapped.
- LLM extraction live đã thất bại/không cấu hình ở snapshot này; số skill hiện tại chủ yếu đến từ taxonomy deterministic. Không được trình bày là LLM extraction đã đạt chất lượng production.
- Skill/career mapping accuracy và human usefulness vẫn `NOT_RUN`; coverage không thay thế accuracy.

## Fix nguồn đã đưa vào code

- `normalize.parse_posted_date` nhận biết “Hạn/Deadline”, ngày không hợp lệ và ngày tương lai; các trường hợp này quay về ngày crawl thay vì giả làm ngày đăng.
- `stable_job_id` dùng SHA-256 của URL chuẩn hóa, tránh hai URL khác nhau có cùng số đuôi bị trùng ID.
- Hai fix có unit regression test. Snapshot hiện tại đã được vá tương đương trước khi build; lần crawl kế tiếp sẽ nhận fix từ nguồn.

## Claim được phép khi pitch

“CareerCompass đã xử lý một snapshot 298 tin từ ba nguồn để trích tín hiệu kỹ năng, lương và khu vực. Đây là proxy quan sát có caveat; sản phẩm hiển thị denominator, độ tin cậy và không bịa trend khi dữ liệu chưa đủ.”
