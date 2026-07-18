# Day 3 Release Scorecard

Baseline commit: `e76a0a919505e7d534153fd95f41b72e5abc7b10`  
Implementation branch: `codex/day3-opportunity-plan`  
Release candidate commit: `8f982fc`  
Expansion Gate: **FAIL — automated candidate ready, manual E2E/human gates remain**

## Automated evidence

| Gate | Actual | State | Evidence | Owner |
|---|---|---|---|---|
| Core regression | 347 backend tests; 64 frontend tests; TS typecheck + Next production build pass | PASS | `python -m pytest -q`; `npm test`; `npm run typecheck`; `npm run build` | M1 |
| Snapshot provenance | Manifest/card synchronized at 3.865 normalized rows; stable SHA-256 `4ecfc1…` | PASS | `data/processed/manifest.json`, `docs/DATA_SNAPSHOT.md` | M2 |
| Acquisition integrity | 3.914 unique raw records; raw/full text ignored; source limitations retained | PASS_WITH_CAVEATS | `DATA_SNAPSHOT_AUDIT.md` | M2 |
| Extraction held-out | Dictionary extraction ran on 3.865; held-out human F1 not rerun | NOT_RUN | `postings_enriched.report.json` | M2/M3 |
| Career mapping publish | 1.031/3.865 mapped; accuracy `NOT_RUN`; candidate DB removed and release DB unchanged | FAIL / BLOCKED | `postings_mapped.report.json` | M2/M3 |
| What-if isolation | Deep copy, one hypothetical skill, deterministic real scoring, original profile byte-stable, invalid input 422 | PASS | `test_what_if.py`, `test_recommendations.py` | M4 |
| Research isolation/citations/fallback | Typed 11th tool, policy stage, safe URLs, local/replay fallback, candidate/profile isolation | PASS | research unit/integration/contract tests | M4 |
| DuckDuckGo live gate | 7/10 queries with >=3 relevant safe links; p95 1.129s; rate-limit/empty on last 3 | FAIL | `python -m scripts.run_research_spike` | M4/M1 |
| UI/UX | Cream editorial system, serif/mono split, 2px geometry, compare/inspector/research/what-if, print stylesheet | PASS_AUTOMATED | Vitest/typecheck/build; visual human QA pending | M5/M6 |
| Explore/Launch/Replay E2E on deployed URLs | Backend is hosted on another machine; not run here | NOT_RUN | run `docs/DEPLOY.md` smoke matrix | M1 |
| Student usability | No fresh Day-3 participant session recorded | NOT_RUN | `docs/next/EVALUATION.md` U1–U6 | M1 |
| Counselor usefulness | Print flow exists; no counselor timing/feedback recorded | NOT_RUN | counselor protocol | M1/M5 |

## Task-to-plan implementation map

| Task | Current state | Delivered / remaining |
|---|---|---|
| N1-01 | PARTIAL | Automated test matrix and scorecard done; deployed E2E + human gate remain. |
| N1-02 | VERIFIED | BE/FE/mock/API contracts synchronized for What-if and Career Research. |
| N1-03 | NOT_RUN | User test, rehearsal and release sign-off require team/deployed URLs. |
| N2-01 | VERIFIED_WITH_CAVEATS | Deterministic normalize, atomic output, manifest dry-run, synchronized candidate reports. |
| N2-02/N2-03 | NOT_RUN | Held-out labels and route reviewer sign-off remain. |
| N3-01 | BLOCKED_PUBLISH | Candidate pipeline built; no `market.db` replacement before accuracy/region gates. |
| N3-02/N3-03 | NOT_RUN | No gold-label improvement loop or skill bridge shipped. |
| N4-01/N4-02 | VERIFIED_SUBSET | Safe add-skill What-if is implemented; broader mutation types intentionally cut. |
| N4-03 | PARTIAL | Equal-weight compare and grounded fields exist; counselor question model remains presentation-only. |
| N4-04 | PARTIAL | Existing red-team/agent suite passes; fresh Day-3 pair matrix not separately reported. |
| N4-05 | VERIFIED_FALLBACK | Agent tool/policy/replay complete; live DDG disabled because gate is 7/10. |
| N5-01/N5-02 | VERIFIED_SUBSET | Preview, delta and undo work; no confirm-to-profile from hypothetical evidence. |
| N5-03 | PARTIAL | Browser print brief works; confirmed-profile summary and counselor timing remain. |
| N6-01/N6-02 | VERIFIED_SUBSET | Compare and signal inspector render grounded recommendation/market fields. |
| N6-03 | VERIFIED_FALLBACK | Research cards support live/cached/replay/unavailable; deploy default is replay. |
| N6-04 | PASS_AUTOMATED | Responsive/type/build tests pass; human visual/keyboard sweep remains. |

## Locked runtime decisions

- Production/demo default remains `WEB_RESEARCH_MODE=replay`; `ddg` is an optional kill-switch mode, not a release dependency.
- DDGS is a community, keyless adapter—not an official DuckDuckGo API and not an SLA-backed source.
- Search query uses only allowlisted career title + enum intent/region; no name, school, GPA, gender, raw transcript or profile is sent.
- Web results never modify recommendation order, score, readiness, profile or market aggregate.
- Candidate D3 data is not published. Mapping coverage is not accuracy, and observed postings are not labor-shortage evidence.

## Manual release checklist

1. Deploy FE/BE with `WEB_RESEARCH_MODE=replay`; run Explore, Launch and replay three times using `docs/DEPLOY.md`.
2. Confirm `/api/health`, CORS, Research `replay/unavailable`, What-if→Undo and browser print on the public URLs.
3. Run U1–U5 with at least 2 Explore + 2 Launch users and one counselor; record denominators and one observed fix.
4. Either complete 50-label mapping accuracy + region QA or keep the existing release `market.db` and current limitations.
5. Only set `WEB_RESEARCH_MODE=ddg` after a fresh target-host spike reaches >=8/10; otherwise keep replay.

Open Sev-1/2: none found by automated suites.  
Features disabled by kill switch: live web research.  
Release decision now: **DO_NOT_SHIP_DAY3 AS FINAL** until manual E2E/human gates; safe to review/merge as an automated release candidate with replay mode.
