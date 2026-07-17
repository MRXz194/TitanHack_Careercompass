# 🤝 TEAM RULES — Quy tắc làm việc chung (48h)

> Mục tiêu của rules: **không ai bị block, main luôn chạy, không cãi nhau lúc 3h sáng.**

## 1. Git workflow

- **Branch:** `main` được bảo vệ — không push thẳng. Mỗi task một branch:
  - `feat/<TASK-ID>-mo-ta-ngan` → `feat/PR-03-chat-engine`
  - `fix/<TASK-ID>-mo-ta` cho bugfix
- **Commit message:** `<type>(<scope>): <mô tả>` — VD: `feat(backend): add /api/chat endpoint`, `fix(frontend): profile card không update`. Type: `feat|fix|docs|chore|refactor`.
- **PR:**
  - Nhỏ — mục tiêu < 400 dòng diff. To hơn thì tách.
  - Điền PR template (có sẵn), gắn Task ID vào title: `[PR-03] Chat engine`.
  - 1 review là đủ merge. **Buddy review của nhau** (M2↔M3, M4↔M3, M5↔M6), M1 review phần còn lại. Review trong vòng **30 phút** kể từ khi được tag — đang bận cũng dừng tay review, vì người kia đang chờ.
  - Merge kiểu **squash** cho gọn history.
- **Kẹt conflict > 15 phút** → gọi M1, không tự "giải quyết mạnh tay".
- Commit thường xuyên (ít nhất mỗi 2h khi đang code) — mất điện/mất máy không mất việc.

## 2. API contract là luật

- [API_CONTRACT.md](API_CONTRACT.md) là **nguồn chân lý duy nhất** giữa FE và BE.
- Contract **freeze tại H+8**. Sau đó muốn đổi: nhắn M1 → M1 gọi 5 phút với 2 bên liên quan → sửa file contract TRƯỚC → rồi mới sửa code. Đổi contract mà không sửa file = revert.
- BE thêm field mới (additive) thì được, **xóa/đổi tên field** thì phải theo quy trình trên.
- FE luôn giữ được **mock mode** (`NEXT_PUBLIC_USE_MOCK=1`) chạy được đến tận phút chót — đây là lưới an toàn demo.

## 3. Giao tiếp & sync

- **1 group chat chính** + kênh/thread `#blockers` riêng. Blocker post theo format: `[BLOCKED] <task-id> — đang kẹt gì — đã thử gì — cần ai`.
- **Rule 45/90:** kẹt 45 phút → hỏi buddy. Kẹt 90 phút → báo M1, đổi cách tiếp cận hoặc đổi người. **Hero-coding trong im lặng là cấm.**
- **Sync 10 phút** tại các mốc ⏰ trong PLAN.md. Format mỗi người 90 giây: (1) xong gì, (2) đang làm gì, (3) có block không. Không thảo luận sâu trong sync — hẹn riêng sau.
- Handoff (bàn giao giữa 2 người) phải có **tin nhắn tường minh** trong group: "@người-nhận D-05 xong, dataset ở `data/processed/postings.jsonl`, doc ở PR #12" — người nhận thả ✅ xác nhận. Không có ✅ = chưa handoff xong.
- Quyết định tranh cãi > 5 phút → M1 chốt. Chốt xong không mở lại (ghi vào `docs/BACKLOG.md` nếu tiếc).

## 4. Scope & chất lượng

- Feature ngoài In-scope (PLAN.md §2) → ghi `docs/BACKLOG.md`, không code. M1 có quyền veto tại chỗ.
- Sau mốc **M4 (H+40): feature freeze** — chỉ fix bug. Sau **H+46: code freeze** — không deploy gì mới.
- Không cần test coverage — nhưng **matching engine (PR-05) và normalize (D-04) phải có unit test** vì sai ở đó là sai âm thầm ra số liệu bịa.
- Secrets: **không bao giờ commit `.env`** (đã gitignore). Key chia sẻ qua group chat riêng tư, ai commit key thì người đó đi rotate.

## 5. Quy tắc dùng AI assistant (Claude/Cursor/Copilot) — QUAN TRỌNG vì cả team dùng AI

1. **Trước khi prompt:** mở `CLAUDE.md` (root) + `CLAUDE.md` của package đang làm (frontend/ hoặc backend/) — nếu tool không tự đọc thì paste vào context. Paste thêm nguyên văn task của bạn từ TASKS.md.
2. **Prompt theo task ID**, một task một phiên hội thoại — đừng dồn 3 task vào 1 chat, AI sẽ trộn lẫn.
3. AI sinh code xong: **bạn phải chạy được nó local trước khi mở PR.** "AI bảo thế" không phải là lý do trong review.
4. AI muốn thêm thư viện mới ngoài stack đã chốt (PLAN.md §6) → hỏi M1 trước. Mỗi dependency mới là một rủi ro deploy.
5. AI đề nghị đổi API contract / schema → KHÔNG nghe theo ngay, đi theo quy trình đổi contract ở §2.
6. Code AI sinh ra dính key/secret hardcode → xóa ngay, dùng env var.
7. Khi AI kẹt loop (sửa mãi không xong) > 30 phút → dừng, tự đọc lỗi, hoặc hỏi buddy. Đừng để AI đào hố sâu hơn.

## 6. Sức khỏe (nghiêm túc — chất lượng giờ 40+ phụ thuộc vào điều này)

- **Ngủ theo ca, có xếp lịch** (M1 xếp tại kickoff): ca 1 trong H+8→20, ca 2 trong H+30→40, mỗi người tối thiểu 2×3h. Người sắp ngủ phải handoff công việc dở trong group trước khi ngủ.
- Không quyết định kiến trúc sau 2h sáng — ghi lại, sáng chốt.
- Ăn uống: M1 lo đặt đồ ăn theo giờ sync — không ai skip bữa để code.
