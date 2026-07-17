# CLAUDE.md — AI Assistant Context (CareerCompass)

> Context file for Claude Code / Cursor / Copilot used by ALL team members. Read this + the package-level CLAUDE.md (`frontend/CLAUDE.md` or `backend/CLAUDE.md`) before generating any code. Team docs are in Vietnamese; code, comments, and identifiers are in English (UI strings in Vietnamese).

## What this project is

48h hackathon product: AI career guidance for Vietnamese students. Three pillars:
1. **Market Intelligence** — real job-posting data (crawled) → skill demand, salaries, trends per region.
2. **Conversational Profiler** — multi-turn Vietnamese chat builds a student profile (NOT a quiz); profile is visible and editable by the student.
3. **Explainable Recommender** — top-5 careers + 1 "stretch" suggestion, each with evidence (student quotes + market stats), ≥2 study routes (always ≥1 non-university), and a counterfactual.

**Ethics is a graded criterion (highest weight):** expand choices, never box in. No gender input anywhere in the profile/recommender. Region informs, never filters. All suggestions framed as reference, not verdict.

## Source of truth documents

- `docs/API_CONTRACT.md` — FE↔BE contract. NEVER change response/request shapes without updating this file + `backend/app/models/schemas.py` + `frontend/types/index.ts` in the same PR. If your generated code needs a field that doesn't exist in the contract, STOP and tell the user to follow the contract-change process (TEAM_RULES.md §2).
- `docs/ARCHITECTURE.md` — component layout; put new files where §4 says.
- `docs/AI_DESIGN.md` — prompt/scoring/bias design. Do not invent alternative scoring or prompt schemes.
- `docs/TASKS.md` — task IDs; the user will tell you which task (e.g. PR-05) they're on.

## Tech stack (FIXED — do not suggest alternatives or add dependencies without asking)

- Frontend: Next.js 15 (App Router) + TypeScript + Tailwind v4 + Recharts. API calls only via `frontend/lib/api.ts` (has mock mode `NEXT_PUBLIC_USE_MOCK=1`).
- Backend: FastAPI + Pydantic v2 + SQLAlchemy + SQLite. Python 3.11.
- LLM: OpenAI-compatible client ONLY via `backend/app/services/llm.py` (chat = DeepSeek via env `CHAT_*`, embeddings = OpenAI `text-embedding-3-small` via env `EMBED_*`). Never import an LLM SDK elsewhere. Never hardcode model names or API keys.
- Vector search: NumPy cosine in-process. Do NOT add a vector DB.
- All prompts live in `backend/app/prompts/` with a version comment.

## Hard rules (violations break the demo or the ethics criterion)

1. **No gender field anywhere.** Not in Profile schema, not in prompts as an assumption, not in scoring. If chat reveals gender, do not store it.
2. **No invented numbers.** Any statistic shown to users must come from `market.db` / stats passed into the prompt. Evidence generation is validated by code.
3. **Region is never a hard filter** on career suggestions.
4. Every career recommendation includes ≥2 routes, ≥1 of type `vocational|college|certificate`.
5. All user-facing strings are natural Vietnamese (friendly "mình/bạn/em" tone, no jargon).
6. Salary unit = million VND/month (`*_trieu`).
7. Secrets only via env vars; `.env` is gitignored.
8. Keep the FE mock mode working at all times — it is the demo safety net.

## Conventions

- Branches `feat/<TASK-ID>-slug`, commits `type(scope): message`, PRs < 400 lines, squash merge.
- Python: type hints, Pydantic models mirror the contract, black-ish formatting. TS: strict mode, types in `frontend/types/index.ts` mirror the contract.
- Errors: API returns `{"error": {"code", "message"}}`; FE shows friendly Vietnamese fallback, never a raw stack.
- LLM calls: always structured output + Pydantic validation + retry ≤2 + non-LLM fallback so the flow never dies mid-demo.

## When generating code

- Prefer editing existing stubs over creating parallel new files (stubs already match the contract).
- Small, runnable increments; the user must be able to run it locally before PR.
- If a task seems to require changing the contract, architecture, or stack — say so explicitly instead of silently doing it.
