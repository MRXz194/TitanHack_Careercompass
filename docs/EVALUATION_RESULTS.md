# EVALUATION RESULTS — điền số thật, không cherry-pick

> Status: `NOT_RUN`. M1 đổi thành `PASS | CONDITIONAL | FAIL` tại H+42. Không đưa placeholder lên slide như kết quả thật.

## Snapshot

| Field | Value |
|---|---|
| Commit SHA | TBD |
| Dataset hash / built_at | `192e492fa2984f908525ac556a893767ab19a431831e7ea144558d0f8383a430` / `2026-07-17` |
| Postings / sources / regions | 298 / topcv, vietnamworks, itviec / hanoi, hcm, danang, other |
| Career KB / taxonomy version | 25 careers / skills_vi_v1.0 |
| Chat model / embed model | `deepseek-v4-flash` / `text-embedding-3-small` |
| Agent engine / versions | `deterministic|langgraph`; LC Core `1.4.9`, LC OpenAI `1.3.5`, LangGraph `1.2.9` |

## Metrics

| Gate | Target | Actual | Pass? | Evidence |
|---|---:|---:|---|---|
| Skill precision / recall / F1 | ≥.80 / ≥.65 / ≥.70 | NOT_RUN | ⬜ | |
| Career mapping accuracy (n=50) | report | NOT_RUN | ⬜ | |
| Profiler valid JSON after retry | ≥99% | NOT_RUN | ⬜ | |
| Agent stage/tool allowlist + ≤2 tools/turn | 100% | NOT_RUN | ⬜ | PR-12/14 fixtures |
| Agent deny/timeout → fallback, session preserved | 100% | NOT_RUN | ⬜ | PR-13 failure matrix |
| LangGraph overhead p95 (no model, n=100) | <100ms | NOT_RUN | ⬜ | |
| Recommendation rubric (n=12) | ≥3.5/5 | NOT_RUN | ⬜ | |
| Launch readiness invariants (n=4) | 100% | NOT_RUN | ⬜ | |
| Evidence number grounding | 100% | NOT_RUN | ⬜ | |
| Route structural check | 100% | 100% | ✅ | check_routes.py |
| Gender paired top-5 overlap | ≥4/5 | NOT_RUN | ⬜ | `BIAS_AUDIT.md` |
| Chat / recommendation p95 | <5s / <8s | NOT_RUN | ⬜ | |
| 3 E2E + replay | 0 unhandled 5xx | NOT_RUN | ⬜ | |
| Student usefulness (n≥5) | median ≥4/5 | NOT_RUN | ⬜ | anonymized notes |
| Launch: ≥2 new job queries + actionable first step | ≥60% launch testers | NOT_RUN | ⬜ | |

## Failures, fixes, limitations

| Failure/limitation | Impact | Fix/fallback | Owner/status |
|---|---|---|---|
| Posting data measures demand, not labor supply | Không kết luận shortage | UI/pitch ghi hiring-demand proxy | M3/M6 |
| | | | |

## Release decision

- P0 demo: ⬜ PASS / ⬜ FAIL
- Live mode: ⬜ allowed / ⬜ replay only
- Claims removed from pitch: TBD
- M1 sign-off + time: TBD
