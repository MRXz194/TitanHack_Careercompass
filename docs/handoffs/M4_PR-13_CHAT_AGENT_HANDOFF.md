# [HANDOFF] M4 · PR-13 — Chat agent orchestrator → M1 / M5

## Artifact

| Item | Path |
|---|---|
| Chat wiring | `backend/app/services/agent_chat.py` |
| Integrated in | `backend/app/services/profiler.py` → `handle_turn` |
| Graph/tools (PR-12) | `agent_graph.py`, `agent_policy.py`, `agent_tools.py` |
| Tests | `tests/unit/test_agent_chat.py`, `tests/integration/test_agent_chat_api.py` |

## Behavior

| Mode | Chat behavior |
|---|---|
| `AGENT_MODE=deterministic` (default) | Classic phase machine + optional **local** `extract_profile_evidence` tool (no graph, no planner LLM) |
| `AGENT_MODE=langgraph` | Bounded agent on **discover/confirm_profile** only; plan→policy→tool→compose; merge extract deltas; session still SQLAlchemy |
| `DEMO_MODE=replay` | Agent path **off** (no graph), classic path only |

### API contract (unchanged)

`ChatResponse = { reply, phase, turn, done, profile }` only.  
**Never** returns `trace`, `observations`, `thought_summary`, CoT.

### Stage mapping

| API `phase` | Agent stage |
|---|---|
| warmup / interests / abilities / constraints | `discover` |
| wrapup / done | `confirm_profile` |

`retrieve/explain/ready` agent tools are **not** selected from chat (recommendation remains PR-05…07 deterministic).

### Degradation

- Planner/tool/policy failure → classic deterministic reply; session preserved  
- Max 2 agent tools/turn + deadline in policy budget  
- No graph checkpointer  

## Verify

```bash
cd backend
python -m pytest -q tests/unit/test_agent_chat.py tests/integration/test_agent_chat_api.py
python -m pytest -q tests/unit tests/contract tests/integration
# optional langgraph:
# AGENT_MODE=langgraph python -m pytest -q tests/integration/test_agent_chat_api.py
```

## M5 notes

- Keep rendering `phase` status copy only; do not surface agent internals  
- Correction UX still `PATCH /api/profile/{id}`  

## M1 notes

- Default `AGENT_MODE=deterministic` for demo safety  
- Replay fixtures unchanged; agent disabled under `DEMO_MODE=replay`  

## Consumer ack

- M5 chat UX: ⬜  
- M1 replay smoke: ⬜  
