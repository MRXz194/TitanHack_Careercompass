# PREFLIGHT — gate trước khi bấm giờ 48h

> M1 chỉ tuyên bố `READY` khi toàn bộ P0 checkbox pass. Tài liệu chi tiết không thay cho môi trường chạy được.

## A. Product/scope

- [ ] 6/6 hiểu đề bài và nói lại 4 tiêu chí chấm.
- [ ] Explore là live demo chính; Launch là shared-core P1 + replay safety net.
- [ ] P0/P1/P2 và kill switches được cả team chấp nhận.
- [ ] Out-of-scope job board/CV/auto-apply/hiring prediction được chốt.
- [ ] Persona Minh/An và demo timebox được duyệt.

## B. Team/ownership

- [ ] Gán tên thật/GitHub handle vào M1–M6; buddy pairs xác nhận.
- [ ] Mỗi người mở đúng `docs/workstreams/M*.md`, chọn task đầu và nói expected output/test/handoff.
- [ ] Sleep shifts, sync times và `#blockers` sẵn sàng.
- [ ] Không hai người/agent cùng sở hữu một file ở task đầu.

## C. Repo/environment

- [ ] Python 3.11 + Node 20 trên ít nhất 4 máy; 6/6 chạy FE mock.
- [x] Backend install + smoke tests pass trên 1 máy, sau khi pull `main` mới nhất commit `9a62969` (2026-07-17): `compileall` OK, `pytest tests/unit tests/contract` 231 passed, `pytest tests/integration` 26 passed, `scripts.check_routes` OK (25 careers). Cần thêm ≥1 máy khác để tick đủ điều kiện "4 máy".
- [x] Frontend `npm run typecheck` + `npm run build` pass (2026-07-17, commit `9a62969`, Next.js 15.5.20, 6 routes build tĩnh OK); `frontend/tests/unit/transparency-copy.test.ts` (chạy bằng `npx tsx`, không cần framework) cũng pass.
- [ ] CI test PR pass; branch protection/review active — **chưa bấm**: cần leader làm theo `docs/DEPLOY.md` §A (branch protection rule + labels).
- [x] `.env` không tracked, không có secret trong git history/diff (`git log --all -p` scan pattern `sk-...`/`*_API_KEY=` chỉ thấy `REPLACE_ME` trong `.env.example`). Dev/demo env matrix ghi ở `docs/DEPLOY.md`; key owner = M1 (chưa gán tên thật).
- [x] Mock/live/replay flags — `DEMO_MODE=replay` đã wired thật trong code (`backend/app/services/agent_chat.py`, `evidence.py`, `profiler.py` đều đọc `settings.demo_mode`), có 3 fixture thật trong `backend/app/data/replay/` (explore/launch/agent trace, đều đánh dấu `"fictional": true`). Chưa test bằng `CHAT_API_KEY` thật (live LLM path vẫn `NOT_RUN`, xem `docs/EVALUATION_RESULTS.md`).

## D. Contract/fixtures

- [ ] API contract + Pydantic + TS + mocks đồng bộ Explore/Launch.
- [ ] Contract version/label trước H+0; breaking change process rõ.
- [ ] Explore/Launch request/result fixtures parse được.
- [ ] Error envelope, null/low-confidence and no-session states có fixture.

## E. Data/AI cost

- [x] M2 có ít nhất 1 source candidate + Plan B dataset/license — 3 nguồn thật (topcv/vietnamworks/itviec) đã crawl, 298 postings, terms/license URL ghi trong `data/processed/manifest.json`. **L-06 go/no-go (2026-07-17): Plan A, tiếp tục crawl** — xem `docs/DATA_SNAPSHOT.md`§"Go/no-go decision". Re-check tại H+10; <1k hoặc bị block → Plan B.
- [ ] M1 chốt crawl/API/LLM budget và ngưỡng 70% chuyển fallback.
- [ ] LLM/embedding keys test bằng call tối thiểu, không paste key vào chat/issue.
- [ ] Cache/artifact/replay directories và hash/version rule rõ.
- [ ] M4/M1 cài đúng pinned LangChain/LangGraph từ `requirements.txt`; gateway import smoke pass; chốt spike 90 phút, `/api/chat` only, no `create_agent`/prebuilt/checkpointer/LangSmith service; `AGENT_MODE=deterministic` fallback chạy được.
- [x] M1 chạy test gates theo `TESTING.md`: compile; unit; contract; integration; route invariant — tất cả xanh (chạy 2026-07-17, commit `9a62969` sau khi M2/M3/M4/M5/M6 merge: `compileall` OK, `pytest tests/unit tests/contract` 231 passed, `pytest tests/integration` 26 passed, `scripts.check_routes` OK). E2E folder tồn tại (`backend/tests/e2e`) nhưng rỗng → `NOT_IMPLEMENTED`, chưa có owner/status thật, cần L-07 gán khi core sẵn sàng.

## F. Ethics/security/evaluation

- [ ] No-gender/region-not-filter/readiness-not-probability rules được 6/6 hiểu.
- [x] Data source/PII/session retention checklist có owner — `docs/SECURITY_PRIVACY.md`§5 checklist release: 5/6 mục M1 đã verify pass (secret scan, session delete, no raw PII in log/replay, source manifest+attribution trên UI, dependency/endpoint smoke test); còn "Production CORS chỉ có FE origin" chờ L-03 deploy xong mới verify được.
- [ ] Gold data/persona templates sẵn, không tune trên test set sau khi đo baseline.
- [ ] Người test dự kiến và consent quote template đã liên hệ.

## Go/no-go record

```md
Status: NOT_READY | READY_WITH_CAVEATS | READY
Time/commit: ...
Unmet item + owner + deadline: ...
Approved P0/P1 cuts: ...
M1 sign-off: ...
```

Repo hiện chỉ là `READY_FOR_TEAM_REVIEW` cho đến khi runtime/CI/source/key items được kiểm chứng trên máy team.
