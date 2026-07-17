# AGENT WORKFLOW — cách 6 thành viên dùng AI mà không phá kiến trúc

## 1. Mục tiêu

AI là pair programmer, không phải source of truth. Workflow này tối ưu ba thứ: ít block, ít token/API cost, và mọi thay đổi đều chạy/test/handoff được. Một người chịu trách nhiệm cuối cho mỗi task dù dùng bao nhiêu agent.

## 2. Context bootstrap bắt buộc

Mỗi task mở một AI session mới và đọc theo thứ tự:

1. `CLAUDE.md` hoặc `AGENTS.md` ở root.
2. `frontend/CLAUDE.md` hoặc `backend/CLAUDE.md` nếu chạm package đó.
3. Task card của member trong `docs/workstreams/`.
4. Chỉ các source-of-truth liên quan: API contract, architecture, AI design, data pipeline, evaluation/security/testing. Nếu task chạm agent/tool/LLM flow, bắt buộc đọc thêm `docs/AGENTIC_RUNTIME.md`, `docs/ADR_AGENT_ORCHESTRATION.md` và test matrix trong `docs/TESTING.md`.
5. Code hiện tại của đúng files `Allowed files`; không load cả repo nếu không cần.

Agent phải nhắc lại trước khi code: `Task ID`, expected artifact, files sẽ sửa, test sẽ chạy, contract có đổi không và stop condition.

## 3. Task packet chuẩn

```md
Task: <ID + tên>
Owner/reviewer: <M# / buddy>
Problem: <lỗi hoặc outcome cần đạt>
Inputs: <artifact + version/hash>
Allowed files: <danh sách>
Forbidden changes: <contract/stack/file người khác sở hữu>
Expected output: <file/API/UI/report cụ thể>
Acceptance tests: <lệnh + expected>
Fallback: <đường đơn giản nếu quá thời gian>
Handoff consumer: <ai nhận và cần gì>
```

Thiếu một mục → agent hỏi owner hoặc đọc docs; không tự mở scope.

### Bổ sung bắt buộc cho task agentic (PR-12/13/14 và consumer UI)

```md
Allowed tools/stages: <tên tool + stage được phép>
Policy invariants: <privacy/provenance/autonomy/budget cần giữ>
Trace policy: <những metadata được log; xác nhận không log CoT/raw transcript>
Failure behavior: <deny/timeout/invalid tool -> fallback nào>
Replay fixture: <path + contract/prompt/tool/snapshot versions>
```

Không dùng từ “agent tự quyết” trong handoff. Owner phải chỉ ra authority cuối nằm ở policy code, contract hay deterministic service.

## 4. Lifecycle cho mọi task

1. **Inspect:** đọc code/docs, xác nhận working tree và artifact version.
2. **Plan nhỏ:** tối đa 3–7 bước, nêu rủi ro và dependency.
3. **Contract/test trước:** thêm fixture/schema/test nhỏ trước hoặc cùng implementation.
4. **Implement vertical slice:** thay stub nhỏ nhất chạy được; không tạo parallel architecture.
5. **Verify:** chạy targeted test → unit/contract → integration → smoke/E2E phù hợp theo `docs/TESTING.md`.
6. **Self-review:** diff, secret/PII, hard rules, fallback/mock/replay.
7. **Buddy review:** reviewer đọc code và chạy ít nhất một lệnh, không chỉ đọc summary AI.
8. **Handoff:** dùng `docs/HANDOFF.md`; consumer xác nhận chạy được.

Không được ghi “done” nếu test chưa chạy. Nếu môi trường thiếu runtime, trạng thái là `CODE_COMPLETE_NOT_VERIFIED`, không phải `DONE`.

## 5. Phân luồng agent và file ownership

| Lane | Owner | Files chính | Không được tự sửa |
|---|---|---|---|
| Lead/integration | M1 | CI, deploy, replay, docs result | thuật toán data/AI |
| Data | M2 | `data/pipeline/crawl*`, `normalize.py`, manifests | API/UI |
| Market AI | M3 | taxonomy, extract/stats/embed, `services/market.py` | profiler/UI |
| Profile/recommend | M4 | profiler/matching/prompts/recommend router | crawler/charts |
| Agent runtime | M4 | LangChain tool schemas; `services/agent_graph.py`, `agent_policy.py`, `agent_tools.py` | provider adapter ngoài `llm.py`, `create_agent`, arbitrary integration, FE rendering |
| FE explore | M5 | chat/profile components, `/explore` | market algorithms |
| FE results | M6 | results/market/landing components | backend scoring |

Hai agent không sửa cùng file đồng thời. Cross-file contract change do một owner thực hiện trong một branch; hai bên review, không chia ba file contract cho ba agent.

## 6. Builder–Reviewer–Verifier pattern

- **Builder agent:** chỉ task card + allowed files; tạo implementation và targeted tests.
- **Reviewer agent:** chỉ đọc diff + source-of-truth; tìm lỗi contract, edge case, ethics/security; không rewrite toàn bộ.
- **Verifier:** chạy lệnh, API/UI smoke, ghi output thật. Có thể là người hoặc agent có terminal.

Builder không tự tuyên bố quality metric. Reviewer không merge. Owner quyết định dựa trên evidence.

## 7. Tối ưu token và API cost

- Dùng mock/seed và deterministic test trước khi gọi LLM thật.
- Một transcript/profile fixture tái dùng cho local test; không gọi model để test CSS/API plumbing.
- Batch + cache theo input hash/taxonomy version; resume từ checkpoint.
- Prompt ngắn, structured JSON; chỉ truyền fields cần thiết, không truyền raw dataset/cả docs.
- Agent planner chỉ nhận compact sanitized state + allowed-tool schema; không nhét full transcript, raw market data hoặc chain-of-thought vào context.
- Mỗi trace fixture dùng observation đã sanitize; không dùng transcript thật làm replay/demo.
- Trong agent context, dùng path + đoạn liên quan thay vì paste tất cả file lặp lại.
- Khi lỗi, gửi stack trace tối thiểu + command + changed files; không paste log hàng nghìn dòng.
- Mỗi task một session; cuối session ghi 5–10 dòng handoff để session sau không đọc lại lịch sử dài.
- M1 đặt budget thật cho extraction và full-session chat; vượt 70% budget → chuyển deterministic/template/replay cho dev.

### Budget envelope tại kickoff

M1 ghi số tiền/credit thật vào kickoff note (không hardcode giá model trong repo vì thay đổi). Phân bổ khuyến nghị:

| Pool | Share ceiling | Control |
|---|---:|---|
| Skill extraction prototype/full | 40% | chỉ low-signal postings, batch/cache, max posting cap |
| Profiler/evidence quality testing | 30% | scripted personas, cache transcript, deterministic plumbing |
| Integration/user test | 15% | live only on acceptance runs |
| Demo reserve | 5% | live persona; replay is default backup |
| Buffer | 10% | M1 approval only |

M3/M4 log estimated cost per job/session. Khi pool chạm 70%, owner báo M1; 90% hard stop live dev calls. Không dùng production API để generate sample copy/fixtures lặp lại.

## 8. Prompt template cho member

```text
Bạn đang làm CareerCompass task <ID>. Đọc CLAUDE.md, <package>/CLAUDE.md,
docs/workstreams/<FILE>.md task <ID>, API_CONTRACT.md và EVALUATION.md phần liên quan.

Trước khi sửa: tóm tắt problem, input artifact/version, allowed files, expected output,
test commands, hard rules và fallback trong <=10 dòng. Không đổi contract/stack ngoài task.
Sau khi sửa: chạy test, review diff, báo PASS/FAIL/NOT_RUN kèm evidence và handoff template.
```

## 9. Stop/escalation conditions

Agent phải dừng và báo owner khi:

- Cần field API chưa có, dependency mới, secret/quyền truy cập hoặc source crawl không rõ quyền.
- Test contradict docs, input artifact hash sai, hoặc sửa file đang có người khác sở hữu.
- Cần nới hard rule/quality threshold để pass.
- LLM output cần dữ liệu không có; không được bịa fixture như dữ liệu thật.
- Đã lặp cùng lỗi 2 lần hoặc kẹt 30 phút với AI; owner áp dụng rule 45/90.

## 10. Definition of Done cho AI-assisted task

- Diff chỉ trong scope/allowed files; không duplicate service/component.
- Acceptance tests chạy và output được ghi trong PR.
- Mock/live/replay liên quan vẫn hoạt động.
- Contract, types, docs và fixtures đồng bộ nếu shape đổi.
- Không secret/PII/raw transcript; user-facing copy đúng tiếng Việt và ethics.
- Consumer nhận artifact/version/lệnh chạy/limitation và thả ✅.
