# M4 — Conversational Profile, Matching, Explainability, Ethics

**Mission:** tạo profile có evidence và recommendation mở rộng cơ hội; cùng core phục vụ Explore và Launch.

**Owned:** profiler state/session, prompts, matching, evidence, pathways/readiness, recommend router. **Buddy:** M3.

## Card contract

Mỗi task phải có problem, action, expected artifact, tests, risk/fallback và handoff. Agent task
phải thêm allowlist/policy/trace/replay fields trong `AGENT_WORKFLOW.md`; mọi recommendation và
ethics invariant vẫn do deterministic code sở hữu.

## Task cards

### PR-01 — Profile/Launch contract freeze (H+0→3)
- **Actions:** review Profile fields với M5; optional journey/education/experience; no gender/name/school prestige; patch semantics.
- **Expected:** contract + Pydantic + TS + mock đồng bộ; Explore default backward-compatible.
- **Tests:** schema examples parse; old Explore request still works; no forbidden fields.
- **Handoff:** contract v1 → M5/M1.

#### Status (M4)
- **State:** DONE (freeze locked by tests)
- **Commit:** 36c64ab / 15fa92e / 928737a (tests) + afcfd23 (handoff) + this verify-evidence commit
- **Contract version label:** Profile/Launch v1 (API_CONTRACT Profile schema)

#### Verify evidence
- `python -m compileall app scripts tests` → PASS
- `pytest -q tests/unit/test_profile_contract.py` → PASS (12)
- `pytest -q tests/contract/test_schema_contract.py` → PASS (3)
- `pytest -q tests/integration/test_api_smoke.py` → PASS (7)
- full unit+contract+integration → **22 passed** (12+3+7)
- `npm run typecheck` (frontend) → PASS

#### Handoff → M5 / M1
```md
[HANDOFF] PR-01 — M4 → M5/M1
- Artifact/PR: feat/PR-01-profile-contract-freeze; schemas.py + types/index.ts + mocks + tests
- Contract/version: API_CONTRACT Profile v1 frozen (journey_mode, education_stage, job_goal, experiences; no gender)
- Chạy thử:
  - backend: `cd backend && python -m pytest -q tests/unit/test_profile_contract.py tests/contract/test_schema_contract.py tests/integration/test_api_smoke.py`
  - frontend: `cd frontend && npm run typecheck`
- Test evidence: unit/contract/integration = PASS (22); typecheck = PASS; compileall = PASS
- Input → output mẫu: ChatRequest omit journey_mode → profile.journey_mode=explore; Launch opening keeps education_stage/job_goal null
- Known limitations:
  1. PATCH not SQLite-persistent across process restart (PR-03)
  2. No real adaptive profiler/LLM (PR-02/PR-03)
  3. Stub may not persist multi-step patch chains in memory beyond single response (PR-03)
- Người nhận đã chạy và phản hồi: ⬜
```

#### Cannot do in PR-01 / deferred
- PR-02 prompts, PR-03 session engine, PR-05+ matching/evidence/readiness logic, PR-12+ agent runtime

### PR-02 — Adaptive prompts for two modes (H+2→8)
- **Actions:** shared tone/safety; Explore asks activities/abilities/constraints; Launch asks projects/internships/tools/job goal; one question/turn.
- **Expected:** versioned prompts + 3 Explore/3 Launch transcripts; structured delta.
- **Tests:** no repeated question; no gender; handles “không biết”, stereotype, no experience, prompt injection.
- **Fallback:** deterministic question bank per phase/mode.

#### Status (M4)
- **State:** DONE (prompts + delta + fixtures locked offline)
- **Prompt version:** `profiler-v2`
- **Commit:** `41f489f` (impl) + `c5c6968` (design/plan)

#### Verify evidence
- `python -m compileall app scripts tests` → PASS
- `pytest -q tests/unit/test_profiler_io.py tests/unit/test_profiler_prompts.py tests/unit/test_profiler_transcripts.py` → PASS
- full `pytest -q tests/unit tests/contract tests/integration` → PASS (42 on this branch base)

#### Handoff → PR-03 / M1
```md
[HANDOFF] PR-02 — M4 → PR-03 (self) / M1 note
- Artifact: app/prompts/profiler.py (v2), app/models/profiler_io.py, tests/fixtures/profiler/*.json
- Contract/version: prompt_version=profiler-v2; internal ProfilerTurnOutput (not public API)
- Chạy thử:
  - `cd backend && python -m pytest -q tests/unit/test_profiler_io.py tests/unit/test_profiler_prompts.py tests/unit/test_profiler_transcripts.py`
- Test evidence: unit IO/prompts/transcripts PASS; suite unit+contract+integration PASS
- Input → output mẫu: build_profiler_system("launch","abilities"); get_fallback_question rotation; 6 fixtures parse as ProfilerTurnOutput
- Known limitations:
  1. Not wired into /api/chat or SQLite session (PR-03)
  2. Transcripts are fictional static fixtures — not live LLM eval (PR-11/PR-14)
  3. Merge/completeness/correction precedence still PR-03
- Người nhận đã chạy và phản hồi: ⬜
```

#### Cannot do in PR-02 / deferred
- PR-03 session engine + chat stub replacement
- Live model transcript scoring
- Agent graph (PR-12+)

### PR-03 — Profiler/session engine (H+8→16)
- **Actions:** deterministic phase state; completeness rules by mode; merge validated deltas; experience evidence; SQLite sessions; patch/delete.
- **Expected:** `/chat` 10 turns, profile persistence/edit, mode locked after opening.
- **Tests:** unit merge/completeness; 10-turn E2E each mode; retry≤2; model timeout fallback; restart persistence; delete.
- **Risk:** LLM overwrites evidence → code merge allowlist; preserve user corrections.

#### Status (M4)
- **State:** DONE (deterministic path + SQLite sessions; LLM optional when `CHAT_API_KEY` set)
- **Branch:** `feat/PR-03-profiler-session-engine` (merge into `kaguya`)

#### Verify evidence
- `python -m compileall app tests` → PASS
- `pytest -q tests/unit tests/contract tests/integration` → PASS (76)
- Unit: merge/corrections/completeness/phase/injection (`test_profiler_engine.py`)
- Integration: mode lock, patch persist, delete, 10-turn Explore/Launch, correction precedence

#### Handoff → M5 / M1 (PR-04 prep)
```md
[HANDOFF] PR-03 — M4 → M5/M1
- Artifact: services/profiler.py, session_store.py, session_orm.py, routers/chat.py (wired)
- Sessions: SQLite `sessions.db` via SESSIONS_DB_URL
- Chạy thử:
  - `cd backend && uvicorn app.main:app --reload --port 8000`
  - `cd backend && python -m pytest -q tests/integration/test_profiler_session.py`
- Behavior: mode locked on open; PATCH/GET persist; DELETE /api/profile/{id}; no LLM required for demo (deterministic extractor + question bank)
- Known limitations:
  1. Deterministic extractor is keyword-based (quality << live LLM)
  2. DELETE /api/profile is additive (not yet in API_CONTRACT.md prose — M1 may document)
  3. Agent graph still PR-12/13; this is deterministic profiler core
- Người nhận: ⬜
```

#### Cannot do / deferred
- Live LLM quality transcripts (needs keys + PR-02 prompts already wired)
- LangGraph agent (PR-12/13)
- Formal M5/M1 consumer ack (see PR-04 handoff doc)

### PR-04 — Chat handoff (H+16)
- **Actions:** deploy sample Explore/Launch, request/response, latency/error/fallback notes.
- **Expected:** M5 integrates; M1 records replay immediately.
- **Verify:** consumer runs both modes and patch; contract/OpenAPI matches.

#### Status (M4)
- **State:** DONE
- **Handoff doc:** `docs/handoffs/M4_PR-04_CHAT_HANDOFF.md`
- **Samples:** `backend/app/data/replay/explore_sample_session.json`, `launch_sample_session.json`

#### Verify evidence
- `pytest -q tests/contract/test_chat_handoff_samples.py` → PASS
- full unit/contract/integration suite → PASS
- Capture: `PYTHONPATH=. python scripts/capture_chat_samples.py`

#### Handoff → M5 / M1
See full template in `docs/handoffs/M4_PR-04_CHAT_HANDOFF.md` (curl, latency, errors, fallback, consumer checklist).

#### Cannot do / deferred
- Full `DEMO_MODE=replay` router short-circuit (M1 L-08 uses samples as seed)
- Live LLM persona polish (needs keys; quality PR-10/11)

### PR-05 — Explainable matching (H+20→26)
- **Actions:** cosine candidate retrieval; weighted skill overlap; capped market signal; deterministic diversity/stretch; config thresholds.
- **Expected:** top 5 + stretch; region never filter; Launch uses evidence/project skill coverage.
- **Tests:** weight/unit; identical human profile different region keeps candidate set; market spike cannot dominate low fit; 12 personas rubric.
- **Fallback:** cosine + skill overlap only; market shown as information, not score.

#### Status (M4)
- **State:** DONE (seed KB + dim/cosine fallback; npy path ready when MI-06 lands)
- **Code:** `backend/app/services/matching.py`, `routers/recommend.py` wired

#### Verify evidence
- `pytest -q tests/unit/test_matching.py tests/integration/test_recommendations.py` → PASS
- full unit/contract/integration → PASS

#### Notes
- `profile_text` excludes region/gender; region only mild market boost, never filters candidate set
- Market contribution capped (`MARKET_SIGNAL_CAP=0.35`)
- Stretch = different dominant dimension outside top-5
- Launch `job_readiness` lite (matched needs evidence; actions present); PR-07 may polish
- 12-persona human rubric = PR-11/eval, not automated here

#### Cannot do / deferred
- Real embeddings until `data/processed/careers.npy` (MI-06)
- Live market.db stats until MI-04 (still seed_market)
- LLM evidence wording polish (PR-06)

### PR-06 — Grounded evidence + counterfactual (H+26→31)
- **Actions:** code selects quotes/stats; LLM verbalizes; digit/stat-key validator; counterfactual from rerun scoring; template fallback.
- **Expected:** why-from-you, why-from-market, true counterfactual, no unsupported claim.
- **Tests:** 100% number grounding; quote belongs session; null/low-confidence; injection; timeout.
- **Fallback:** deterministic Vietnamese templates.

#### Status (M4)
- **State:** DONE
- **Code:** `services/evidence.py`, `prompts/evidence.py` (v1); wired in `matching.build_recommendation`
- **Handoff:** `docs/handoffs/M4_PR-06_EVIDENCE_HANDOFF.md`

#### Verify evidence
- `pytest -q tests/unit/test_evidence.py tests/integration/test_evidence_grounding.py` → PASS
- full unit/contract/integration → PASS

#### Notes
- Digit grounding enforced on market stats text; salary/trend omitted when null/low-confidence/sample&lt;5
- Counterfactual from re-score (PR-05), not free prose
- LLM optional; template always safe for demo

#### Deferred
- PR-07 pathways/readiness polish
- Live market.db numbers (MI-04)

### PR-07 — Study pathways + Graduate Launch readiness (H+26→31)
- **Actions:** ≥2 study routes; Launch matched/missing skills, readiness band, search queries, 4 deliverable actions.
- **Expected:** Explore `job_readiness=null`; Launch object follows GRADUATE_LAUNCH.
- **Tests:** route script; missing∩matched empty; missing⊆role top skills; matched evidence trace; actions weeks 1–4 + deliverable.
- **Fallback:** deterministic roadmap from KB; no course/company names without source.

#### Status (M4)
- **State:** DONE
- **Code:** `backend/app/services/pathways.py` (wired from `matching.build_recommendation`)
- **Handoff:** `docs/handoffs/M4_PR-07_PATHWAYS_LAUNCH_HANDOFF.md`
- **Branch:** `feat/PR-07-pathways-launch-readiness` → merge `kaguya`

#### Verify evidence
- `pytest -q tests/unit/test_pathways.py tests/integration/test_launch_pathways.py` → PASS
- full unit/contract/integration → PASS
- `python scripts/check_routes.py` → PASS

#### Invariants locked
- Explore `job_readiness=null`; Launch matched evidence; missing⊆top_skills; 4 actions w/ deliverable
- Region does not change readiness band; market demand cannot inflate low-evidence band

### PR-08 — Bias/opportunity audit (H+31→35)
- **Actions:** gender paired, region paired, school-prestige mention ignored, route/stretch coverage, prompt audit.
- **Expected:** real `BIAS_AUDIT.md`, failures/fixes/retest.
- **Tests:** top-5 overlap ≥4/5 gender; region candidate set not poorer; readiness unchanged by gender/school name.
- **Fallback:** remove offending field/weight/copy; do not lower threshold.

#### Status (M4)
- **State:** DONE
- **Report:** `docs/BIAS_AUDIT.md` (real PASS tables)
- **Tests:** `backend/tests/unit/test_bias_audit.py`
- **Handoff:** `docs/handoffs/M4_PR-08_BIAS_AUDIT_HANDOFF.md`
- **Code harden:** `matching.sanitize_scoring_text` strips gender/school prestige from ranking text

#### Verify evidence
- `pytest -q tests/unit/test_bias_audit.py` → PASS
- `python scripts/check_routes.py` → PASS
- full unit/contract/integration → PASS

### PR-09 — Transparency copy (H+35→36)
- **Actions:** explain data, mode, scoring, demand proxy, limits, autonomy, readiness meaning.
- **Expected:** ≤300 words main page + tooltips; student-readable Vietnamese.
- **Verify:** 2 outsiders paraphrase correctly; no “AI knows best/guaranteed job”.

#### Status (M4)
- **State:** DONE (copy + page wire + automated gates; human 2-outsider paraphrase ⬜)
- **Source of truth:** `frontend/lib/copy/transparency.ts` (`transparency-v1`)
- **Page:** `frontend/app/how-it-works/page.tsx`
- **Docs mirror:** `docs/copy/M4_transparency_vi.md`
- **Handoff:** `docs/handoffs/M4_PR-09_TRANSPARENCY_COPY_HANDOFF.md`

#### Verify evidence
- `pytest -q tests/unit/test_transparency_copy.py` → PASS
- `cd frontend && npm run typecheck` → PASS
- full backend unit/contract/integration → PASS


### PR-10 — Quality tuning only (H+34→40)
- **Actions:** fix labeled issues from E2E/user test; prompt/config changes one at a time; rerun gold personas.
- **Expected:** no open Sev-1/2 `ai-quality`; before/after evidence.
- **Forbidden:** new model/feature/contract after freeze without M1.

### PR-11 — AI evaluation report (H+35→38)
- **Actions:** profiler validity, persona rubric, grounding, readiness invariants, latency/cost, paired bias.
- **Expected:** actual metrics + commit/model/prompt/artifact versions in `EVALUATION_RESULTS.md`.
- **Verify:** M3/M1 reproduce sample; no cherry-pick.

### PR-12 — LangChain tool layer + LangGraph spike + bounded policy registry (H+4→12)
- **Problem:** Flow hỏi đáp không được hard-code kịch bản, nhưng agent tự do sẽ không test/replay/bảo vệ được ethics.
- **Actions:** đọc ADR/TESTING; verify pinned LangChain/LangGraph install và `llm.py` gateway; timebox 90' tạo custom StateGraph fake structured planner → policy → fake LangChain tool → fallback. Sau đó tạo `agent_graph.py`/`agent_policy.py`/`agent_tools.py`, `@tool(args_schema=PydanticModel)`, stage allowlist, planner schema, pre/post policy privacy/provenance/autonomy/cost.
- **Expected:** LangChain chỉ model/tool/structured contracts; LangGraph chỉ orchestration chat; registry 10 local typed tools; policy decision/reason code; không `create_agent`, prebuilt ReAct, LangSmith service/checkpointer/browser/shell/arbitrary HTTP/config/KB write.
- **Tests:** gateway fake structured-output; tool JSON schema; graph compile/invoke offline; overhead <100ms p95/100 fixtures; deterministic mode không compile/invoke graph; tool stage matrix; unknown tool/invalid args; gender/school strip; budget/deadline; provenance; correction precedence. Đặt đúng `tests/unit|contract|integration`.
- **Risk/fallback:** graph spike fail → plain Python bounded orchestrator dùng cùng LangChain gateway/tool contracts. Planner lỗi hoặc policy deny hai lần → deterministic question/template, không loop.
- **Handoff:** tool schemas + policy matrix + sample observation cho M3/M5/M6/M1.

### PR-13 — LangChain/LangGraph chat agent orchestrator + degradation (H+16→22)
- **Problem:** Tool registry chỉ có giá trị nếu request path ghép được plan → policy → observation → response một cách có giới hạn.
- **Actions:** tích hợp custom StateGraph vào `/api/chat` chỉ ở `discover/confirm_profile`; planner/composer gọi LangChain gateway, tool dùng typed registry; tối đa 2 agent-selected tools/turn; truyền deadline 8s qua nodes; sanitize trace; map stage về `phase`; recommendation deterministic; không expose CoT.
- **Expected:** Explore/Launch chat dùng chung graph; API không đổi; `DEMO_MODE=replay` không network/key; session canonical ở SQLAlchemy, không graph checkpointer.
- **Tests:** unit node routing/deadline; contract tool/API shapes; integration 10-turn mỗi mode; timeout/invalid structured output/tool exception; deterministic mode; no raw transcript/CoT; trace versions/latency/fallback; recommendation has no planner; E2E replay do M1 nhận.
- **Risk/fallback:** `AGENT_MODE=deterministic` quay về question bank; retrieval/ranking luôn deterministic PR-05.
- **Handoff:** endpoint behavior + replay trace fixture cho M1/M5/M6.

### PR-14 — Agent evaluation/red-team (H+31→38)
- **Problem:** Agentic chỉ là claim mạnh khi chứng minh được tool choice, safety và fallback, không chỉ có demo đẹp.
- **Actions:** chạy tool-selection fixtures, prompt injection, 12 personas, gender/region/school pairs, missing provenance, budget/latency, replay; ghi failures/fix/retest.
- **Expected:** `EVALUATION_RESULTS.md` có model/prompt/tool/policy/snapshot versions, calls/turn, p95, pass/fail, limitation.
- **Tests:** toàn bộ bảng §8 `AGENTIC_RUNTIME.md`; fail không được xoá fixture hay nới threshold.
- **Handoff:** scorecard/pitch evidence cho M1; M1 xác nhận deterministic replay.

## Hard-stop rules

- No recommendation if profile completeness below mode threshold; ask/correct instead.
- No exact readiness probability, hiring prediction or personal salary prediction.
- User correction outranks model inference.
- LLM never selects candidates or invents requirements; code/data do.
- Agent chỉ chọn tool trong allowlist; policy code, không phải prompt, là authority cuối.
