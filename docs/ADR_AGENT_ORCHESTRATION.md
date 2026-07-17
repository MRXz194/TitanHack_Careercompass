# ADR — Agent orchestration: LangGraph tối giản

**Status:** Accepted for MVP, guarded by spike gate 90 phút  
**Owner:** M4 · Reviewer: M1/M3  
**Scope:** chỉ `POST /api/chat`; không áp dụng cho data pipeline hoặc `/api/recommendations`

## Quyết định

Dùng **LangGraph `StateGraph` tối giản** để hiện thực bounded ReAct chat agent. LangGraph chỉ nối các node; toàn bộ policy, tool schemas, merge profile, timeout và fallback vẫn là code CareerCompass.

```text
load_session → plan → policy_gate → execute_tool → compose → persist
                    └── deny/timeout ─────────→ fallback → persist
```

Không dùng trong MVP:

- LangChain `create_agent` hoặc prebuilt autonomous agent.
- LangSmith, Agent Server, cloud deployment hoặc vendor-specific tracing.
- LangGraph checkpointer/memory làm nguồn dữ liệu thứ hai.
- Multi-agent, subgraph, parallel tool execution hoặc human interrupt.
- LangGraph cho matching, market stats, pathways hay Launch readiness.

Session canonical vẫn ở SQLAlchemy `sessions.db`. Mỗi HTTP request load state, invoke graph có budget, validate kết quả rồi persist. `/api/recommendations` vẫn là deterministic pipeline.

## Nếu không dùng LangGraph thì dùng gì?

Fallback kỹ thuật là **plain Python bounded orchestrator**: `Enum` stage + Pydantic `AgentPlan` + dictionary tool registry + policy function + vòng lặp tối đa 2 tools. Nó không phải framework khác và dùng cùng tool/policy contracts. Vì vậy LangGraph là implementation detail, không khóa kiến trúc.

## Spike gate — tối đa 90 phút trong PR-12

Chỉ giữ LangGraph khi tất cả điều kiện pass:

- `StateGraph` compile/invoke với fake planner, không network và không đổi API contract.
- Unknown tool, policy deny, invalid JSON và timeout đều về deterministic fallback.
- Không log raw transcript/CoT; graph state chỉ chứa dữ liệu JSON-serializable đã sanitize.
- Targeted tests và CI hiện có pass; dependency được pin theo version thực tế đã cài.
- Overhead orchestration không LLM `<100ms` trên 100 lượt fixture.
- `AGENT_MODE=deterministic` chạy cùng contract mà không import/invoke graph path.

Nếu một gate fail hoặc M4 chưa quen LangGraph: dừng spike, dùng plain Python orchestrator; không kéo dài quá 90 phút và không làm trễ PR-03/PR-05/data path.

## Lý do phù hợp

- State/edge thể hiện đúng bounded decision loop và dễ trình bày với judge.
- Conditional edge làm policy deny/fallback rõ, test được.
- Sau hackathon có đường mở sang durable execution/HITL nếu counselor approval thực sự cần.
- Ranh giới trên giữ dependency không lan sang domain logic và giữ quyền tự chủ của người học.

## Trigger mở rộng sau MVP

Chỉ bật checkpointer/HITL hoặc subgraph khi có use case thật: counselor cần pause/approve, workflow kéo dài qua nhiều ngày, external write tool, hoặc nhiều node cần resume sau failure. Khi đó phải review privacy, retention và source of truth trước.
