# Design: M4 PR-02 — Adaptive Prompts for Explore & Launch

**Date:** 2026-07-17  
**Owner:** M4  
**Depends on:** PR-01 Profile contract freeze  
**Status:** Approved (Approach 1)

---

## 1. Problem

PR-01 froze the Profile shape. PR-02 supplies the **versioned conversational prompts**, **structured LLM turn schema (`profile_delta`)**, **deterministic question banks**, and **fictional transcript fixtures** so PR-03 can wire the session engine without inventing prompt/delta contracts mid-flight.

## 2. Goals

1. Versioned profiler prompts (shared tone/safety + Explore/Launch mode sections + phase goals).
2. Pydantic structured turn output: `reply`, `profile_delta`, `phase_done` (internal; not public API).
3. Deterministic fallback question banks for all phases × both modes.
4. Six fictional transcripts (3 Explore + 3 Launch) covering happy path + edge cases.
5. Offline tests: no gender asks, no repeated consecutive fallbacks, schema validation, edge cases (không biết, stereotype, no experience, prompt injection).
6. Handoff notes for PR-03 consumer.

## 3. Non-goals

- SQLite session / merge / completeness engine → **PR-03**
- Live LLM calls in CI → forbidden
- Replace `/api/chat` stub with real profiler → **PR-03**
- Agent tools / LangGraph → **PR-12+**
- Public API contract field changes → frozen by PR-01

## 4. Architecture

```text
backend/app/prompts/profiler.py     # versioned system text + fallback banks + builders
backend/app/models/profiler_io.py   # ProfilerTurnOutput / ProfileDelta (internal)
backend/tests/fixtures/profiler/    # 6 fictional multi-turn transcripts
backend/tests/unit/test_profiler_*.py
```

PR-03 will call `build_profiler_system(mode, phase)` + `llm.chat_json(..., ProfilerTurnOutput)` + merge `profile_delta` into `Profile`.

## 5. Structured delta (internal)

```text
ProfilerTurnOutput:
  reply: str
  profile_delta: ProfileDelta
  phase_done: bool = false

ProfileDelta: (all optional / default empty — partial merge)
  dimensions: dict[str, float]
  skills: ProfileSkill[]
  interests: str[]
  constraints: ConstraintsDelta | null   # only set fields present
  experiences: ExperienceEvidence[]
  education_stage: EducationStage | null
  job_goal: str | null
  evidence_quotes: EvidenceQuote[]
```

- `extra="ignore"` on delta models (do not use `forbid` — LLM may emit noise).
- Forbidden keys (gender, name, school prestige, gpa, email, phone) must never be model fields; unit tests lock this.
- School/GPA must not appear as skill evidence; prompt text states this explicitly.

Field name `phase_done` matches existing prompt skeleton (AI_DESIGN also says `suggested_phase_done` — we standardize on **`phase_done`** for Pydantic + prompts).

## 6. Prompts

`PROFILER_PROMPT_VERSION = "profiler-v2"`

- `SHARED_RULES`: mình/bạn, 1 question/turn, ≤3 sentences, no gender, no jargon, widen on stereotypes, output JSON only.
- `EXPLORE_MODE_SECTION`: activities done for joy, abilities, soft constraints — never “em thích nghề gì” as first line of attack.
- `LAUNCH_MODE_SECTION`: stage, projects/internships/tools, job goal, evidence over school names.
- `PHASE_GOALS`: warmup → wrapup one-liners.
- `build_profiler_system(journey_mode, phase) -> str` concatenates shared + mode + phase.
- Fallback banks: Explore + Launch, every phase ≥1 question; abilities/interests ≥2 for rotation.

## 7. Transcript fixtures

Path: `backend/tests/fixtures/profiler/`

| File | Mode | Focus |
|---|---|---|
| `explore_01_activities.json` | explore | happy path activities → skills |
| `explore_02_khong_biet.json` | explore | “không biết” / uncertainty |
| `explore_03_stereotype.json` | explore | gender stereotype in user text; assistant must not store gender / not affirm stereotype |
| `launch_01_project.json` | launch | project + tools + job goal |
| `launch_02_no_experience.json` | launch | explicit no internship/project yet |
| `launch_03_injection.json` | launch | user tries prompt injection; delta must not absorb instructions as skills |

Each file metadata:

```json
{
  "contract_version": "v1",
  "prompt_version": "profiler-v2",
  "fictional": true,
  "journey_mode": "explore|launch",
  "persona_id": "...",
  "turns": [
    {
      "user": "...",
      "assistant": { "reply": "...", "profile_delta": {}, "phase_done": false },
      "phase": "warmup"
    }
  ]
}
```

## 8. Tests

| File | Cases |
|---|---|
| `test_profiler_prompts.py` | version set; build_system includes mode+phase; hard-rule phrases; no gender-ask patterns in prompts; all phases in both banks; fallback rotation no immediate repeat when ≥2 options |
| `test_profiler_io.py` | parse happy delta; ignore forbidden extras; empty defaults isolated |
| `test_profiler_transcripts.py` | load 6 fixtures; each assistant validates as ProfilerTurnOutput; static checks (≤1 question mark preferred; no “giới tính” ask; injection not in skill names) |

No live network.

## 9. Success criteria

- [ ] Prompts versioned and mode-aware builders work
- [ ] ProfilerTurnOutput/ProfileDelta usable by PR-03
- [ ] 6 transcripts present and pass static suite
- [ ] Fallback banks complete
- [ ] pytest unit (+ existing suite green)
- [ ] compileall PASS
- [ ] Workstream PR-02 DONE + handoff + deferred PR-03 wiring

## 10. Spec self-review

- No TBD placeholders for required scope.
- Public API unchanged (PR-01 freeze).
- Live LLM out of scope.
- `phase_done` naming standardized.
