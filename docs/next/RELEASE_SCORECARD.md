# Day 3 Release Scorecard

Baseline commit: `e76a0a919505e7d534153fd95f41b72e5abc7b10`

Implementation branch: `codex/day3-opportunity-plan`

Release candidate commit: `8f982fc`

Main integration / CI fix: `19b87ad` / `d283b40`

Persona/workflow hardening code head: `codex/persona-workflow-hardening` @ `b6c8c39`

Latest verified product-code release: `2fc677e` ([CI 29660149913](https://github.com/MRXz194/TitanHack_Careercompass/actions/runs/29660149913)); later docs/CI-pin commits use the same full gate before handoff.

Automated Core Gate: **PASS** · Expansion/Production Gate: **FAIL — public deploy and human/data-label gates remain**

## Automated evidence

| Gate | Actual | State | Evidence | Owner |
|---|---|---|---|---|
| Product-code release workflow | 335 unit/contract + 46 integration + 7 E2E = 388 backend tests; runtime Explore→recommend→research/what-if + Launch + market + privacy pipeline; route invariant; 81/81 frontend tests + typecheck + production build; production dependency audit 0 | PASS_CI | [GitHub Actions run 29660149913](https://github.com/MRXz194/TitanHack_Careercompass/actions/runs/29660149913), artifact `runtime-workflow-2fc677ee2997d9884fd1b97991d8754542f31043` | M1/M3/M4/M5/M6 |
| Core regression (main baseline) | 347 backend tests; 64 frontend tests; TS typecheck + Next production build pass; Ubuntu CI backend/frontend pass | PASS_BASELINE | [GitHub Actions run 29639845313](https://github.com/MRXz194/TitanHack_Careercompass/actions/runs/29639845313) | M1 |
| Persona/workflow hardening candidate | 334 unit/contract + 40 integration + 7 E2E = 381 backend tests; route invariant; 79/79 frontend tests + typecheck + production build | PASS_CI | [GitHub Actions run 29654386126](https://github.com/MRXz194/TitanHack_Careercompass/actions/runs/29654386126) on `b6c8c39` | M1/M4/M5 |
| Snapshot provenance | Manifest/card synchronized at 3.865 normalized rows; stable SHA-256 `4ecfc1…` | PASS | `data/processed/manifest.json`, `docs/DATA_SNAPSHOT.md` | M2 |
| Acquisition integrity | 3.914 unique raw records; raw/full text ignored; source limitations retained | PASS_WITH_CAVEATS | `DATA_SNAPSHOT_AUDIT.md` | M2 |
| Extraction held-out | Dictionary extraction ran on 3.865; held-out human F1 not rerun | NOT_RUN | `postings_enriched.report.json` | M2/M3 |
| Career mapping publish | 1.031/3.865 mapped; accuracy `NOT_RUN`; candidate DB removed and release DB unchanged | FAIL / BLOCKED | `postings_mapped.report.json` | M2/M3 |
| What-if isolation | Deep copy, one hypothetical skill, deterministic real scoring, original profile byte-stable, invalid input 422 | PASS | `test_what_if.py`, `test_recommendations.py` | M4 |
| Research isolation/citations/fallback | Typed 11th tool, policy stage, safe URLs, local/replay fallback, candidate/profile isolation | PASS | research unit/integration/contract tests | M4 |
| DuckDuckGo live gate | 7/10 queries with >=3 relevant safe links; p95 1.129s; rate-limit/empty on last 3 | FAIL | `python -m scripts.run_research_spike` | M4/M1 |
| UI/UX | Cream editorial system, serif/mono split, compare-first, region research, retry/new-profile recovery; demand volume is now visibly separated from growth; mobile DOM at 390px has no horizontal overflow; Launch readiness is visible before expanding a card | PASS_AUTOMATED | 81 Vitest tests/typecheck/build + prior Edge headless/DevTools measurement; visual human QA pending | M5/M6 |
| Persona browser smoke | Technical and creative Explore profiles produced different dominant dimensions/top careers; Launch retained only stated Excel evidence, did not invent a dashboard, and exposed readiness in one click | PASS_LOCAL_MOCK | Real React UI in headless Edge; backend persona workflows pass CI, deployed-browser repetition remains | M1/M5/M6 |
| Offline Explore/Launch/Replay E2E | 7/7 E2E including five-persona distinctness and Launch isolation | PASS_CI | [GitHub Actions run 29654386126](https://github.com/MRXz194/TitanHack_Careercompass/actions/runs/29654386126) | M1 |
| Vercel public production routes | Deployment URLs redirect to Vercel login; earlier HTTP 200 was auth HTML, not app route evidence | FAIL / BLOCKED | `docs/DEPLOY.md`; disable Deployment Protection then rerun incognito smoke | M1/M6 |
| Render health + live CORS E2E | Render dashboard URL chưa được bàn giao; guessed service URL timeout, không dùng làm evidence | NOT_RUN / BLOCKED | cần URL thật + `/api/health` | M1 |
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
6. **Completed:** hardening CI xanh cho persona workflows, no-accent/negation/privacy,
   blank-profile 409, frontend request-race, demand/trend semantics và runtime workflow artifact
   tại run `29660149913`.
7. Disable Vercel Deployment Protection for production and verify the final URL remains on the app domain in an incognito browser.

Open Sev-1: public Vercel access blocked by Deployment Protection.

Local limitation: máy audit không có Python/Docker daemon; backend hardening đã được xác nhận bằng CI Ubuntu ở trên. Frontend 81 tests/typecheck/build đã pass cả local lẫn CI.

Features disabled by kill switch: live web research.

Release decision now: **DO_NOT_SHIP_DAY3 AS FINAL** until manual E2E/human gates; safe to review/merge as an automated release candidate with replay mode.
