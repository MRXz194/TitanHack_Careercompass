# backend/CLAUDE.md — Backend-specific AI context

Read root `CLAUDE.md` first. Backend = FastAPI + Pydantic v2 + SQLAlchemy + SQLite, Python 3.11.

## Layout (put code in the right layer)

- `app/routers/*` — HTTP layer only: parse request, call a service, return schema. No business logic here.
- `app/services/*` — business logic. `llm.py` is the ONLY file that instantiates LangChain model/embedding adapters or talks to provider APIs.
- `app/services/agent_graph.py` + `agent_policy.py` + `agent_tools.py` — PR-12-owned planned files for minimal LangGraph StateGraph, CareerCompass policy and LangChain typed local tools. Read `docs/AGENTIC_RUNTIME.md` + `docs/ADR_AGENT_ORCHESTRATION.md`; do not create a parallel agent folder or add arbitrary/external side-effect tools.
- `app/models/schemas.py` — Pydantic models, MUST mirror `docs/API_CONTRACT.md` exactly (field names, enums, units).
- `app/prompts/*` — all prompt strings, each with a `# vN — date — change` comment on top.
- `app/core/config.py` — all settings from env. Never read `os.environ` elsewhere.
- `scripts/*` — dev/test utilities runnable standalone (`python scripts/test_chat.py`).
- `tests/unit|contract|integration|e2e|fixtures` — canonical test tree; markers/commands are fixed in `docs/TESTING.md`.

## Rules

- Every LLM call: structured output parsed into a Pydantic model, retry ≤2 with error feedback, then a deterministic fallback (canned question / template evidence). An unhandled LLM failure that 500s the API is a demo-killer — never allow it.
- Agent planner can choose only the tool/stage allowlist. Policy code validates input, privacy, provenance, autonomy and per-turn budget before/after every call; it is the authority, not prompt text. Never store/expose chain-of-thought or raw transcript in an agent trace.
- LangChain is limited to model adapters, structured output and typed tool contracts. LangGraph is orchestration only for `/api/chat`. Do not use `create_agent`, prebuilt ReAct, LangSmith service/checkpointer state, or route recommendation/matching through the graph. `AGENT_MODE=deterministic` must remain a tested fallback.
- Import `ChatOpenAI`/`OpenAIEmbeddings` only in `services/llm.py`; other modules call gateway functions. Agent tools may import LangChain tool abstractions but provider adapters may not leak into domain code.
- Explore and Launch share profiler/matching/services. `journey_mode` selects prompt/completeness/presenter only; never duplicate routers or scoring engines.
- Launch readiness is deterministic and explainable: matched skills require profile/experience evidence; missing skills come from role top skills; LLM only verbalizes validated inputs.
- Evidence generation must pass the number-check: every digit in LLM output must exist in the stats dict passed in (see `services/` when implemented, design in docs/AI_DESIGN.md §4).
- `DEMO_MODE=replay` short-circuits chat/recommendations to cached JSON in `app/data/replay/` — keep this path working.
- Stats with < 5 salary samples return null, never a made-up number.
- SQLite via SQLAlchemy only (no raw sqlite3), so the Postgres upgrade path stays open.
- Log every LLM call: model, tokens, latency (plain `logging`, INFO).

## Run

```
uvicorn app.main:app --reload --port 8000   # from backend/
python scripts/test_chat.py                 # chat in terminal, no FE needed
python -m pytest -q tests/unit tests/contract
python -m pytest -q tests/integration
```
