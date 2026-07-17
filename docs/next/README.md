# NEXT — Extra 24-hour plan

Thư mục này chỉ được mở khi MVP hiện tại đã qua **Expansion Gate**. Mục tiêu của 24 giờ dư không phải tăng số lượng màn hình, mà tăng bằng chứng rằng CareerCompass giải quyết đúng đề: tín hiệu tuyển dụng có chất lượng, gợi ý cá nhân hóa có thể giải thích, mở rộng cơ hội và hữu ích trong một buổi tư vấn thật.

## Expansion Gate — điều kiện bắt buộc

M1 chỉ chuyển team sang kế hoạch này khi tất cả điều kiện sau có evidence tại cùng một commit:

- Explore E2E live hoặc validated snapshot chạy thành công 3 lần liên tiếp.
- Launch E2E và replay chạy thành công ít nhất 1 lần; replay không gọi mạng/model.
- Không còn Sev-1/Sev-2; frontend typecheck/build và backend unit/contract/integration đều xanh.
- Market data có snapshot ID, source/date/count/confidence; không dùng seed mà gắn nhãn như dữ liệu thật.
- Matching, evidence grounding, route invariant và paired-bias tests pass.
- Có ít nhất 1 sinh viên và 1 counselor chạy flow nền, không gặp blocker.

Nếu một điều kiện fail, team quay về sửa P0/P1. Không mở task trong thư mục này để né blocker core.

## North star của ngày dư

> Người học và counselor có thể so sánh hai hướng đi, kiểm tra “nếu thay đổi một năng lực/ràng buộc thì kết quả thay đổi thế nào”, và truy ngược mọi tín hiệu thị trường về snapshot/confidence — mà không bị ép chọn top-1.

## Deliverable tích hợp

Tên nội bộ: **Opportunity Decision Lab**.

Nó gồm ba capability, theo thứ tự ưu tiên:

1. **Signal Inspector:** chứng minh quality/provenance của skill signal theo nghề, vùng và thời gian.
2. **Compare + What-if:** so sánh hai hướng và chạy counterfactual bằng scoring thật.
3. **Counselor Brief:** bản tóm tắt in được, không PII, phục vụ buổi tư vấn.

Chi tiết:

- [DAY3_PLAN.md](DAY3_PLAN.md) — mục tiêu, scope, timeline, architecture, kill switches.
- [TASKS.md](TASKS.md) — task card M1–M6, test/DoD/handoff.
- [EVALUATION.md](EVALUATION.md) — acceptance, quality, bias, usability và release scorecard.

## Claim boundary

- Job postings phản ánh **observed hiring demand**, không chứng minh thiếu hụt cung–cầu.
- “What-if” là thay đổi giả định để tham khảo, không dự đoán tương lai hay xác suất được tuyển.
- Counselor Brief là tài liệu mở đầu thảo luận, không phải kết luận hướng nghiệp.
- Region dùng để cung cấp bối cảnh thị trường; không loại nghề khỏi candidate set.
- Không thêm gender, school prestige, GPA scoring, CV ranking, job auto-apply hoặc employer ranking.
