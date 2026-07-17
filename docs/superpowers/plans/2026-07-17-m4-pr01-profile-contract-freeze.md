# M4 PR-01 Profile/Launch Contract Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze and verify the shared Profile/Launch API contract (docs + Pydantic + TypeScript + mocks), expand DoD tests, run lint/typecheck/pytest, and hand off to M5/M1 — without inventing new product fields or building the profiler engine.

**Architecture:** Approach 1 (freeze & harden). Source of truth remains `docs/API_CONTRACT.md`; `backend/app/models/schemas.py` and `frontend/types/index.ts` must mirror it; FE mocks and BE chat stub must return the same shapes. PR-01 is a type-boundary + test gate, not a new service.

**Tech Stack:** FastAPI + Pydantic v2 + pytest (backend); TypeScript strict + `tsc --noEmit` (frontend); no new dependencies; no live LLM.

**Spec:** `docs/superpowers/specs/2026-07-17-m4-pr01-profile-contract-freeze-design.md`

## Global Constraints

- No gender / name / school prestige / GPA / email / phone fields on Profile or ProfilePatch.
- Region is preference only, never a hard filter (schema comment only here).
- Do not change field names or add product fields unless audit finds true drift vs contract.
- Do not enable `extra="forbid"` (semi-breaking); keep Pydantic default ignore for extras.
- Do not implement SQLite sessions, LLM merge, prompts, matching, or agent graph (PR-02+).
- Live network/model calls forbidden in tests.
- Branch name: `feat/PR-01-profile-contract-freeze`.
- Commits: `type(scope): message`; keep PR small (<400 lines preferred).
- User-facing copy stays Vietnamese elsewhere; this PR is mostly schema/tests/docs in English identifiers.

### Frozen field sets (copy verbatim)

**Profile fields:**  
`session_id`, `journey_mode`, `education_stage`, `job_goal`, `dimensions`, `skills`, `interests`, `constraints`, `evidence_quotes`, `experiences`, `completeness`

**ProfilePatch fields:**  
`dimensions`, `remove_skills`, `add_interests`, `education_stage`, `job_goal`, `add_experiences`, `remove_experience_titles`

**Forbidden keys:**  
`gender`, `sex`, `name`, `full_name`, `school`, `school_name`, `school_prestige`, `gpa`, `email`, `phone`

**Dimension keys:**  
`ky_thuat`, `phan_tich`, `sang_tao`, `xa_hoi`, `quan_ly`

---

## File map

| File | Responsibility in PR-01 |
|---|---|
| `docs/API_CONTRACT.md` | Law; clarify comments only if audit finds wrong semantics |
| `backend/app/models/schemas.py` | Pydantic mirror; fix only true drift |
| `frontend/types/index.ts` | TS mirror; fix only true drift |
| `frontend/lib/mock/profile.ts` | Patch semantics parity |
| `frontend/lib/mock/chat.ts` | Explore/Launch profile shape parity |
| `frontend/lib/mock/recommendations.ts` | Launch `job_readiness` shape presence (no logic rewrite) |
| `backend/app/routers/chat.py` | Minimal stub: default explore; PATCH null clear if tests require |
| `backend/tests/unit/test_profile_contract.py` | Unit DoD |
| `backend/tests/contract/test_schema_contract.py` | OpenAPI + field-set DoD |
| `backend/tests/integration/test_api_smoke.py` | HTTP DoD |
| `docs/workstreams/M4_PROFILE_RECOMMENDER.md` | Status + limitations for PR-01 |

---

### Task 1: Branch + three-way audit

**Files:**
- Modify: none required unless drift found (record in commit message / later Task 5)
- Reference: `docs/API_CONTRACT.md`, `backend/app/models/schemas.py`, `frontend/types/index.ts`, `frontend/lib/mock/*.ts`, `backend/app/routers/chat.py`

**Interfaces:**
- Consumes: frozen field sets in Global Constraints
- Produces: written audit conclusion (PASS/DRIFT) used by Task 5

- [ ] **Step 1: Create branch**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass
git checkout kaguya
git pull --ff-only origin kaguya || true
git checkout -b feat/PR-01-profile-contract-freeze
```

Expected: on branch `feat/PR-01-profile-contract-freeze`.

- [ ] **Step 2: Run field-set audit script (read-only)**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass/backend
python - <<'PY'
from app.models.schemas import Profile, ProfilePatch, ChatRequest

PROFILE_EXPECTED = {
    "session_id","journey_mode","education_stage","job_goal","dimensions",
    "skills","interests","constraints","evidence_quotes","experiences","completeness",
}
PATCH_EXPECTED = {
    "dimensions","remove_skills","add_interests","education_stage","job_goal",
    "add_experiences","remove_experience_titles",
}
FORBIDDEN = {
    "gender","sex","name","full_name","school","school_name","school_prestige",
    "gpa","email","phone",
}
DIMS = {"ky_thuat","phan_tich","sang_tao","xa_hoi","quan_ly"}

assert set(Profile.model_fields) == PROFILE_EXPECTED, set(Profile.model_fields) ^ PROFILE_EXPECTED
assert set(ProfilePatch.model_fields) == PATCH_EXPECTED, set(ProfilePatch.model_fields) ^ PATCH_EXPECTED
assert FORBIDDEN.isdisjoint(Profile.model_fields)
assert FORBIDDEN.isdisjoint(ProfilePatch.model_fields)
assert ChatRequest.model_fields["journey_mode"].default == "explore"
p = Profile(session_id="audit")
assert set(p.dimensions) == DIMS
print("PY_AUDIT_OK")
PY
```

Expected stdout includes `PY_AUDIT_OK`. If assertion fails, note exact missing/extra fields for Task 5.

- [ ] **Step 3: Manually confirm TS + mock parity**

Open and confirm these names exist and match Global Constraints:

- `frontend/types/index.ts` — `Profile`, `ProfilePatch`, `JourneyMode`, `EducationStage`, `ExperienceKind`
- `frontend/lib/mock/chat.ts` — builds `Profile` with Launch fields
- `frontend/lib/mock/profile.ts` — applies patch omit/null for `education_stage`/`job_goal`
- `frontend/lib/mock/recommendations.ts` — `job_readiness` null vs object by mode

Write a one-line note for yourself: `AUDIT: py=PASS|DRIFT; ts=PASS|DRIFT; mock=PASS|DRIFT`.

- [ ] **Step 4: Commit branch marker only if no code yet (optional empty skip)**

If nothing to commit, skip. Otherwise:

```bash
git status
```

---

### Task 2: Unit tests — Profile contract DoD

**Files:**
- Modify: `backend/tests/unit/test_profile_contract.py`
- Test: same file

**Interfaces:**
- Consumes: `Profile`, `ProfilePatch`, `ChatRequest`, `ExperienceEvidence` from `app.models.schemas`
- Produces: unit coverage for parse example, defaults, forbidden fields, patch null flag

- [ ] **Step 1: Replace/extend unit test file with full DoD cases**

Write the full file content:

```python
import pytest
from pydantic import ValidationError

from app.models.schemas import ChatRequest, ExperienceEvidence, Profile, ProfilePatch


pytestmark = pytest.mark.unit

FORBIDDEN = {
    "gender",
    "sex",
    "name",
    "full_name",
    "school",
    "school_name",
    "school_prestige",
    "gpa",
    "email",
    "phone",
}

PROFILE_FIELDS = {
    "session_id",
    "journey_mode",
    "education_stage",
    "job_goal",
    "dimensions",
    "skills",
    "interests",
    "constraints",
    "evidence_quotes",
    "experiences",
    "completeness",
}

PATCH_FIELDS = {
    "dimensions",
    "remove_skills",
    "add_interests",
    "education_stage",
    "job_goal",
    "add_experiences",
    "remove_experience_titles",
}

DIMENSION_KEYS = {"ky_thuat", "phan_tich", "sang_tao", "xa_hoi", "quan_ly"}


def test_profile_field_set_matches_frozen_contract() -> None:
    assert set(Profile.model_fields) == PROFILE_FIELDS
    assert FORBIDDEN.isdisjoint(Profile.model_fields)


def test_profile_patch_field_set_matches_frozen_contract() -> None:
    assert set(ProfilePatch.model_fields) == PATCH_FIELDS
    assert FORBIDDEN.isdisjoint(ProfilePatch.model_fields)


def test_profile_does_not_accept_or_expose_gender() -> None:
    profile = Profile(session_id="unit-profile", gender="female")

    assert "gender" not in Profile.model_fields
    assert "gender" not in profile.model_dump()


def test_profile_ignores_other_forbidden_extras() -> None:
    profile = Profile(
        session_id="unit-forbidden",
        school_prestige="top",
        gpa=3.9,
        name="Minh",
        email="x@y.z",
    )
    dumped = profile.model_dump()
    for key in FORBIDDEN:
        assert key not in dumped


def test_opening_profile_has_no_unsupported_inference() -> None:
    profile = Profile(session_id="unit-opening", journey_mode="launch")

    assert profile.education_stage is None
    assert profile.job_goal is None
    assert profile.skills == []
    assert profile.interests == []
    assert profile.experiences == []
    assert profile.completeness == 0.0
    assert set(profile.dimensions) == DIMENSION_KEYS
    assert all(value == 0.0 for value in profile.dimensions.values())


def test_profile_collection_defaults_are_isolated() -> None:
    first = Profile(session_id="first")
    second = Profile(session_id="second")

    first.interests.append("dữ liệu")

    assert second.interests == []


def test_chat_request_defaults_journey_mode_to_explore() -> None:
    req = ChatRequest(session_id="explore-default")
    assert req.journey_mode == "explore"
    assert req.message is None


def test_api_contract_profile_example_parses() -> None:
    """Minimal full example aligned with docs/API_CONTRACT.md Profile schema."""
    example = {
        "session_id": "uuid-example",
        "journey_mode": "explore",
        "education_stage": "high_school",
        "job_goal": None,
        "dimensions": {
            "ky_thuat": 0.7,
            "phan_tich": 0.4,
            "sang_tao": 0.8,
            "xa_hoi": 0.3,
            "quan_ly": 0.2,
        },
        "skills": [
            {
                "name": "vẽ tay",
                "level": "tự đánh giá khá",
                "source_quote": "em thích vẽ",
            }
        ],
        "interests": ["vẽ", "sửa chữa đồ điện"],
        "constraints": {
            "region_pref": "danang",
            "study_budget": "hạn chế",
            "study_duration_pref": "ngắn",
            "notes": "gia đình muốn em học gần nhà",
        },
        "evidence_quotes": [
            {
                "turn": 3,
                "quote": "em hay sửa đồ điện trong nhà",
                "mapped_to": "ky_thuat",
            }
        ],
        "experiences": [],
        "completeness": 0.6,
    }
    profile = Profile.model_validate(example)
    assert profile.journey_mode == "explore"
    assert profile.skills[0].name == "vẽ tay"
    assert profile.constraints.region_pref == "danang"


def test_launch_profile_example_with_experience_parses() -> None:
    example = {
        "session_id": "launch-example",
        "journey_mode": "launch",
        "education_stage": "final_year",
        "job_goal": "tìm vai trò dữ liệu entry-level",
        "dimensions": {
            "ky_thuat": 0.2,
            "phan_tich": 0.8,
            "sang_tao": 0.4,
            "xa_hoi": 0.3,
            "quan_ly": 0.4,
        },
        "skills": [
            {
                "name": "Excel",
                "level": "đã dùng trong project",
                "source_quote": "em đã làm dashboard bán hàng bằng Excel",
            }
        ],
        "interests": ["phân tích dữ liệu"],
        "constraints": {
            "region_pref": "danang",
            "study_budget": None,
            "study_duration_pref": None,
            "notes": "",
        },
        "evidence_quotes": [
            {
                "turn": 2,
                "quote": "em đã làm dashboard bán hàng bằng Excel",
                "mapped_to": "phan_tich",
            }
        ],
        "experiences": [
            {
                "title": "Dashboard bán hàng",
                "kind": "project",
                "description": "dashboard từ dữ liệu mở",
                "skills": ["Excel"],
                "source_quote": "em đã làm dashboard bán hàng bằng Excel",
            }
        ],
        "completeness": 0.7,
    }
    profile = Profile.model_validate(example)
    assert profile.journey_mode == "launch"
    assert profile.experiences[0].kind == "project"


def test_profile_patch_tracks_null_clear_fields() -> None:
    patch = ProfilePatch.model_validate(
        {"education_stage": None, "job_goal": None}
    )
    assert "education_stage" in patch.model_fields_set
    assert "job_goal" in patch.model_fields_set
    assert patch.education_stage is None
    assert patch.job_goal is None


def test_profile_patch_omit_does_not_mark_nullable_fields() -> None:
    patch = ProfilePatch.model_validate({"add_interests": ["thiết kế"]})
    assert "education_stage" not in patch.model_fields_set
    assert "job_goal" not in patch.model_fields_set
    assert patch.add_interests == ["thiết kế"]


def test_experience_kind_rejects_unknown() -> None:
    with pytest.raises(ValidationError):
        ExperienceEvidence(
            title="x",
            kind="not-a-real-kind",  # type: ignore[arg-type]
            source_quote="quote",
        )
```

- [ ] **Step 2: Run unit tests**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass/backend
python -m pytest -q tests/unit/test_profile_contract.py
```

Expected: all PASS. If FAIL due to schema drift, fix in Task 5 then re-run (do not delete tests).

- [ ] **Step 3: Commit**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass
git add backend/tests/unit/test_profile_contract.py
git commit -m "test(backend): expand PR-01 profile contract unit coverage"
```

---

### Task 3: Contract tests — OpenAPI + field sets

**Files:**
- Modify: `backend/tests/contract/test_schema_contract.py`

**Interfaces:**
- Consumes: FastAPI `app.openapi()`, `Profile`, `ProfilePatch`, `ChatResponse`, `RecommendationResponse`, `Recommendation`
- Produces: OpenAPI ethics + frozen field assertions

- [ ] **Step 1: Extend contract tests**

Replace file with:

```python
import pytest

from app.main import app
from app.models.schemas import (
    ChatResponse,
    Profile,
    ProfilePatch,
    Recommendation,
    RecommendationResponse,
)


pytestmark = pytest.mark.contract

FORBIDDEN = {
    "gender",
    "sex",
    "name",
    "full_name",
    "school",
    "school_name",
    "school_prestige",
    "gpa",
    "email",
    "phone",
}


def test_core_response_models_keep_expected_top_level_fields() -> None:
    assert set(ChatResponse.model_fields) == {"reply", "phase", "turn", "done", "profile"}
    assert set(RecommendationResponse.model_fields) == {
        "generated_at",
        "disclaimer",
        "recommendations",
        "stretch",
    }
    assert "job_readiness" in Recommendation.model_fields


def test_openapi_profile_matches_ethics_boundary() -> None:
    schemas = app.openapi()["components"]["schemas"]
    profile_schemas = [
        schema
        for name, schema in schemas.items()
        if name == "Profile" or name.startswith("Profile-")
    ]

    assert profile_schemas
    for profile_schema in profile_schemas:
        props = set(profile_schema.get("properties", {}))
        assert props == set(Profile.model_fields)
        assert FORBIDDEN.isdisjoint(props)


def test_openapi_profile_patch_has_no_forbidden_fields() -> None:
    schemas = app.openapi()["components"]["schemas"]
    patch_schemas = [
        schema
        for name, schema in schemas.items()
        if name == "ProfilePatch" or name.startswith("ProfilePatch-")
    ]
    assert patch_schemas
    for schema in patch_schemas:
        props = set(schema.get("properties", {}))
        assert props == set(ProfilePatch.model_fields)
        assert FORBIDDEN.isdisjoint(props)
```

- [ ] **Step 2: Run contract tests**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass/backend
python -m pytest -q tests/contract/test_schema_contract.py
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass
git add backend/tests/contract/test_schema_contract.py
git commit -m "test(backend): lock OpenAPI profile freeze for PR-01"
```

---

### Task 4: Integration tests — Explore default + PATCH null clear

**Files:**
- Modify: `backend/tests/integration/test_api_smoke.py`
- Modify if needed: `backend/app/routers/chat.py` (only if PATCH/default fails)

**Interfaces:**
- Consumes: `TestClient` fixture from `backend/tests/conftest.py`
- Produces: HTTP-level DoD for backward-compatible Explore and Launch PATCH clear

- [ ] **Step 1: Append integration tests** (keep existing tests)

Add to `backend/tests/integration/test_api_smoke.py`:

```python
def test_chat_omitting_journey_mode_defaults_to_explore(client: TestClient) -> None:
    response = client.post(
        "/api/chat",
        json={"session_id": "explore-compat", "message": None},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["journey_mode"] == "explore"
    assert "gender" not in body["profile"]


def test_patch_null_clears_launch_optional_fields(client: TestClient) -> None:
    # Opening launch has nulls; second turn mock may fill stage/goal — clear them via PATCH.
    open_resp = client.post(
        "/api/chat",
        json={
            "session_id": "patch-clear",
            "message": None,
            "journey_mode": "launch",
        },
    )
    assert open_resp.status_code == 200

    # Advance one turn so stub may populate education_stage/job_goal (turn >= 2).
    client.post(
        "/api/chat",
        json={
            "session_id": "patch-clear",
            "message": "Em năm cuối, muốn làm data entry-level",
            "journey_mode": "launch",
        },
    )

    patch_resp = client.patch(
        "/api/profile/patch-clear",
        json={"education_stage": None, "job_goal": None},
    )
    assert patch_resp.status_code == 200
    profile = patch_resp.json()["profile"]
    assert profile["education_stage"] is None
    assert profile["job_goal"] is None
    assert profile["journey_mode"] == "launch"
```

- [ ] **Step 2: Run integration tests**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass/backend
python -m pytest -q tests/integration/test_api_smoke.py
```

Expected: PASS.

If `test_patch_null_clears_launch_optional_fields` fails because stub regenerates filled values after patch incorrectly, apply **minimal** fix in `backend/app/routers/chat.py` `patch_profile`: keep using `model_fields_set` for null clear (already present). If advance turn does not fill stage, adjust test to first PATCH set values then clear:

```python
    client.patch(
        "/api/profile/patch-clear",
        json={
            "education_stage": "final_year",
            "job_goal": "data entry-level",
        },
    )
    patch_resp = client.patch(
        "/api/profile/patch-clear",
        json={"education_stage": None, "job_goal": None},
    )
```

Note: current stub does **not** persist patches into `_sessions`; it rebuilds mock then applies patch once for the response. That is acceptable for PR-01 if the response after a single PATCH shows null. Do not implement SQLite.

- [ ] **Step 3: Commit**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass
git add backend/tests/integration/test_api_smoke.py backend/app/routers/chat.py
git commit -m "test(backend): PR-01 explore default and patch null smoke"
```

---

### Task 5: Fix drift only (schemas / types / mocks / contract comments)

**Files (only if audit or tests failed):**
- Modify: `backend/app/models/schemas.py`
- Modify: `frontend/types/index.ts`
- Modify: `frontend/lib/mock/profile.ts` / `chat.ts` / `recommendations.ts`
- Modify: `docs/API_CONTRACT.md` (comments only preferred)
- Modify: `backend/app/routers/chat.py` (minimal)

**Interfaces:**
- Consumes: frozen field sets
- Produces: three-way + mock parity PASS

- [ ] **Step 1: If all Task 2–4 tests already pass and audit was PASS, skip code changes**

Record in handoff: "No schema drift; tests locked freeze."

- [ ] **Step 2: If drift exists, fix all sources in one commit**

Rules:

1. Match `docs/API_CONTRACT.md` first.
2. Update `schemas.py` and `types/index.ts` together.
3. Update mocks to still typecheck and keep Explore + Launch shapes.
4. Never add forbidden fields.
5. Never enable `extra="forbid"`.

- [ ] **Step 3: Re-run affected tests**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass/backend
python -m pytest -q tests/unit/test_profile_contract.py tests/contract/test_schema_contract.py tests/integration/test_api_smoke.py
```

Expected: PASS.

- [ ] **Step 4: Commit only if files changed**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass
git add docs/API_CONTRACT.md backend/app/models/schemas.py frontend/types/index.ts frontend/lib/mock backend/app/routers/chat.py
git commit -m "fix(contract): align profile freeze sources for PR-01"
```

---

### Task 6: Static validate — compileall + FE typecheck

**Files:**
- None (verify only)

**Interfaces:**
- Consumes: current tree
- Produces: static evidence for handoff

- [ ] **Step 1: Backend compileall**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass/backend
python -m compileall app scripts tests
```

Expected: exit code 0.

- [ ] **Step 2: Full unit + contract + integration gates used by PR-01**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass/backend
python -m pytest -q tests/unit tests/contract tests/integration
```

Expected: all PASS (or document any pre-existing unrelated failures separately — do not skip PR-01 failures).

- [ ] **Step 3: Frontend typecheck**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass/frontend
# install only if node_modules missing
test -d node_modules || npm install
npm run typecheck
```

Expected: exit code 0. If environment lacks Node, record `typecheck=NOT_RUN` with reason in handoff; backend tests still required PASS.

- [ ] **Step 4: Commit nothing if no files changed**

---

### Task 7: Docs handoff — workstream + status

**Files:**
- Modify: `docs/workstreams/M4_PROFILE_RECOMMENDER.md` (PR-01 section)

**Interfaces:**
- Consumes: test evidence from Task 6
- Produces: consumer-ready handoff block for M5/M1

- [ ] **Step 1: Update PR-01 card in workstream**

Under `### PR-01 — Profile/Launch contract freeze`, append (or replace bullets with status block):

```markdown
#### Status (M4)
- **State:** DONE (freeze locked by tests) | or CODE_COMPLETE_NOT_VERIFIED
- **Commit:** <sha after final commit>
- **Contract version label:** Profile/Launch v1 (API_CONTRACT Profile schema)

#### Verify evidence
- `python -m compileall app scripts tests` → PASS|FAIL
- `pytest -q tests/unit/test_profile_contract.py` → PASS|FAIL
- `pytest -q tests/contract/test_schema_contract.py` → PASS|FAIL
- `pytest -q tests/integration/test_api_smoke.py` → PASS|FAIL
- `npm run typecheck` (frontend) → PASS|FAIL|NOT_RUN

#### Handoff → M5 / M1
```md
[HANDOFF] PR-01 — M4 → M5/M1
- Artifact/PR: feat/PR-01-profile-contract-freeze; schemas.py + types/index.ts + mocks + tests
- Contract/version: API_CONTRACT Profile v1 frozen (journey_mode, education_stage, job_goal, experiences; no gender)
- Chạy thử:
  - backend: `cd backend && python -m pytest -q tests/unit/test_profile_contract.py tests/contract/test_schema_contract.py tests/integration/test_api_smoke.py`
  - frontend: `cd frontend && npm run typecheck`
- Test evidence: unit/contract/integration = PASS; typecheck = ...
- Input → output mẫu: ChatRequest omit journey_mode → profile.journey_mode=explore; Launch opening keeps education_stage/job_goal null
- Known limitations:
  1. PATCH not SQLite-persistent across process restart (PR-03)
  2. No real adaptive profiler/LLM (PR-02/PR-03)
  3. Stub may not persist multi-step patch chains in memory beyond single response (PR-03)
- Người nhận đã chạy và phản hồi: ⬜
```

#### Cannot do in PR-01 / deferred
- PR-02 prompts, PR-03 session engine, PR-05+ matching/evidence/readiness logic, PR-12+ agent runtime
```

Fill real PASS/FAIL and commit SHA after Task 8.

- [ ] **Step 2: Commit docs**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass
git add docs/workstreams/M4_PROFILE_RECOMMENDER.md
git commit -m "docs(m4): handoff PR-01 profile contract freeze"
```

---

### Task 8: Final verification + freeze commit polish

**Files:**
- Possibly touch handoff SHA lines only

- [ ] **Step 1: Run full PR-01 verification matrix**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass/backend
python -m compileall app scripts tests
python -m pytest -q tests/unit/test_profile_contract.py tests/contract/test_schema_contract.py tests/integration/test_api_smoke.py

cd ../frontend
npm run typecheck
```

- [ ] **Step 2: Update workstream evidence lines with actual results + `git rev-parse --short HEAD`**

- [ ] **Step 3: Final commit if docs updated**

```bash
cd /home/ilovekaguya/hackathon/TitanHack_Careercompass
git add docs/workstreams/M4_PROFILE_RECOMMENDER.md
git commit -m "docs(m4): record PR-01 verify evidence"
```

- [ ] **Step 4: Show status for PR**

```bash
git log --oneline kaguya..HEAD
git status
```

Do **not** push or open GitHub PR unless user asks.

---

## Plan self-review

### Spec coverage

| Spec requirement | Task |
|---|---|
| Three-way + mock sync | Task 1 audit, Task 5 fix |
| Explore default omit journey_mode | Task 2 unit + Task 4 integration |
| No forbidden fields / ethics | Task 2 + Task 3 |
| Launch optional fields present | Task 2 launch example parse |
| PATCH omit vs null | Task 2 unit + Task 4 integration |
| Tests unit/contract/integration | Tasks 2–4 |
| compileall + typecheck | Task 6 |
| Handoff + limitations + deferred | Task 7–8 |
| Non-goals (no PR-02/03/agent) | Global Constraints + Task 5 rules |

### Placeholder scan

No TBD steps; test code and commands are complete. Drift fix is conditional but with explicit rules.

### Type consistency

Field sets match design inventory and Global Constraints throughout Tasks 2–4.

---

## Execution handoff

After this plan is saved, implementers should use:

1. **Subagent-Driven (recommended)** — `superpowers:subagent-driven-development`
2. **Inline Execution** — `superpowers:executing-plans`

Do not start coding until the owner picks an execution mode (or says “implement now” with a mode).
