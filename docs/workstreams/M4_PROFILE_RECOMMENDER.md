# M4 — Conversational Profile, Matching, Explainability, Ethics

**Mission:** tạo profile có evidence và recommendation mở rộng cơ hội; cùng core phục vụ Explore và Launch.

**Owned:** profiler state/session, prompts, matching, evidence, pathways/readiness, recommend router. **Buddy:** M3.

## Task cards

### PR-01 — Profile/Launch contract freeze (H+0→3)
- **Actions:** review Profile fields với M5; optional journey/education/experience; no gender/name/school prestige; patch semantics.
- **Expected:** contract + Pydantic + TS + mock đồng bộ; Explore default backward-compatible.
- **Tests:** schema examples parse; old Explore request still works; no forbidden fields.
- **Handoff:** contract v1 → M5/M1.

### PR-02 — Adaptive prompts for two modes (H+2→8)
- **Actions:** shared tone/safety; Explore asks activities/abilities/constraints; Launch asks projects/internships/tools/job goal; one question/turn.
- **Expected:** versioned prompts + 3 Explore/3 Launch transcripts; structured delta.
- **Tests:** no repeated question; no gender; handles “không biết”, stereotype, no experience, prompt injection.
- **Fallback:** deterministic question bank per phase/mode.

### PR-03 — Profiler/session engine (H+8→16)
- **Actions:** deterministic phase state; completeness rules by mode; merge validated deltas; experience evidence; SQLite sessions; patch/delete.
- **Expected:** `/chat` 10 turns, profile persistence/edit, mode locked after opening.
- **Tests:** unit merge/completeness; 10-turn E2E each mode; retry≤2; model timeout fallback; restart persistence; delete.
- **Risk:** LLM overwrites evidence → code merge allowlist; preserve user corrections.

### PR-04 — Chat handoff (H+16)
- **Actions:** deploy sample Explore/Launch, request/response, latency/error/fallback notes.
- **Expected:** M5 integrates; M1 records replay immediately.
- **Verify:** consumer runs both modes and patch; contract/OpenAPI matches.

### PR-05 — Explainable matching (H+20→26)
- **Actions:** cosine candidate retrieval; weighted skill overlap; capped market signal; deterministic diversity/stretch; config thresholds.
- **Expected:** top 5 + stretch; region never filter; Launch uses evidence/project skill coverage.
- **Tests:** weight/unit; identical human profile different region keeps candidate set; market spike cannot dominate low fit; 12 personas rubric.
- **Fallback:** cosine + skill overlap only; market shown as information, not score.

### PR-06 — Grounded evidence + counterfactual (H+26→31)
- **Actions:** code selects quotes/stats; LLM verbalizes; digit/stat-key validator; counterfactual from rerun scoring; template fallback.
- **Expected:** why-from-you, why-from-market, true counterfactual, no unsupported claim.
- **Tests:** 100% number grounding; quote belongs session; null/low-confidence; injection; timeout.
- **Fallback:** deterministic Vietnamese templates.

### PR-07 — Study pathways + Graduate Launch readiness (H+26→31)
- **Actions:** ≥2 study routes; Launch matched/missing skills, readiness band, search queries, 4 deliverable actions.
- **Expected:** Explore `job_readiness=null`; Launch object follows GRADUATE_LAUNCH.
- **Tests:** route script; missing∩matched empty; missing⊆role top skills; matched evidence trace; actions weeks 1–4 + deliverable.
- **Fallback:** deterministic roadmap from KB; no course/company names without source.

### PR-08 — Bias/opportunity audit (H+31→35)
- **Actions:** gender paired, region paired, school-prestige mention ignored, route/stretch coverage, prompt audit.
- **Expected:** real `BIAS_AUDIT.md`, failures/fixes/retest.
- **Tests:** top-5 overlap ≥4/5 gender; region candidate set not poorer; readiness unchanged by gender/school name.
- **Fallback:** remove offending field/weight/copy; do not lower threshold.

### PR-09 — Transparency copy (H+35→36)
- **Actions:** explain data, mode, scoring, demand proxy, limits, autonomy, readiness meaning.
- **Expected:** ≤300 words main page + tooltips; student-readable Vietnamese.
- **Verify:** 2 outsiders paraphrase correctly; no “AI knows best/guaranteed job”.

### PR-10 — Quality tuning only (H+34→40)
- **Actions:** fix labeled issues from E2E/user test; prompt/config changes one at a time; rerun gold personas.
- **Expected:** no open Sev-1/2 `ai-quality`; before/after evidence.
- **Forbidden:** new model/feature/contract after freeze without M1.

### PR-11 — AI evaluation report (H+35→38)
- **Actions:** profiler validity, persona rubric, grounding, readiness invariants, latency/cost, paired bias.
- **Expected:** actual metrics + commit/model/prompt/artifact versions in `EVALUATION_RESULTS.md`.
- **Verify:** M3/M1 reproduce sample; no cherry-pick.

## Hard-stop rules

- No recommendation if profile completeness below mode threshold; ask/correct instead.
- No exact readiness probability, hiring prediction or personal salary prediction.
- User correction outranks model inference.
- LLM never selects candidates or invents requirements; code/data do.
