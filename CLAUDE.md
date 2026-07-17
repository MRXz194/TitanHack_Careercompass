# CLAUDE.md — AI Assistant Context (CareerCompass)

> Context file for Claude Code / Cursor / Copilot used by ALL team members. Read this + the package-level CLAUDE.md (`frontend/CLAUDE.md` or `backend/CLAUDE.md`) before generating any code. Team docs are in Vietnamese; code, comments, and identifiers are in English (UI strings in Vietnamese).

## What this project is

48h hackathon product addressing a real Vietnamese education-to-employment mismatch: students often choose from trends/family expectations without current labor signals; graduates then struggle to translate their study and projects into job roles/skills. Schools and counselors cannot provide deep 1:1, data-grounded guidance at scale.

Two journeys share one core:
- **Explore:** high-school/early students → career families + university/vocational/certificate routes.
- **Graduate Launch:** final-year/recent graduates → entry-level role families + evidenced/missing skills + search queries + 30-day deliverables. It is NOT a job board, CV scorer, auto-apply or hiring prediction.

Three pillars:
1. **Market Intelligence** — real job-posting data (crawled) → skill demand, salaries, trends per region.
2. **Conversational Profiler** — multi-turn Vietnamese chat builds a student profile (NOT a quiz); profile is visible and editable by the student.
3. **Explainable Recommender** — top-5 careers + 1 "stretch" suggestion, each with evidence (student quotes + market stats), ≥2 study routes (always ≥1 non-university), and a counterfactual.

**Ethics is a graded criterion (highest weight):** expand choices, never box in. No gender input anywhere in the profile/recommender. Region informs, never filters. All suggestions framed as reference, not verdict.

Judges prioritize: skill-signal extraction quality; personalization/explainability; anti-bias/opportunity expansion (high weight); actual usefulness to students/counselors. Code or UI work that does not improve one of these or demo reliability is P2.

## Source of truth documents

- `docs/API_CONTRACT.md` — FE↔BE contract. NEVER change response/request shapes without updating this file + `backend/app/models/schemas.py` + `frontend/types/index.ts` in the same PR. If your generated code needs a field that doesn't exist in the contract, STOP and tell the user to follow the contract-change process (TEAM_RULES.md §2).
- `docs/ARCHITECTURE.md` — component layout; put new files where §4 says.
- `docs/AI_FOCUS.md` — why this is an AI-centered hackathon product, what AI claims are allowed, and where the product applies.
- `docs/AGENTIC_RUNTIME.md` — bounded ReAct agent, tool allowlist, policy gates, budgets and agent evaluation. Read before touching profiler, LLM, matching or agent UI.
- `docs/AI_DESIGN.md` — prompt/scoring/bias design. Do not invent alternative scoring or prompt schemes.
- `docs/TASKS.md` — task IDs; the user will tell you which task (e.g. PR-05) they're on.
- `docs/HANDOFF.md` — required handoff template and artifact versions.
- `docs/EVALUATION.md` — fixed quality gates; do not weaken thresholds to make results pass.
- `docs/SECURITY_PRIVACY.md` — minors' data, source-use and logging rules.
- `docs/BUSINESS_CASE.md` — users/buyers, real workflow and pilot KPIs.
- `docs/GRADUATE_LAUNCH.md` — exact Launch scope/invariants; do not expand into recruitment automation.
- `docs/AGENT_WORKFLOW.md` — mandatory AI-assisted development workflow and cost controls.
- `docs/workstreams/M*.md` — detailed task cards by owner; read the matching member file.
- `docs/FEATURE_ROADMAP.md` — features allowed only after P0/P1 gates pass.
- `docs/PREFLIGHT.md` — kickoff readiness gate; docs alone never imply runtime READY.

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
9. Job postings measure observed hiring demand, not labor-supply shortage. UI says “Radar nhu cầu kỹ năng”; never overclaim `gap_score`.
10. Do not log raw student messages/profile or put real test transcripts in replay fixtures.
11. `journey_mode` changes questions/presentation, not the candidate/data core. Do not fork Explore and Launch services.
12. Launch `readiness.band` is not hiring probability; matched skill needs user evidence, missing skill must come from role market skills, every action needs a deliverable.

## Conventions

- Branches `feat/<TASK-ID>-slug`, commits `type(scope): message`, PRs < 400 lines, squash merge.
- Python: type hints, Pydantic models mirror the contract, black-ish formatting. TS: strict mode, types in `frontend/types/index.ts` mirror the contract.
- Errors: API returns `{"error": {"code", "message"}}`; FE shows friendly Vietnamese fallback, never a raw stack.
- LLM calls: always structured output + Pydantic validation + retry ≤2 + non-LLM fallback so the flow never dies mid-demo. In agent mode, LLM may plan from the fixed tool allowlist and phrase grounded evidence; it never directly selects careers, changes config/KB, calls arbitrary tools or bypasses policy.

## When generating code

- Prefer editing existing stubs over creating parallel new files (stubs already match the contract).
- Small, runnable increments; the user must be able to run it locally before PR.
- If a task seems to require changing the contract, architecture, or stack — say so explicitly instead of silently doing it.
- Follow the Builder–Reviewer–Verifier process in `docs/AGENT_WORKFLOW.md`; status is not DONE until tests actually run and handoff is acknowledged.
