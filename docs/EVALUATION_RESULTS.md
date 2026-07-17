# EVALUATION RESULTS — điền số thật, không cherry-pick

> Status: `M4_PARTIAL` — automated M4 gates measured at commit `1b83e6b`. M1 owns final PASS/CONDITIONAL/FAIL at release. Không đưa proxy như human score lên slide.

## Snapshot

| Field | Value |
|---|---|
| Commit SHA | `1b83e6b` |
| Career KB count | 25 |
| Profiler prompt | `profiler-v2` |
| Chat p95 (offline) | 8.2 ms |
| Recommendation p95 (offline) | 7.7 ms |
| Agent orchestrator p95 (offline) | 0.5 ms |
| Agent engine default | `deterministic` (langgraph optional; no planner on recommend) |
| Tool policy version | `agent-policy-v1` |
| Tool registry version | `agent-tools-v1` |
| Max agent tools / turn | 2 |
| Agent deadline | 8000 ms |

## Metrics

| Gate | Target | Actual | Pass? | Evidence |
|---|---:|---:|---|---|
| pytest:profiler_unit | all green | 44 passed in 0.38s | PASS | tests/unit/test_profiler_engine.py tests/unit/test_profiler_prompts.py tests/unit/test_profiler_transcripts.py tests/unit/test_quality_tuning.py |
| pytest:profiler_integration | all green | 15 passed in 0.46s | PASS | tests/integration/test_profiler_session.py tests/integration/test_quality_chat.py tests/integration/test_api_smoke.py |
| pytest:grounding | all green | 9 passed in 0.14s | PASS | tests/unit/test_evidence.py tests/integration/test_evidence_grounding.py |
| pytest:readiness | all green | 12 passed in 0.18s | PASS | tests/unit/test_pathways.py tests/integration/test_launch_pathways.py |
| pytest:bias | all green | 17 passed in 0.26s | PASS | tests/unit/test_bias_audit.py |
| pytest:matching | all green | 13 passed in 0.22s | PASS | tests/unit/test_matching.py tests/integration/test_recommendations.py |
| pytest:agent | all green | 61 passed in 0.87s | PASS | tests/unit/test_agent_policy.py tests/unit/test_agent_tools.py tests/unit/test_agent_graph.py tests/unit/test_agent_chat.py tests/unit/test_agent_redteam.py tests/contract/test_agent_tool_contract.py tests/integration/test_agent_chat_api.py |
| route_structural | 100% | 100% | PASS | scripts/check_routes.py |
| recommendation_rubric_automated_proxy_n12 | ≥3.5/5 human (proxy automated) | 4.25/5 mean criteria; hard_fail_personas=0 | PASS | 8 Explore + 4 Launch structural gold profiles |
| chat_p95 | <5000ms | 8.2ms (n=40, deterministic) | PASS | TestClient offline path |
| recommendation_p95 | <8000ms | 7.7ms (n=10, deterministic) | PASS | TestClient offline path |
| profiler_valid_structured_path | ≥99% JSON valid after retry | 100% offline structured/fixtures (no live LLM this run) | PASS | profiler unit+integration; live LLM NOT_RUN |
| evidence_number_grounding | 100% | 100% | PASS | test_evidence + test_evidence_grounding |
| launch_readiness_invariants | 100% | 100% | PASS | test_pathways + test_launch_pathways |
| gender_paired_top5_overlap | ≥4/5 | PASS suite | PASS | docs/BIAS_AUDIT.md + test_bias_audit |
| agent_tool_selection_allowlist | 100% stage allowlist | PASS suite | PASS | fixtures agent/allow|deny + test_agent_redteam + test_agent_policy |
| agent_prompt_injection | no policy/tool scope change | PASS suite | PASS | fixtures agent/injection + test_injection_* |
| agent_personas_n12 | ≤2 tools/turn; allowlist only | 12 personas offline | PASS | fixtures agent/personas/personas_12.json |
| agent_provenance_budget_replay | provenance + ≤2 tools + sanitized replay | PASS suite | PASS | fallback fixtures + app/data/replay/agent_sanitized_trace.json |
| agent_orchestrator_p95 | <100ms offline / <8000ms budget | 0.5ms (n=40, plain_python) | PASS | plain_python_orchestrator; LangGraph optional via AGENT_MODE |
| agent_langgraph_gates | 100% allowlist/fallback | PASS offline red-team; policy=agent-policy-v1; tools=agent-tools-v1; default_mode=deterministic | PASS | PR-12/13/14: tests/unit/test_agent_*.py + fixtures/agent; recommendation remains deterministic (no planner) |
| skill_extraction_prf | ≥.80/.65/.70 | NOT_RUN | N/A | Owner M3 — not M4 PR-11 |
| human_recommendation_rubric_dual_rater | ≥3.5/5 by ≥2 humans | NOT_RUN | NOT_RUN | Requires M3 dual human raters; automated proxy reported separately |
| student_usefulness_n5 | median ≥4/5 | NOT_RUN | N/A | Owner M1 user testing L-11 |

## Failures, fixes, limitations

| Failure/limitation | Impact | Fix/fallback | Owner/status |
|---|---|---|---|
| Posting data = demand proxy | Không claim shortage | UI Radar nhu cầu | M3/M6 |
| Live LLM profiler quality not measured this run | Chat quality offline-only | Keys + session sample later | M4 |
| Human dual-rater rubric NOT_RUN | Không claim ≥3.5 human | Automated proxy only | M4/M3 |
| Live agent planner LLM NOT_RUN | Không claim fully autonomous agent | Offline policy/red-team PASS; default AGENT_MODE=deterministic | M4 |
| User testing n≥5 N/A | Không claim usefulness median | M1 L-11 | M1 |

## Notes

- CHAT_API_KEY set=False; DEMO_MODE=off; AGENT_MODE default=deterministic; latency measured offline deterministic path only.
- Do not present automated rubric proxy as dual-human scores in pitch.
- Agent claim boundary: offline allowlist/policy/fallback/replay gates PASS; live multi-turn LLM planner NOT_RUN. Do not claim fully autonomous agent.

## Release decision (M1)

- P0 demo: ⬜ PASS / ⬜ FAIL
- Live mode: ⬜ allowed / ⬜ replay only
- Claims removed from pitch: TBD
- M1 sign-off + time: TBD

_Generated by `backend/scripts/run_m4_evaluation.py` at commit 1b83e6b._
