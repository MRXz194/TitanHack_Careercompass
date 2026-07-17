# [HANDOFF] M4 · PR-06 — Grounded evidence → M6 / M1

Grounded evidence + true counterfactual for recommendation cards.

## Artifact

| Item | Path |
|---|---|
| Evidence service | `backend/app/services/evidence.py` |
| Prompt | `backend/app/prompts/evidence.py` (`evidence-v1`) |
| Wired from | `backend/app/services/matching.py` → `build_recommendation` |
| Unit tests | `backend/tests/unit/test_evidence.py` |
| Integration | `backend/tests/integration/test_evidence_grounding.py` |

## Behavior

1. **Code** selects allowed quotes from profile (evidence_quotes, skill/experience source_quote, interests).
2. **Code** builds `allowed_stats` only from `MarketStats` (no invented numbers).
3. **Code** computes counterfactual by re-scoring with flipped dominant dimension (`matching._counterfactual_text`).
4. Optional **LLM** verbalizes (if `CHAT_API_KEY` and not `DEMO_MODE=replay`); output validated.
5. On fail / no key → **deterministic Vietnamese templates** that only use allowed stats/quotes.

### Grounding rules

- Every digit in `why.from_market[*].stat` must appear in stats dict.
- Salary lines omitted when `salary_sample_count < 5` or salary null.
- Trend omitted when `low_confidence=true`.
- Quotes must belong to session profile (injection strings skipped).

## Run / verify

```bash
cd backend
python -m pytest -q tests/unit/test_evidence.py tests/integration/test_evidence_grounding.py
python -m pytest -q tests/unit tests/contract tests/integration
```

## M6 notes

- FE already renders `why.from_you`, `why.from_market`, `why.counterfactual` — shapes unchanged.
- Show `market.low_confidence` caveats; do not invent alternate numbers client-side.
- Counterfactual is reference text, not a verdict.

## Known limitations

1. LLM polish only when API key present; default path is templates (demo-safe).
2. Stats still from seed until MI-04 live market.db.
3. Pathway/readiness full polish is PR-07.

## Consumer ack

- M6 renders evidence cards from live API: ⬜  
- M1 smoke recommendations after merge: ⬜  
