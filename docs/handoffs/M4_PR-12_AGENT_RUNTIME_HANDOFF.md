# [HANDOFF] M4 · PR-12 — Agent tools + policy + LangGraph spike → M1/M3/M5

## Artifact

| Item | Path |
|---|---|
| Schemas | `backend/app/models/agent_schemas.py` |
| Policy | `backend/app/services/agent_policy.py` (`agent-policy-v1`) |
| Tools | `backend/app/services/agent_tools.py` (`agent-tools-v1`, 10 tools) |
| Graph / orchestrator | `backend/app/services/agent_graph.py` |
| Tests | `tests/unit/test_agent_*.py`, `tests/contract/test_agent_tool_contract.py` |

## Spike gate (ADR)

| Check | Result |
|---|---|
| StateGraph compile/invoke offline (fake planner) | PASS when `AGENT_MODE=langgraph` |
| Tool JSON schemas | PASS (10/10) |
| Unknown tool / stage deny → fallback | PASS |
| Deterministic mode never compile/invoke graph | PASS |
| Orchestration p95 (100 turns, no model) | PASS &lt;100ms |
| No CoT/raw transcript in trace | PASS |

## Runtime flags

| `AGENT_MODE` | Behavior |
|---|---|
| `deterministic` (default) | `plain_python_orchestrator` only; **no** graph compile |
| `langgraph` | custom `StateGraph` plan→policy→tool→compose |

Historical note (at PR-12 land): `/api/chat` still used classic profiler path.  
**Superseded:** **PR-13** wires `agent_chat` into `profiler.handle_turn`; **PR-14** red-teams allowlist/fallback.

## Forbidden (enforced by design)

- No `create_agent` / prebuilt ReAct / checkpointer / LangSmith app config  
- No browser/shell/arbitrary HTTP/KB write tools  
- Recommendation pipeline remains deterministic (PR-05…07)

## Verify

```bash
cd backend
python -m pytest -q tests/unit/test_agent_policy.py tests/unit/test_agent_tools.py tests/unit/test_agent_graph.py tests/contract/test_agent_tool_contract.py
python -m pytest -q tests/unit tests/contract tests/integration
```

## Consumer notes

- **M1:** pin already in requirements; default `AGENT_MODE=deterministic` for demo safety  
- **M5:** no API shape change this PR  
- **PR-13:** wire `invoke_agent_turn` into `/api/chat` for discover/confirm only  

## Consumer ack

- M1 spike gate review: ⬜  
- PR-13 ready to integrate: ⬜  
