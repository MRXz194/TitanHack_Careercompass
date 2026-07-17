# M1 — Lead, Integration, DevOps, Product Validation

**Mission:** giữ critical path chạy, main xanh, claims trung thực và demo có fallback. M1 không ôm code core của người khác.

**Đọc:** `PLAN.md`, `TASKS.md`, `AGENT_WORKFLOW.md`, `HANDOFF.md`, `TESTING.md`, `EVALUATION.md`, `SECURITY_PRIVACY.md`, `BUSINESS_CASE.md`.

## Card contract

Mỗi task phải có outcome cụ thể, action, expected artifact, verify/test, risk/fallback và handoff.
Task nào dùng `Verify` thay cho `Tests` vẫn phải ghi command/evidence theo `TESTING.md`; không có
evidence thì trạng thái là `NOT_VERIFIED`, không phải `DONE`.

## Task cards

### L-01 — Kickoff và contract alignment (H+0→2)
- **Problem:** team sinh viên + AI dễ hiểu khác nhau về MVP, mode và API.
- **Actions:** walkthrough đề bài; chốt P0/P1/P2; gán owner/buddy; cả team đọc hard rules; xác nhận Explore vs Launch.
- **Expected:** board chứa toàn bộ task ID hiện có với owner/status; contract v1 label; giờ sync/sleep; contact escalation; API budget envelope/pool owners.
- **Verify:** 6/6 chạy quickstart/mock; mỗi người nói lại input/output task đầu; không còn field “tự hiểu”.
- **Risk/fallback:** setup lỗi >30' → người đó dùng mock/UI hoặc fixture trước; buddy xử lý setup riêng.
- **Handoff:** kickoff note + contract version → toàn team.

### L-02 — GitHub guardrails + CI (H+1→3)
- **Actions:** branch protection, required CI/review, labels `area/*`, `priority/*`, `status/blocked`; issue/PR template.
- **Expected:** main không push trực tiếp; CI backend/frontend; CODE review SLA 30'.
- **Verify:** mở test PR nhỏ; CI trigger; direct push bị chặn; PR template render.
- **Risk/fallback:** free-plan không hỗ trợ rule → team convention + M1 là người duy nhất merge, log merge.

### L-03 — Deploy skeleton sớm (H+2→5)
- **Actions:** FE/BE deploy; env matrix dev/demo; CORS exact origin; health check; không upload real key vào log.
- **Expected:** public FE + `/api/health`; deployment runbook; rollback version.
- **Verify:** incognito/mobile mở được; mock/live flag; 404/error envelope; restart vẫn health.
- **Fallback:** BE hosting fail → FE mock deploy + local/replay BE cho demo; không chờ giờ 40.
- **Handoff:** URLs/env names/known limitation → M5/M6/M4.

### L-04 — Developer runbook (H+2→4)
- **Actions:** giữ `scripts/dev.md` đúng với Windows/macOS; thêm command test/mode/troubleshoot.
- **Expected:** người mới setup <10 phút, không hỏi miệng.
- **Verify:** một member chưa setup làm theo doc; sửa mọi bước ngầm.
- **Fallback:** Docker không phải P0; không thêm nếu làm phức tạp.

### L-05 — Integration watch (suốt 48h)
- **Actions:** review/merge theo critical path; run smoke sau merge; theo dõi artifact/hash; không merge hai PR cùng sửa contract.
- **Expected:** main xanh; integration log; blocker owner/ETA.
- **Verify:** CI + targeted smoke; contract diff 3 nơi; mock/live/replay không regression.
- **Risk:** review bottleneck → buddy review trước, M1 chỉ gate contract/security/deploy.

### L-06 — Data go/no-go (H+10)
- **Actions:** xem count, source permission, sample quality, salary/date coverage; quyết định target hay Plan B.
- **Expected:** decision record: source, actual count, plan, claims được phép.
- **Verify:** M2/M3 đọc cùng manifest; pipeline input schema không đổi.
- **Fallback:** <1k/nguồn blocked → dataset mở có license + seed; pitch đúng provenance.

### L-07 — E2E bug triage (H+20→44)
- **Actions:** chạy Explore + Launch persona mỗi 4h; bug severity; owner/ETA; freeze scope.
- **Expected:** test log với commit/mode/artifact; Sev-1/2 bằng 0 trước H+40.
- **Verify:** 3 runs liên tiếp; refresh/back/retry; low-confidence; profile correction; delete session.
- **Fallback:** live instability → replay-only decision được ghi, không giấu.

### L-08 — Replay safety net (H+18→22)
- **Actions:** capture fictional Explore/Launch requests/responses; short-circuit network; fixture schema validation.
- **Expected:** 2 persona replay, no network call, same contract as live.
- **Verify:** ngắt mạng/key rỗng; full flow; log chứng minh không gọi provider.
- **Risk:** fixture stale sau contract → CI schema test; contract owner cập nhật fixture cùng PR.

### L-09 — Pitch/deck evidence (H+38→44)
- **Actions:** problem → product → data quality → ethics → usefulness → business/pilot → scale; dùng actual metrics.
- **Expected:** ≤10 slides, mỗi number có source/denominator; Explore + Launch narrative.
- **Verify:** claim audit với M2/M3; không “real-time/skill shortage/representative study” quá dữ liệu.
- **Fallback:** metric fail → đưa limitation + deterministic fallback, không xóa failure.

### L-10 — Rehearsal/code freeze (H+44→46)
- **Actions:** 2 rehearsal có timer; speaker/controller/backup; freeze deployment; incident cue.
- **Expected:** demo <4 phút hoặc đúng slot; Q&A owner; video backup.
- **Verify:** cold browser, wifi off/replay, projector zoom, notification off.
- **Fallback:** một click chuyển replay; một click mở video; không live-debug trên sân khấu.

### L-11 — User/counselor test (recruit H+20, test H+31→38)
- **Actions:** ≥3 Explore + ≥2 Launch students, 1–2 counselors; consent quote; observe không hướng dẫn; rubric EVALUATION.
- **Expected:** completion/time/usefulness/new choice/new job query/criticism; anonymized quotes.
- **Verify:** report ghi x/y đúng sample; ít nhất 1 UX fix; không PII/raw transcript.
- **Risk:** không tuyển đủ → remote moderated + counselor proxy, report đúng n thực tế.

### L-12 — Privacy/source/release gate (H+2→4, H+38)
- **Actions:** source terms decision; no PII/log; session delete/TTL; CORS/secrets; prompt injection/error check.
- **Expected:** SECURITY_PRIVACY checklist signed; blocked claims/features removed.
- **Verify:** secret scan/diff, log inspection, delete session, malicious text rendered safely.
- **Fallback:** delete endpoint chưa xong → no persistence/restart DB + disclaimer; không pilot thật.

### L-13 — Test/AI-stack baseline (H+1→4, duy trì)
- **Problem:** sáu người và nhiều AI agent sẽ tạo test rải rác, gọi model live hoặc cài LangChain/LangGraph lệch version nếu không có gate chung.
- **Actions:** verify exact dependencies trong ADR/requirements; duy trì `pytest.ini` và `tests/unit|contract|integration|e2e|fixtures`; CI chạy import smoke → compile → unit → contract → integration → route check; review mọi fixture theo no-network/no-PII rule.
- **Expected:** test tree/markers đúng `TESTING.md`; failures chỉ đúng layer; E2E Explore/Launch/replay có owner và status thật.
- **Verify:** clean environment install; chạy toàn bộ command baseline; cố tình dùng marker sai để xác nhận strict markers; rút key/network vẫn chạy unit/contract/integration.
- **Risk/fallback:** package install conflict → giữ `AGENT_MODE=deterministic`, ghi exact resolver error và sửa dependency PR; không để từng member tự pin version khác.
- **Handoff:** command/output/commit + test status matrix → toàn team; M4 nhận stack baseline cho PR-12.

## M1 hourly dashboard

| Check | Green | Yellow | Red action |
|---|---|---|---|
| Data H+10 | allowed source + ≥1k | low coverage | Plan B immediately |
| Chat H+18 | 10 turns valid | repeat/latency | freeze prompt + fallback |
| Core H+30 | E2E skeleton | one integration gap | cut P2 |
| Real H+34 | grounded live flow | partial live | template/replay |
| Freeze H+40 | gates documented | noncritical fail | remove claim/feature |
