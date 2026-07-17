# [HANDOFF] M4 · PR-11 — AI evaluation report → M1 / pitch

## Artifact

| Item | Path |
|---|---|
| Results table | `docs/EVALUATION_RESULTS.md` |
| Harness | `backend/scripts/run_m4_evaluation.py` |
| Report gate tests | `backend/tests/unit/test_evaluation_report.py` |

## What was measured (honest)

**PASS (automated, offline deterministic path):**

- Profiler unit + integration suites
- Evidence number grounding 100%
- Launch readiness invariants 100%
- Route structural 100%
- Gender paired bias suite (see `BIAS_AUDIT.md`)
- Chat p95 ≪ 5s; recommendation p95 ≪ 8s (TestClient, no live LLM)
- Automated structural rubric on 12 gold profiles mean ≥3.5 (proxy — **not** dual-human)

**NOT_RUN / N/A (do not overclaim in pitch):**

- Skill extraction PR/F1 (M3)
- Live LLM session validity
- Human dual-rater recommendation rubric
- User testing n≥5 (M1)
- LangGraph/agent gates (PR-12+)

## Reproduce

```bash
cd backend
PYTHONPATH=. python scripts/run_m4_evaluation.py
python -m pytest -q tests/unit/test_evaluation_report.py
```

## Pitch rules

- Status is `M4_PARTIAL` until M1 final sign-off
- Never present automated proxy rubric as “human ≥3.5/5”
- Demand proxy limitation already listed

## Consumer ack

- M1 release decision filled: ⬜  
- M3 confirms extraction rows stay M3-owned: ⬜  
