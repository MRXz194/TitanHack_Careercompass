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
