# NEXT — Extra 24-hour plan

Implementation branch: `codex/day3-opportunity-plan`. M1 ghi baseline/release commit vào scorecard; task branch chỉ merge vào branch này theo dependency graph, không merge thẳng `main` trước Day 3 go/no-go.

Thư mục này chỉ được mở khi MVP hiện tại đã qua **Expansion Gate**. Mục tiêu của 24 giờ dư không phải tăng số lượng màn hình, mà tăng bằng chứng rằng CareerCompass giải quyết đúng đề: tín hiệu tuyển dụng có chất lượng, gợi ý cá nhân hóa có thể giải thích, mở rộng cơ hội và hữu ích trong một buổi tư vấn thật.

Canonical docs vẫn là source of truth cho MVP. Sau khi Expansion Gate pass, thư mục này là **approved delta** duy nhất cho Day 3: thêm bounded `research` stage/endpoint và structured insight UI, nhưng giữ nguyên policy, privacy, deterministic recommendation và contract-change rules. Mọi mâu thuẫn khác phải dừng và hỏi M1; không tự diễn giải theo tài liệu mới hơn.

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

> Người học và counselor có thể so sánh hai hướng đi, kiểm tra “nếu thay đổi một năng lực/ràng buộc thì kết quả thay đổi thế nào”, truy ngược mọi tín hiệu thị trường về snapshot/confidence, và mở các nguồn hiện tại để tự kiểm chứng — mà không bị ép chọn top-1.

## Deliverable tích hợp

Tên nội bộ: **Opportunity Decision Lab**.

Nó gồm bốn capability, theo thứ tự ưu tiên:

1. **Signal Inspector:** chứng minh quality/provenance của skill signal theo nghề, vùng và thời gian.
2. **Compare + What-if:** so sánh hai hướng và chạy counterfactual bằng scoring thật.
3. **Counselor Brief:** bản tóm tắt in được, không PII, phục vụ buổi tư vấn.
4. **Career Research Cards (P1 sau H+17):** agent tìm nguồn hiện tại theo explicit intent, nhưng không được đổi profile/xếp hạng; live DuckDuckGo chỉ bật sau spike và luôn có replay/local fallback.

Chi tiết:

- [DAY3_PLAN.md](DAY3_PLAN.md) — mục tiêu, scope, timeline, architecture, kill switches.
- [TASKS.md](TASKS.md) — task card M1–M6, test/DoD/handoff.
- [EVALUATION.md](EVALUATION.md) — acceptance, quality, bias, usability và release scorecard.
- [DATA_RESEARCH_ARCHITECTURE.md](DATA_RESEARCH_ARCHITECTURE.md) — crawler/data quality workflow, bounded web-research agent, structured insight UI và scale path.
- [DATA_SNAPSHOT_AUDIT.md](DATA_SNAPSHOT_AUDIT.md) — kết quả crawl 3.914 records, hashes, raw-field diagnostics, blockers và handoff M2/M3.
- [RELEASE_SCORECARD.md](RELEASE_SCORECARD.md) — trạng thái triển khai thật, test evidence, DDG gate và các bước manual còn chặn release.

## Thứ tự triển khai bắt buộc

1. Chốt snapshot công khai, report và limitation theo từng source; không lấy quota bằng duplicate hoặc bypass block.
2. Chạy normalize/extract/map/aggregate và profile quality trước khi dùng số liệu trong UI.
3. Qua Expansion Gate của core rồi mới mở Compare/What-if/Inspector.
4. Chỉ sau H+17 mới mở web-research P1; spike phải pass policy, timeout, citation và replay trước khi bật `WEB_RESEARCH_MODE=ddg`.
5. Mọi phần mới độc lập bằng feature flag; nếu fail thì demo core + local snapshot, không phụ thuộc live search.

## Kickoff cho thành viên và coding AI

Trước khi nhận task Day 3, mỗi người/AI phải đọc theo thứ tự:

1. `CLAUDE.md` và `frontend/CLAUDE.md` hoặc `backend/CLAUDE.md` theo phạm vi sửa.
2. `docs/API_CONTRACT.md`, `docs/ARCHITECTURE.md`, `docs/AGENTIC_RUNTIME.md`, `docs/TESTING.md`, `docs/TEAM_RULES.md`.
3. Bốn tài liệu trong thư mục `docs/next`, sau đó chỉ task ID mình nhận trong `TASKS.md` và dependency trực tiếp của task đó.
4. Kiểm tra `git status`, baseline commit/snapshot và handoff mới nhất trước khi code; không sửa hoặc stage file của lane khác.

Prompt handoff tối thiểu cho AI:

```text
Task: <N?-??>
Baseline commit/snapshot: <sha/hash>
Problem + expected output: <copy từ TASKS.md>
Files/contracts được phép sửa: <list>
Dependencies đã nhận: <task/commit/artifact>
Commands bắt buộc: <tests/build/smoke>
Hard invariants: no score/profile mutation from web; source/confidence visible;
route opportunity; no gender/school/GPA scoring; replay/offline fallback.
Kết thúc bằng: changed files, test evidence, limitations, consumer handoff.
```

AI không được đọc raw job text hàng loạt vào prompt, tự thêm package/API/field, tự đổi score threshold hoặc mở live search nếu task card/feature gate chưa cho phép.

## Claim boundary

- Job postings phản ánh **observed hiring demand**, không chứng minh thiếu hụt cung–cầu.
- Một snapshot có timestamp không phải dữ liệu “real-time”; trend chỉ hợp lệ khi đủ cửa sổ thời gian và sample.
- “What-if” là thay đổi giả định để tham khảo, không dự đoán tương lai hay xác suất được tuyển.
- Web result là nguồn tham khảo hiện tại có citation; nó không phải evidence để agent tự đổi score hoặc tạo market statistic.
- Counselor Brief là tài liệu mở đầu thảo luận, không phải kết luận hướng nghiệp.
- Region dùng để cung cấp bối cảnh thị trường; không loại nghề khỏi candidate set.
- Không thêm gender, school prestige, GPA scoring, CV ranking, job auto-apply hoặc employer ranking.
