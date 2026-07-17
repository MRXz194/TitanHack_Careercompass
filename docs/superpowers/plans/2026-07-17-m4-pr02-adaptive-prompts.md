# M4 PR-02 Adaptive Prompts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Ship versioned Explore/Launch profiler prompts, internal structured delta models, fallback question banks, six fictional transcripts, offline tests, and M4 workstream handoff — without wiring the chat session engine (PR-03).

**Architecture:** Prompt text + builders in `app/prompts/profiler.py`; internal IO models in `app/models/profiler_io.py`; fixtures under `tests/fixtures/profiler/`; pure unit tests; no live LLM.

**Tech Stack:** Python 3.11, Pydantic v2, pytest. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-07-17-m4-pr02-adaptive-prompts-design.md`

## Global Constraints

- No gender/name/school prestige/GPA fields on ProfileDelta or ProfilerTurnOutput.
- Public API contract (`API_CONTRACT.md` / `schemas.py` Profile) unchanged.
- No live model/network in tests.
- No SQLite session engine, no replacing `routers/chat.py` stub (PR-03).
- All prompts have version comment; `PROFILER_PROMPT_VERSION = "profiler-v2"`.
- Branch: `feat/PR-02-adaptive-prompts`.
- UI strings Vietnamese; identifiers English.
- Fixtures fictional only (`fictional: true`).

---

### Task 1: Branch + internal IO models

**Files:**
- Create: `backend/app/models/profiler_io.py`
- Test: `backend/tests/unit/test_profiler_io.py`

- [ ] **Step 1: Branch from kaguya**

```bash
git checkout kaguya
git checkout -b feat/PR-02-adaptive-prompts
```

- [ ] **Step 2: Write `profiler_io.py`**

```python
"""Internal profiler LLM I/O models (not part of public FE/BE API contract).

Used by PR-02 prompts/tests and PR-03 session engine merge.
Public Profile remains in app.models.schemas.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.schemas import (
    EducationStage,
    EvidenceQuote,
    ExperienceEvidence,
    ProfileSkill,
)


class ConstraintsDelta(BaseModel):
    model_config = ConfigDict(extra="ignore")

    region_pref: Optional[str] = None
    study_budget: Optional[str] = None
    study_duration_pref: Optional[str] = None
    notes: Optional[str] = None


class ProfileDelta(BaseModel):
    """Partial profile update from one profiler turn. Empty fields mean 'no change'."""

    model_config = ConfigDict(extra="ignore")

    dimensions: dict[str, float] = Field(default_factory=dict)
    skills: list[ProfileSkill] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    constraints: Optional[ConstraintsDelta] = None
    experiences: list[ExperienceEvidence] = Field(default_factory=list)
    education_stage: Optional[EducationStage] = None
    job_goal: Optional[str] = None
    evidence_quotes: list[EvidenceQuote] = Field(default_factory=list)


class ProfilerTurnOutput(BaseModel):
    """Structured LLM turn. Matches prompt JSON keys."""

    model_config = ConfigDict(extra="ignore")

    reply: str
    profile_delta: ProfileDelta = Field(default_factory=ProfileDelta)
    phase_done: bool = False
```

- [ ] **Step 3: Unit tests for IO**

Create `backend/tests/unit/test_profiler_io.py` covering:
- field sets exclude forbidden keys
- parse full example
- ignore extra `gender` on delta
- defaults isolated

- [ ] **Step 4: pytest + commit**

```bash
cd backend && python -m pytest -q tests/unit/test_profiler_io.py
git add backend/app/models/profiler_io.py backend/tests/unit/test_profiler_io.py
git commit -m "feat(backend): add profiler structured turn IO models for PR-02"
```

---

### Task 2: Versioned prompts + fallback helpers

**Files:**
- Modify: `backend/app/prompts/profiler.py`
- Test: `backend/tests/unit/test_profiler_prompts.py`

- [ ] **Step 1: Implement full profiler.py**

Requirements:
- Header `# v2 — 2026-07-17 — adaptive Explore/Launch prompts + structured delta`
- `PROFILER_PROMPT_VERSION = "profiler-v2"`
- `SHARED_RULES`, `EXPLORE_MODE_SECTION`, `LAUNCH_MODE_SECTION`, `PHASE_GOALS` (dict Phase → str)
- `build_profiler_system(journey_mode: str, phase: str) -> str`
- Keep/expand `FALLBACK_QUESTIONS` and `LAUNCH_FALLBACK_QUESTIONS` for all 5 phases
- `get_fallback_question(journey_mode, phase, turn_index: int) -> str` using `turn_index % len(bank)`
- `PROFILER_SYSTEM` = `build_profiler_system("explore", "warmup")` for backward compat

Hard rules must appear in SHARED_RULES text (Vietnamese instruction content for the model):
- never ask/infer gender; do not store if mentioned; widen stereotypes
- one question per turn, ≤3 sentences, mình/bạn
- school/GPA not skill evidence
- JSON only: reply, profile_delta, phase_done

- [ ] **Step 2: Tests** — version, all phases present, mode sections differ, gender-ask ban phrases, fallback rotation, no empty banks

- [ ] **Step 3: commit**

```bash
git commit -m "feat(backend): versioned Explore/Launch profiler prompts for PR-02"
```

---

### Task 3: Six fictional transcript fixtures

**Files:**
- Create: `backend/tests/fixtures/profiler/*.json` (6 files)
- Create: `backend/tests/fixtures/profiler/README.md` (short)

Each transcript ≥3 turns, valid assistant objects matching ProfilerTurnOutput, fictional personas.

Cover design table (explore 01–03, launch 01–03).

- [ ] **Step 1: Write 6 JSON files + README**
- [ ] **Step 2: commit**

```bash
git commit -m "test(fixtures): add 6 fictional Explore/Launch profiler transcripts"
```

---

### Task 4: Transcript static validation tests

**Files:**
- Create: `backend/tests/unit/test_profiler_transcripts.py`

- [ ] **Step 1: Load all fixtures, validate ProfilerTurnOutput, static safety rules**
- [ ] **Step 2: pytest + commit**

```bash
git commit -m "test(backend): validate profiler transcript fixtures for PR-02"
```

---

### Task 5: Handoff docs + full verify

**Files:**
- Modify: `docs/workstreams/M4_PROFILE_RECOMMENDER.md` (PR-02 status block)

- [ ] **Step 1: Run**

```bash
cd backend
python -m compileall app scripts tests
python -m pytest -q tests/unit tests/contract tests/integration
```

- [ ] **Step 2: Update workstream PR-02 with evidence + handoff → PR-03**
- [ ] **Step 3: commit docs**
- [ ] **Step 4: Push PR to base kaguya**

---

## Plan self-review

- Spec goals map to Tasks 1–5.
- No live LLM; no chat router rewrite.
- Forbidden fields covered in IO tests.
- Transcript edge cases listed in Task 3.
