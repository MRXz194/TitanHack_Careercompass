# [HANDOFF] M4 · PR-10 — Quality tuning → M1 / team

## Scope

PR-10 = **quality-only** (no new product features / no contract break).  
GitHub `ai-quality` labels: **none open** at task start → treated internal Sev tickets below.

## Issues tuned (before → after)

| ID | Symptom (before) | Change | Acceptance (after) |
|---|---|---|---|
| Q-01 | Full user utterance stored as `interests[]` → noisy profile / weak match | `_compact_interest_label` + phase-aware interest write | Interests ≤48 chars; long non-activity text skipped |
| Q-02 | Fallback questions can repeat consecutive turns | `get_fallback_question(..., recent_replies=)` + handle_turn de-dupe | No consecutive identical assistant replies (integration) |
| Q-03 | Any message with “việc/data” overwrote `job_goal` with full sentence | `_extract_job_goal` intent markers + short canned goals | Abilities “làm việc nhóm” → no goal; “muốn tìm việc data” → short goal |
| Q-04 | Budget phrases ignored in deterministic path | Detect “hạn chế/eo hẹp…” → `study_budget` | Constraints completeness improves for Explore |
| Q-05 | Evidence reason generic | Template reason uses skill/interest hint when present | Still grounded; more specific copy |

## Gold personas re-run

| Persona | Check | Result |
|---|---|---|
| Hands-on tech (Explore) | top-5 includes technical/hands-on ids | `test_gold_tech_persona_top5_includes_hands_on_role` |
| Launch Excel | readiness actions=4; matched evidence when role has Excel | `test_gold_launch_excel_has_matched_evidence` |
| Chat multi-turn | no consecutive duplicate questions | `test_chat_does_not_repeat_same_question_consecutively` |

## Verify

```bash
cd backend
python -m pytest -q tests/unit/test_quality_tuning.py tests/integration/test_quality_chat.py
python -m pytest -q tests/unit tests/contract tests/integration
```

## Forbidden (kept)

- No new public API fields
- No new model providers
- No threshold weakening in EVALUATION.md / BIAS_AUDIT.md

## Known remaining quality debt (not Sev-1 for demo)

1. Deterministic extractor still keyword-based vs full LLM chat quality  
2. Live 12-persona human rubric → PR-11  
3. Agent path → PR-12+  

## Consumer ack

- M1 E2E after pull: ⬜  
- Close any future `ai-quality` issues against this commit: ⬜  
