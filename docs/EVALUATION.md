# EVALUATION — Chứng minh core hoạt động, không chỉ demo đẹp

> M1 sở hữu bảng pass/fail; M2/M3/M4 cập nhật phần mình. Không sửa ngưỡng sau khi đã xem kết quả chỉ để “làm đẹp số”.

## 0. Test/verify workflow cho mọi task

Mỗi PR phải ghi bốn lớp, dùng `NOT_APPLICABLE` có lý do thay vì bỏ trống:

1. **Static/contract:** type/schema/import/JSON/link/secret checks.
2. **Unit/fixture:** pure parser/scoring/transform/component states.
3. **Integration:** producer→consumer interface, DB/API/mock/live/replay tương ứng.
4. **Acceptance:** DoD/task card và user-visible outcome.

Kết quả ghi `command | environment | commit | PASS/FAIL/NOT_RUN | evidence`. “AI đã review” không phải evidence. Test fail không được xóa/skip để merge; phải fix, fallback hoặc M1 chấp nhận limitation và bỏ claim/feature.

### Test ownership

| Area | Builder test | Buddy verify | Release gate |
|---|---|---|---|
| Crawl/normalize | parser fixtures/idempotence | M3 sample read/hash | M1 source/data go-no-go |
| Extraction/stats | gold + aggregate fixtures | M2 trace raw→stat | M1 metric/claim audit |
| Profiler/matching | state/scoring/invariants | M3 persona/number grounding | M1 E2E/bias/replay |
| FE explore/results | component states + typecheck | M5↔M6 browser task | M1 usability/demo run |
| Contract/deploy | smoke/OpenAPI/CI | affected consumer | M1 merge/deploy |

## 1. Quality gates bắt buộc

| Gate | Cách đo | Owner | Pass trước |
|---|---|---|---|
| Data validity | schema, dedupe, ngày/lương/vùng, source URL, coverage report | M2 | H+20 |
| Skill extraction | golden set 100 postings; precision/recall/F1 micro | M3 + M2 review | H+24 |
| Career mapping | % mapped + accuracy trên 50 mẫu | M3 | H+28 |
| Profiler | 6 Explore + 6 Launch conversations: JSON valid, không lặp, evidence truy vết | M4 | H+18 |
| Recommendation | 8 Explore + 4 Launch golden personas, rubric 1–5 bởi ≥2 người | M4 + M3 | H+34 |
| Grounding | mọi số trong evidence tồn tại trong stats input | M4 | 100% trước H+36 |
| Route coverage | ≥2 route/nghề và ≥1 non-university | M4 + script | 100% trước H+34 |
| Bias | gender/region paired tests + prompt audit | M4 + cả team | H+37 |
| UX | ≥3 Explore + ≥2 Launch students + 1–2 tư vấn viên | M1 + M5 | H+38 |
| Reliability | 3 E2E liên tiếp; replay khi ngắt LLM | M1 | H+44 |

## 2. Data và skill extraction

Tạo `data/eval/skills_gold.jsonl` gồm 100 posting, cân bằng tối thiểu 3 vùng và 5 nhóm nghề. M2 gán skill theo taxonomy; M3 giữ riêng tập này khỏi dữ liệu dùng để chỉnh rule trước lần đo baseline.

- `precision = đúng / tất cả skill hệ thống trích`
- `recall = đúng / tất cả skill trong gold`
- Mục tiêu: precision ≥0.80, recall ≥0.65, F1 ≥0.70.
- Nếu không đạt: ưu tiên precision để không hiển thị skill sai; ghi limitation thật trong pitch.
- Báo cáo thêm `% posting không có skill`, `% unmapped career`, salary coverage và source/region distribution.

## 3. Tính đúng của tín hiệu thị trường

- `demand_count` là **số tin tuyển dụng trong snapshot**, không đồng nghĩa số vị trí tuyển hoặc thiếu hụt lao động.
- MVP gọi biểu đồ là **Radar nhu cầu kỹ năng tuyển dụng**. `gap_score` là proxy xếp hạng tín hiệu cầu, không phải đo trực tiếp khoảng cách cung–cầu.
- Trend chỉ hiện khi đủ hai cửa sổ thời gian và mỗi phía đạt ngưỡng mẫu; nếu không trả `low_confidence=true` hoặc ẩn trend.
- Salary phải có sample count/coverage trong data layer; <5 mẫu thì null. Không nội suy tin không công khai lương.
- Spot-check 10 aggregate bằng cách truy ngược về posting IDs; lưu kết quả trong report.

## 4. Profiler và recommendation

### 12 golden personas

8 Explore bao phủ kỹ thuật/sáng tạo/xã hội/phân tích/thực hành, tài chính hạn chế, tỉnh ngoài 3 vùng, chưa biết sở thích, gia đình gây áp lực, stereotype. 4 Launch bao phủ: project nhưng chưa thực tập, trái ngành, không có experience, skill mạnh nhưng goal mơ hồ.

Hai reviewer chấm output 1–5:

1. Phù hợp với evidence người dùng đã nói.
2. Đa dạng lựa chọn, không chỉ đổi tên nghề cùng nhóm.
3. Route khả thi với constraint, nhưng constraint không thành hard filter.
4. Giải thích cụ thể, không phán quyết hoặc bịa dữ liệu.

Pass: trung bình mỗi tiêu chí ≥3.5/5, không output nào vi phạm hard rule. Bất đồng reviewer >2 điểm phải review lại cùng M1.

### Launch invariants

- Matched skill có source quote/experience evidence: 100%.
- Missing skill thuộc role top skills và không trùng matched: 100%.
- 4 actions có week/action/deliverable/why: 100%.
- Paired gender/school-name không đổi readiness band/candidate set ngoài tolerance.
- Ít nhất 2 search query khác nhau, không chứa thuộc tính nhạy cảm.

## 5. Reliability, latency và cost

| SLO demo | Ngưỡng |
|---|---|
| Chat API p95 trên 20 calls | <5 giây |
| Recommendation p95 trên 10 calls | <8 giây |
| JSON valid sau retry | ≥99% |
| Unhandled 5xx trong 3 demo runs | 0 |
| Replay mode không gọi mạng LLM | 100% |
| Chi phí 1 full session | ghi số thật; cảnh báo nếu vượt budget M1 chốt |

Log chỉ metadata model/tokens/latency; không ghi nội dung hội thoại học sinh.

## 6. Report cuối

Tạo `docs/EVALUATION_RESULTS.md` tại H+36–42: dataset snapshot, metrics, failures, fix đã làm, limitations còn lại. Judge được xem cả pass lẫn fail; không cherry-pick.
