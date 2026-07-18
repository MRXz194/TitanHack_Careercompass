# PREFLIGHT — release gate 48h

> M1 chỉ ghi `READY` khi các mục P0 kỹ thuật bên dưới có evidence ở đúng commit. Checkbox con người/deploy không được tự tick bằng code.

## P0 kỹ thuật

- [x] Scope: Explore + Graduate Launch dùng shared core; không job board/CV/auto-apply/hiring probability.
- [x] LangChain provider/typed contracts + custom LangGraph chỉ cho `/api/chat`; recommendation/data aggregation deterministic.
- [x] API contract, Pydantic, TypeScript và mocks cùng schema; error envelope thống nhất.
- [x] `backend/market.db` aggregate-only có 43 career rows, 548 skill rows, 16 metadata rows.
- [x] Raw/full-description/auto-gold bị ignore và được bỏ khỏi Git HEAD; manifest không tự nhận license.
- [x] Parser deadline/future-date và crawler ID collision có regression tests.
- [x] Embedding mixed-space bị loại khỏi runtime; scorer dùng một không gian 5 chiều rõ ràng.
- [x] E2E Explore/LangGraph và Launch/replay tồn tại, chạy trong CI.
- [x] Render build fail nếu thiếu aggregate DB; local FE dùng API thật (`NEXT_PUBLIC_USE_MOCK=0`).
- [x] Release env chọn `AGENT_MODE=langgraph`; `deterministic` và `DEMO_MODE=replay` là kill switches.

## Evidence hiện có

- Baseline `99f463e`: GitHub CI PASS; backend 285 tests; frontend 61 tests + typecheck + build.
- Current branch local: Python 3.11.9 venv; compile/import PASS; backend 262 unit+contract + 29 integration + 2 E2E; route 25/25; frontend 61 tests + typecheck + build PASS. CI vẫn phải chạy lại sau push.
- Local aggregate inspection bằng SQLite: đúng ba tables, không có description column.
- Mapping coverage 29,87%; accuracy, live LLM quality và human usefulness vẫn `NOT_RUN`.

## Việc M1 phải xác nhận thủ công

- [ ] 6/6 tên thật/GitHub handle, owner M1–M6, buddy reviewer và sleep shift đã chốt.
- [ ] Branch protection yêu cầu backend/frontend CI và một approval.
- [ ] Render/Vercel deploy đúng current commit; `/api/health` trả `market_db_loaded=true`, `postings_count=298`.
- [ ] CORS chỉ đúng Vercel origin; không dùng `*`; không có secret trong log/diff.
- [ ] Chạy Explore và Launch trên mobile/ẩn danh; profile correction, market page, results đều pass.
- [ ] Diễn tập kill switch: `AGENT_MODE=deterministic`, sau đó `DEMO_MODE=replay`.
- [ ] Pitch nói đúng claim boundary trong `EVALUATION_RESULTS.md` và caveat trong `DATA_SNAPSHOT.md`.
- [ ] Nếu còn thời gian: ≥5 student + ≥2 counselor/dual-rater; lưu consent và kết quả aggregate, không commit transcript.

## Go/no-go record

```md
Status: NOT_READY | READY_WITH_CAVEATS | READY
Commit/deployment: ...
Backend CI / Frontend CI / E2E: ...
Health: market_db_loaded=... / postings_count=...
Unmet item + owner + deadline: ...
Activated kill switch (if any): ...
M1 sign-off + time: ...
```

Hiện tại: `READY_FOR_CURRENT_BRANCH_CI`, chưa phải `READY_TO_DEMO` cho đến khi push + CI + deploy smoke pass.
