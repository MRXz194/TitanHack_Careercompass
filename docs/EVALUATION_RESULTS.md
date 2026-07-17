# EVALUATION RESULTS — điền số thật, không cherry-pick

> Status: `NOT_RUN`. M1 đổi thành `PASS | CONDITIONAL | FAIL` tại H+42. Không đưa placeholder lên slide như kết quả thật.

## Snapshot

| Field | Value |
|---|---|
| Commit SHA | TBD |
| Dataset hash / built_at | TBD |
| Postings / sources / regions | TBD |
| Career KB / taxonomy version | TBD |
| Chat model / embed model | `deepseek-v4-flash` / `text-embedding-3-small` |

## Metrics

| Gate | Target | Actual | Pass? | Evidence |
|---|---:|---:|---|---|
| Skill precision / recall / F1 | ≥.80 / ≥.65 / ≥.70 | NOT_RUN | ⬜ | |
| Career mapping accuracy (n=50) | report | NOT_RUN | ⬜ | |
| Profiler valid JSON after retry | ≥99% | NOT_RUN | ⬜ | |
| Recommendation rubric (n=12) | ≥3.5/5 | NOT_RUN | ⬜ | |
| Evidence number grounding | 100% | NOT_RUN | ⬜ | |
| Route structural check | 100% | NOT_RUN | ⬜ | |
| Gender paired top-5 overlap | ≥4/5 | NOT_RUN | ⬜ | `BIAS_AUDIT.md` |
| Chat / recommendation p95 | <5s / <8s | NOT_RUN | ⬜ | |
| 3 E2E + replay | 0 unhandled 5xx | NOT_RUN | ⬜ | |
| Student usefulness (n≥5) | median ≥4/5 | NOT_RUN | ⬜ | anonymized notes |

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
