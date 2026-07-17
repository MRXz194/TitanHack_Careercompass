## Task
<!-- Task ID từ docs/TASKS.md, VD: [PR-03] -->

## Làm gì
<!-- 1-3 gạch đầu dòng -->

## Đã test thế nào
<!-- Chạy local ra sao? Lệnh gì? Screenshot nếu là UI -->

| Layer | Command/evidence | Result |
|---|---|---|
| Static/contract | | PASS / FAIL / N/A |
| Unit/fixture | | PASS / FAIL / N/A |
| Integration | | PASS / FAIL / N/A |
| Acceptance/DoD | | PASS / FAIL / N/A |

## AI-assisted workflow
<!-- Nếu dùng AI: builder session làm gì; reviewer là ai; verifier đã chạy lệnh nào. Không paste transcript dài. -->
- Builder/owner:
- Buddy reviewer:
- Verifier:

## Handoff / artifacts
<!-- Producer→consumer, path/version/hash, lệnh chạy, sample input/output, known limitations. Xóa mục nếu task không handoff. -->

## Checklist
- [ ] Tôi đã chạy code này local, không chỉ tin AI
- [ ] Không đổi API contract (hoặc đã sửa cả 3 nơi: contract + schemas.py + types/index.ts)
- [ ] Không commit secret / .env
- [ ] Diff < 400 dòng (hoặc đã báo M1 lý do)
- [ ] Metric/claim mới có sample size, source và limitation; không gọi hiring demand là supply shortage
- [ ] Không log/commit PII hoặc transcript người test; mock/replay vẫn chạy
- [ ] Tôi đã đọc task card trong `docs/workstreams/`; status không phải DONE nếu test chưa chạy
- [ ] Explore/Launch dùng shared core; readiness không được diễn đạt là xác suất tuyển dụng
