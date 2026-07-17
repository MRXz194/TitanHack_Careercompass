# [HANDOFF] M4 · PR-09 — Transparency copy → M6 / pitch

## Artifact

| Item | Path |
|---|---|
| Runtime copy (source of truth) | `frontend/lib/copy/transparency.ts` (`transparency-v1`) |
| Page wire | `frontend/app/how-it-works/page.tsx` |
| Docs mirror | `docs/copy/M4_transparency_vi.md` |
| BE gate tests | `backend/tests/unit/test_transparency_copy.py` |
| Optional FE assert script | `frontend/tests/unit/transparency-copy.test.ts` |

## Content covered

- Data snapshot / hiring-demand proxy (not “thiếu người”)
- Conversational profile + edit + no gender field
- Scoring priorities + market cap + vocational routes + stretch
- Explore vs Launch + readiness ≠ hiring probability
- Limits, autonomy, disclaimer footer
- Tooltips for demand, match, stretch, region, readiness, source

## Constraints

- Main body ≤300 Vietnamese words (gated)
- No overclaim phrases (AI knows best / guaranteed job / nghề tốt nhất / …)
- M6 may restyle layout; **do not rewrite claims** without M4

## Verify

```bash
cd backend && python -m pytest -q tests/unit/test_transparency_copy.py
cd frontend && npm run typecheck
# optional:
# npx tsx frontend/tests/unit/transparency-copy.test.ts
```

## M6 notes (F2-06)

- Import `PAGE` / `TOOLTIPS` from `@/lib/copy/transparency` for landing tooltips if needed
- Keep footer disclaimer visible on results too (existing product rule)

## Human verify (DoD)

- [ ] 2 people outside team paraphrase “not a verdict / demand proxy / readiness” correctly  
- Owner: M4 after show-and-tell  

## Consumer ack

- M6 layout polish without claim changes: ⬜  
- M1 link page in pitch: ⬜  
