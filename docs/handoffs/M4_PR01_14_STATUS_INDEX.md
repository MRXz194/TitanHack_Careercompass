# [HANDOFF INDEX] M4 · PR-01 → PR-14 — status for M1/M5/M6

> Single index after full M4 chain lands on `kaguya`. Individual handoffs stay authoritative for each PR.

## Branch / validate

| Field | Value |
|---|---|
| Branch | `kaguya` |
| Chain | PR-01…PR-14 **DONE** (offline) |
| Scorecard | `docs/EVALUATION_RESULTS.md` status `M4_PARTIAL` |
| Workstream | `docs/workstreams/M4_PROFILE_RECOMMENDER.md` |

### Reproduce

```bash
cd backend
python -m compileall -q app scripts tests
python -m pytest -q tests/unit tests/contract tests/integration
python scripts/check_routes.py
PYTHONPATH=. python scripts/run_m4_evaluation.py
cd ../frontend && npm run typecheck
```

## Per-PR artifacts

| PR | Handoff / report | Key code |
|---|---|---|
| 01 | workstream inline | `schemas.py`, `frontend/types/index.ts` |
| 02 | workstream inline | `prompts/profiler.py` (`profiler-v2`) |
| 03 | workstream inline | `profiler.py`, `session_store.py` |
| 04 | `M4_PR-04_CHAT_HANDOFF.md` | `app/data/replay/*_sample_session.json` |
| 05 | workstream inline | `matching.py`, `routers/recommend.py` |
| 06 | `M4_PR-06_EVIDENCE_HANDOFF.md` | `evidence.py` |
| 07 | `M4_PR-07_PATHWAYS_LAUNCH_HANDOFF.md` | `pathways.py` |
| 08 | `M4_PR-08_BIAS_AUDIT_HANDOFF.md` | `BIAS_AUDIT.md` |
| 09 | `M4_PR-09_TRANSPARENCY_COPY_HANDOFF.md` | `frontend/lib/copy/transparency.ts` |
| 10 | `M4_PR-10_QUALITY_TUNING_HANDOFF.md` | quality-only profiler/evidence |
| 11 | `M4_PR-11_EVALUATION_REPORT_HANDOFF.md` | `scripts/run_m4_evaluation.py` |
| 12 | `M4_PR-12_AGENT_RUNTIME_HANDOFF.md` | `agent_{policy,tools,graph}.py` |
| 13 | `M4_PR-13_CHAT_AGENT_HANDOFF.md` | `agent_chat.py` → `handle_turn` |
| 14 | `M4_PR-14_AGENT_REDTEAM_HANDOFF.md` | fixtures/agent + redteam tests |

## Hard rules still true

1. No gender field anywhere in profile/scoring storage  
2. No invented market numbers (grounding validators)  
3. Region never hard-filters careers  
4. Recommend path never uses agent planner  
5. Chat public API never returns CoT/trace  
6. Default demo: `AGENT_MODE=deterministic`  

## Open for consumers (not M4 code blockers)

| Item | Owner |
|---|---|
| Release PASS/CONDITIONAL/FAIL | M1 |
| Human dual-rater rubric | M3/M1 |
| Usefulness n≥5 | M1 L-11 |
| F1-10 agent status copy in chat UI | M5 |
| F2-09 provenance panel | M6 |
| Live LLM planner quality | optional post-demo |

## Consumer ack

- M1 replay + pitch claim freeze: ⬜  
- M5 chat/profile integration: ⬜  
- M6 results evidence render: ⬜  
