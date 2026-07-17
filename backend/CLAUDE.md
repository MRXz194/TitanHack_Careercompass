# backend/CLAUDE.md — Backend-specific AI context

Read root `CLAUDE.md` first. Backend = FastAPI + Pydantic v2 + SQLAlchemy + SQLite, Python 3.11.

## Layout (put code in the right layer)

- `app/routers/*` — HTTP layer only: parse request, call a service, return schema. No business logic here.
- `app/services/*` — business logic. `llm.py` is the ONLY file that talks to LLM/embedding APIs.
- `app/models/schemas.py` — Pydantic models, MUST mirror `docs/API_CONTRACT.md` exactly (field names, enums, units).
- `app/prompts/*` — all prompt strings, each with a `# vN — date — change` comment on top.
- `app/core/config.py` — all settings from env. Never read `os.environ` elsewhere.
- `scripts/*` — dev/test utilities runnable standalone (`python scripts/test_chat.py`).

## Rules

- Every LLM call: structured output parsed into a Pydantic model, retry ≤2 with error feedback, then a deterministic fallback (canned question / template evidence). An unhandled LLM failure that 500s the API is a demo-killer — never allow it.
- Evidence generation must pass the number-check: every digit in LLM output must exist in the stats dict passed in (see `services/` when implemented, design in docs/AI_DESIGN.md §4).
- `DEMO_MODE=replay` short-circuits chat/recommendations to cached JSON in `app/data/replay/` — keep this path working.
- Stats with < 5 salary samples return null, never a made-up number.
- SQLite via SQLAlchemy only (no raw sqlite3), so the Postgres upgrade path stays open.
- Log every LLM call: model, tokens, latency (plain `logging`, INFO).

## Run

```
uvicorn app.main:app --reload --port 8000   # from backend/
python scripts/test_chat.py                 # chat in terminal, no FE needed
```
