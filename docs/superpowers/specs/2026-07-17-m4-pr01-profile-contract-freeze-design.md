# Design: M4 PR-01 — Profile/Launch Contract Freeze

**Date:** 2026-07-17  
**Owner:** M4  
**Consumers:** M5 (Profile Card / chat), M1 (integration / preflight), M6 (Launch fields on results)  
**Approach:** Freeze & harden (Approach 1) — no greenfield schema rewrite  
**Status:** Draft for user review (brainstorming gate)

---

## 1. Problem

M5/M6/M1 need a **frozen Profile + Launch field set** so FE mocks, BE stubs, and later profiler/matching share one shape. PR-01 is the contract freeze gate (`docs/workstreams/M4_PROFILE_RECOMMENDER.md`, `docs/TASKS.md` PR-01, `docs/PREFLIGHT.md` §D).

Repo already has a scaffolded contract in three places plus mocks. The gap is **verification, missing DoD tests, explicit freeze documentation, and handoff** — not inventing a new Profile model.

## 2. Goals

1. **Three-way + mock sync:** `docs/API_CONTRACT.md` ↔ `backend/app/models/schemas.py` ↔ `frontend/types/index.ts` ↔ `frontend/lib/mock/*` for Profile, ChatRequest/Response profile payload, ProfilePatch, and Launch-related enums.
2. **Explore backward-compatible:** omitting `journey_mode` defaults to `"explore"`.
3. **Ethics / privacy freeze:** no gender, real name, school prestige, GPA (or equivalent prestige signals) on Profile / ProfilePatch / OpenAPI Profile properties (`SECURITY_PRIVACY.md`, `AI_DESIGN.md` §5, `BIAS_AUDIT.md` structural checks).
4. **Launch optional fields present:** `journey_mode`, `education_stage`, `job_goal`, `experiences[]` with shared core dimensions/skills/interests/constraints/evidence.
5. **PATCH semantics documented and testable at model/stub level:** omit = keep; explicit `null` on `education_stage` / `job_goal` = clear (full session persistence remains PR-03).
6. **Handoff ready:** tests green; workstream + HANDOFF template filled; limitations explicit.

## 3. Non-goals (explicit)

| Deferred | Owner task |
|---|---|
| Adaptive prompts / transcripts | PR-02 |
| SQLite session, merge deltas, completeness engine, delete TTL | PR-03 |
| Real chat handoff beyond contract shape | PR-04 |
| Matching / evidence / pathways / readiness computation | PR-05–07 |
| Bias paired conversation tests (runtime) | PR-08 |
| Agent tools / LangGraph | PR-12–14 |
| Changing field names, adding product fields, `extra="forbid"` breaking clients | Out of PR-01 |
| Live LLM calls for this PR | Forbidden (plumbing only) |

Product rules such as “max 3 experiences” and mode completeness thresholds live in `GRADUATE_LAUNCH.md` / `AI_DESIGN.md` and will be enforced in PR-03 code — **not** silently added as new required fields in this freeze.

## 4. Frozen field inventory (v1)

### 4.1 Enums

| Name | Values |
|---|---|
| `JourneyMode` | `explore` \| `launch` |
| `EducationStage` | `high_school` \| `vocational_student` \| `college_student` \| `university_student` \| `final_year` \| `recent_graduate` \| `other` (+ `null` on Profile) |
| `ExperienceKind` | `project` \| `internship` \| `work` \| `volunteer` \| `coursework` \| `other` |
| `Phase` | `warmup` \| `interests` \| `abilities` \| `constraints` \| `wrapup` |

### 4.2 `Profile`

| Field | Type | Notes |
|---|---|---|
| `session_id` | string | FE-generated uuid |
| `journey_mode` | JourneyMode | default explore; locked after opening (engine = PR-03) |
| `education_stage` | EducationStage \| null | optional; Launch-focused |
| `job_goal` | string \| null | Launch-focused |
| `dimensions` | map of 5 floats 0..1 | keys: `ky_thuat`, `phan_tich`, `sang_tao`, `xa_hoi`, `quan_ly` |
| `skills` | `{name, level, source_quote}[]` | evidence-backed when filled |
| `interests` | string[] | |
| `constraints` | `{region_pref, study_budget, study_duration_pref, notes}` | region = preference only |
| `evidence_quotes` | `{turn, quote, mapped_to}[]` | |
| `experiences` | ExperienceEvidence[] | Launch evidence; Explore may be empty |
| `completeness` | float 0..1 | progress indicator |

### 4.3 Forbidden on Profile / ProfilePatch (must not exist)

`gender`, `sex`, `name`, `full_name`, `school`, `school_name`, `school_prestige`, `gpa`, `email`, `phone`.

Rationale: `SECURITY_PRIVACY.md` §1 + anti-bias by design. Chat may mention these; storage/schema must not.

### 4.4 `ChatRequest`

- `session_id` required  
- `message` optional (`null` = opening)  
- `journey_mode` default `"explore"`

### 4.5 `ProfilePatch`

- Partial update: `dimensions`, `remove_skills`, `add_interests`, `education_stage`, `job_goal`, `add_experiences`, `remove_experience_titles`
- Semantics: field omitted → keep; `education_stage`/`job_goal: null` when present in payload → clear  
- Implementation of persistence after process restart: PR-03; PR-01 only requires stub/model behavior consistent with contract comments.

### 4.6 Recommendation Launch presenter (shape only)

- `Recommendation.job_readiness` is `null` for Explore; object for Launch (mock already).  
- PR-01 does **not** implement readiness logic; optional contract/OpenAPI field presence check only if cheap.

## 5. Architecture impact

No new services or routers. PR-01 sits at the **shared type boundary**:

```text
docs/API_CONTRACT.md  (law)
        │
        ├─► backend/app/models/schemas.py  (runtime validation)
        ├─► frontend/types/index.ts        (FE compile-time)
        └─► frontend/lib/mock/* + BE stub routers  (demo safety net)
```

Matches `ARCHITECTURE.md` “FE mock + BE stub same shape first” and `HANDOFF.md` integration order step 1.

## 6. Implementation plan (Approach 1)

### Step A — Audit (read-only first)

1. Diff field names/enums between contract doc examples, Pydantic models, TS interfaces, mocks (`chat.ts`, `profile.ts`, `recommendations.ts`), and BE stub `routers/chat.py` opening Launch behavior.
2. Record any drift; fix **all** sources in the same PR if drift exists.
3. Prefer comment clarifications in `API_CONTRACT.md` over shape changes.

### Step B — Harden only if needed

- Keep Pydantic default extra-ignore (do **not** enable `extra="forbid"` in this PR — avoids semi-breaking FE).
- Ensure defaults: `journey_mode="explore"`, empty collections isolated (already unit-tested).
- Stub PATCH: ensure `model_fields_set` / equivalent path clears nullable fields when client sends null (minimal fix if tests fail).
- Opening Launch: no inferred `education_stage` / `job_goal` / experiences (already integration smoke).

### Step C — Tests (DoD)

| Layer | File | Cases |
|---|---|---|
| Unit | `tests/unit/test_profile_contract.py` | forbidden fields absent; gender not dumped; opening clean; collection isolation; **API_CONTRACT example JSON parses**; ProfilePatch null clear at model/router helper level; ChatRequest omit journey_mode → explore |
| Contract | `tests/contract/test_schema_contract.py` | OpenAPI Profile properties == model fields; no forbidden keys; ProfilePatch field set; enums present if exposed |
| Integration | `tests/integration/test_api_smoke.py` | POST `/api/chat` with only `session_id` (omit journey_mode) works and profile is explore; optional PATCH null clear against stub |
| FE static | `frontend` | `npm run typecheck` |

No live network, no LLM.

### Step D — Docs / handoff

1. Mark PR-01 done (or partial + limitations) in `docs/workstreams/M4_PROFILE_RECOMMENDER.md`.
2. Emit handoff block per `docs/HANDOFF.md` → M5/M1.
3. Note deferred items (PR-02/03…) still open.
4. Do not invent metrics in `EVALUATION_RESULTS.md` for this PR.

### Step E — Verify commands

```bash
# backend
cd backend
python -m compileall app scripts tests
python -m pytest -q tests/unit/test_profile_contract.py tests/contract/test_schema_contract.py
python -m pytest -q tests/integration/test_api_smoke.py

# frontend types
cd ../frontend
npm run typecheck
```

If project has ruff/black later, run them; until then compileall + pytest + tsc are the PR-01 gates.

## 7. Allowed / forbidden files

**Allowed (M4 PR-01):**

- `docs/API_CONTRACT.md` (clarify only unless audit finds true bug)
- `backend/app/models/schemas.py`
- `frontend/types/index.ts`
- `frontend/lib/mock/profile.ts`, `chat.ts`, `recommendations.ts` (parity only)
- `backend/app/routers/chat.py` (minimal stub semantics for PATCH/default)
- `backend/tests/unit/test_profile_contract.py`
- `backend/tests/contract/test_schema_contract.py`
- `backend/tests/integration/test_api_smoke.py`
- `docs/workstreams/M4_PROFILE_RECOMMENDER.md`
- `docs/superpowers/specs/*` (this design)
- Optional short note in PR description / HANDOFF paste; avoid noisy edits to unrelated docs

**Forbidden:**

- New dependencies / stack changes
- `services/profiler.py` engine rewrite, prompts, matching, agent_graph
- Data pipeline, market.db, FE UI components (M5/M6 ownership)
- Weakening ethics rules or adding gender “for completeness”

## 8. Risks & fallbacks

| Risk | Mitigation |
|---|---|
| Audit finds real drift | Fix 3 sources + mocks in one PR (`TEAM_RULES.md` §2) |
| PATCH stub insufficient for null semantics | Minimal stub fix; document full persistence as PR-03 limitation |
| Scope creep into completeness rules | Leave thresholds to PR-03; tests only check schema/defaults |
| FE typecheck env missing node_modules | Note `NOT_RUN` with reason in handoff; still require BE pytest PASS |

## 9. Success criteria (Definition of Done)

- [ ] Field inventory matches contract across Pydantic + TS + mocks (Explore + Launch).
- [ ] No forbidden fields on Profile/ProfilePatch/OpenAPI Profile.
- [ ] Old Explore request (no `journey_mode`) still works → explore.
- [ ] Schema example from contract parses.
- [ ] Targeted unit + contract + integration tests PASS.
- [ ] `compileall` PASS; `npm run typecheck` PASS or documented `NOT_RUN`.
- [ ] Workstream PR-01 status + HANDOFF template filled; limitations listed.
- [ ] Diff stays focused; no silent contract expansion.

## 10. Implementation checklist (for writing-plans / builder)

1. Branch `feat/PR-01-profile-contract-freeze` from current base.
2. Audit matrix (contract / py / ts / mock) — fix drift.
3. Expand unit + contract + integration tests first or alongside.
4. Minimal stub PATCH/default fixes if tests require.
5. Run verify commands; fix failures.
6. Update `M4_PROFILE_RECOMMENDER.md` + handoff note.
7. Self-review: secrets, PII fixtures, no gender, mock still works.
8. Ready for buddy review (M3) + M5 consumer ack.

## 11. Downstream note (not PR-01 work)

After freeze, M5 may implement Profile Card against types/mocks (`F1-03`). M4 continues PR-02 prompts then PR-03 session engine without changing frozen field names. Agent work (PR-12) depends on PR-01 only for schema stability, not for graph code.

---

## Spec self-review log

- Placeholders: none intentional; deferred work listed as non-goals.
- Consistency: Approach 1 only; no `extra=forbid`; no new product fields.
- Scope: single PR, contract freeze + tests + docs — not multi-subsystem.
- Ambiguity resolved: “max 3 experiences” / completeness thresholds deferred to PR-03; PR-01 freezes shape only.
