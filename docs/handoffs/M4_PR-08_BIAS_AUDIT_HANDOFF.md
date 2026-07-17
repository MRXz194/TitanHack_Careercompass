# [HANDOFF] M4 · PR-08 — Bias / opportunity audit → team + pitch

## Artifact

| Item | Path |
|---|---|
| Audit report (pitch) | `docs/BIAS_AUDIT.md` |
| Automated tests | `backend/tests/unit/test_bias_audit.py` |
| Runner | `backend/scripts/run_bias_audit.py` |
| Scoring sanitize | `matching.sanitize_scoring_text` / `profile_text` |
| Routes check | `backend/scripts/check_routes.py` |

## What was proven

1. **Gender free-text** in quotes does not change top-5 (≥4/5 overlap, top-3 order) across 5 personas  
2. **Region** never shrinks full career candidate set  
3. **Launch:** gender quote / school prestige notes / region do not change roles or readiness band  
4. **Prompts** lack stereotype instructions; ban gender ask  
5. **Structural:** no gender field; non-uni routes; stretch always present  

## Verify

```bash
cd backend
python -m pytest -q tests/unit/test_bias_audit.py
python scripts/check_routes.py
PYTHONPATH=. python scripts/run_bias_audit.py
python -m pytest -q tests/unit tests/contract tests/integration
```

## Pitch use

Open `docs/BIAS_AUDIT.md` — tables filled with real PASS results and the sanitize fix.

## Known limitations

1. Pairs are **constructed profiles** (deterministic), not 5 full live LLM conversations (PR-11 can add live pairs if keys available)  
2. PR-06 evidence module may still be on another PR; audit does not depend on it  
3. Human rubric of recommendation quality is PR-11, not this gate  

## Consumer ack

- Team review H+35: ⬜  
- M1 includes audit file in pitch pack: ⬜  
