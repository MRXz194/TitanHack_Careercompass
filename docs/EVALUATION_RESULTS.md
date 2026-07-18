# EVALUATION RESULTS — release integrity v2

> Baseline: commit `99f463e` on 2026-07-18. Current branch adds release-integrity fixes; local full gates pass, CI for the new commit is pending until push. Không đổi `NOT_RUN` thành PASS nếu chưa có bằng chứng.

| Field | Value |
|---|---|
| Commit SHA | `99f463e` |
| Tool policy / registry | `agent-policy-v1` / `agent-tools-v2-research` |

Không cherry-pick chỉ số đẹp: automated proxy, live test và human test được báo thành các nhóm riêng.

## Automated evidence

| Gate | Current evidence | Status |
|---|---|---|
| Baseline backend CI | 285/285 tests passed on Python 3.11; compile + route check passed | PASS at `99f463e` |
| Baseline frontend | 61/61 Vitest, typecheck, Next production build | PASS locally at `99f463e` |
| Current backend local | compile/import; 262 unit+contract; 29 integration; 2 E2E; route check 25/25 | PASS on Python 3.11.9 |
| Current frontend local | 61 Vitest; typecheck; Next production build 8/8 pages | PASS on Node 24 (CI remains Node 20) |
| Release E2E | Explore/LangGraph + correction + recommend + market; Launch/replay + readiness; added to CI | 2/2 PASS local, PENDING CI |
| Agent policy/red-team | allowlist, budget, injection, sanitized trace suites from PR-12/13/14 | PASS at baseline |
| Route invariant | 25 careers; ≥2 routes and ≥1 vocational/college/certificate | PASS at baseline |
| Aggregate artifact | 43 `career_stats`, 548 `skill_stats`, 16 `market_meta`; no description column | PASS, inspected locally |
| Mapping coverage | 89/298 = 29,87% | MEASURED, not accuracy |
| Skill extraction coverage | 261/298 has ≥1 skill; live LLM success 0 | MEASURED_WITH_CAVEAT |
| Trend | no reliable two-window signal | Correctly `NULL` |

## Metrics

Các số latency dưới đây là evidence offline ở baseline `99f463e`, không phải đo provider live hoặc current-branch CI.

| Gate | Actual | Status |
|---|---:|---|
| evidence_number_grounding | automated suite passed | PASS baseline |
| launch_readiness_invariants | automated suite passed | PASS baseline |
| gender_paired_top5_overlap | paired bias suite passed | PASS baseline |
| route_structural | 25/25 careers pass | PASS baseline |
| chat_p95 | 8,8 ms offline deterministic | PASS baseline |
| recommendation_p95 | 7,3 ms offline deterministic | PASS baseline |
| agent_langgraph_gates | compile/invoke, deny/fallback and contract suite passed | PASS baseline |
| agent_tool_selection_allowlist | stage allowlist suite passed | PASS baseline |
| agent_prompt_injection | policy/tool scope unchanged in red-team fixtures | PASS baseline |
| agent_personas_n12 | 12 fictional personas passed bounded policy suite | PASS baseline |
| agent_orchestrator_p95 | 0,4 ms plain-Python baseline; LangGraph current E2E pending | PASS baseline / PENDING current |

## Human/live gates

| Gate | Target | Actual |
|---|---:|---|
| Skill extraction precision/recall/F1 | ≥0,80 / 0,65 / 0,70 | `NOT_RUN` — sanitized independent gold labels required |
| Career mapping accuracy | report denominator + accuracy | `NOT_RUN` — 50 independent labels required |
| Recommendation dual-rater rubric | mean ≥3,5/5 by ≥2 raters | `NOT_RUN` |
| Student usefulness | median ≥4/5, n≥5 | `NOT_RUN` |
| Counselor usefulness | qualitative + issue log | `NOT_RUN` |
| Live LLM Vietnamese/structured success | ≥80% valid after retry | `NOT_RUN` for current provider/key |

## Release claims

- Được claim: bounded LangGraph agent trên `/api/chat`, deterministic recommendation core, explainable evidence, anti-bias tests, real aggregate snapshot có caveat, replay safety net.
- Không claim: fully autonomous career-deciding agent, real-time market, proven labor shortage, production-grade extraction accuracy, hiring probability, human usefulness score.
- `AGENT_MODE=langgraph` là release path; `deterministic` là kill switch. `/api/recommendations` không có planner.

## Release decision

- Code local: `PASS`; current-commit CI/deploy: `PENDING` cho branch release-integrity v2.
- Live mode: chỉ bật sau deploy smoke test có `market_db_loaded=true`; nếu provider/network lỗi dùng `DEMO_MODE=replay`.
- Human validation: chưa chặn demo kỹ thuật nhưng phải nói rõ `NOT_RUN` và ưu tiên chạy nếu còn thời gian.
