# [HANDOFF] M4 · PR-07 — Pathways + Graduate Launch readiness → M6 / M1

## Artifact

| Item | Path |
|---|---|
| Pathways / readiness | `backend/app/services/pathways.py` |
| Wired from | `backend/app/services/matching.py` → `build_recommendation` |
| Unit tests | `backend/tests/unit/test_pathways.py` |
| Integration | `backend/tests/integration/test_launch_pathways.py` |
| Design source | `docs/GRADUATE_LAUNCH.md` |

## Behavior

### Explore (`journey_mode=explore`)
- `job_readiness` **always `null`**
- `routes`: ≥2, ≥1 `vocational|college|certificate` (guaranteed by `ensure_routes`)

### Launch (`journey_mode=launch`)
- `job_readiness` object with:
  - `band`: `ready_now | near_ready | build_foundation` (guidance, **not** hiring probability)
  - `matched_skills[]`: each has `evidence` from profile skill `source_quote` or experience
  - `missing_skills[]`: ⊆ role `market.top_skills`, disjoint from matched
  - `search_queries`: 2–4 neutral job-search strings (no gender/age/GPA/school prestige)
  - `actions_30d`: exactly weeks 1–4, each with non-empty `deliverable` (no bare “học thêm”)
- Launch **route order** prefers certificate/vocational/college before university (presentation only)

### Hard rules kept
- Same matching engine as Explore (no second scorer)
- Region does **not** change readiness band or drop roles
- Market demand does **not** raise band when skill evidence is low
- No invented school/company brands in fallback route copy

## Verify

```bash
cd backend
python -m pytest -q tests/unit/test_pathways.py tests/integration/test_launch_pathways.py
python -m pytest -q tests/unit tests/contract tests/integration
python scripts/check_routes.py
```

## M6 notes

- Hide readiness block when `job_readiness === null` (Explore)
- Show band + matched/missing + queries + 4 weekly actions for Launch
- Do not render readiness as “% được tuyển”

## Known limitations

1. Evidence wording still template (PR-06 branch if not merged) — shape unchanged
2. Role top skills from seed market until MI-04 live stats
3. Entry role aliases depend on KB fields when present

## Consumer ack

- M6 Launch results UI: ⬜  
- M1 smoke Explore null + Launch readiness: ⬜  
