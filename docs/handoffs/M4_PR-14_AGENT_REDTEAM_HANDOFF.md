# [HANDOFF] M4 · PR-14 — Agent evaluation / red-team → M1 / pitch

## Artifact

| Item | Path |
|---|---|
| Red-team fixtures | `backend/tests/fixtures/agent/{allow,deny,fallback,injection,personas,replay}/` |
| Sanitized agent replay | `backend/app/data/replay/agent_sanitized_trace.json` |
| Tests | `backend/tests/unit/test_agent_redteam.py` (+ existing agent unit/contract/integration) |
| Harness | `backend/scripts/run_m4_evaluation.py` (agent gates + versions) |
| Scorecard | `docs/EVALUATION_RESULTS.md` |
| Bias addendum | `docs/BIAS_AUDIT.md` §4.1 |

## Versions (record in pitch evidence)

| Field | Value |
|---|---|
| Tool policy | `agent-policy-v1` |
| Tool registry | `agent-tools-v2-research` |
| Profiler prompt | `profiler-v2` |
| Default `AGENT_MODE` | `deterministic` |
| Max agent tools / turn | 2 |
| Deadline | 8000 ms |
| Recommendation planner | **none** (deterministic matching) |

## AGENTIC_RUNTIME §8 coverage

| Gate | Result | Evidence |
|---|---|---|
| 12 persona Explore/Launch | PASS | `personas_12.json` + `test_twelve_personas_*` |
| Tool-selection fixture | PASS | allow/deny fixtures parametrized |
| Prompt injection | PASS | injection fixtures; ranking tools DENY |
| Gender/school/region pairs | PASS | strip + region non-filter tests; BIAS §4.1 |
| Grounded evidence / provenance | PASS | missing_provenance DENY; market requires provenance |
| Tool failure matrix | PASS | unknown tool / exception → fallback reply |
| Replay | PASS | sanitized trace fixture; DEMO_MODE=replay disables agent |
| Cost/latency | PASS | orchestrator p95 ≪ 100ms offline |

**Do not delete failing fixtures or lower thresholds.** Failures must be fixed or reported honestly.

## Claim boundary (M1)

- **Allowed:** bounded chat agent with stage allowlist, policy authority, offline red-team PASS, deterministic recommend.
- **Not allowed without live gates:** “fully autonomous agent”, live multi-turn LLM planner quality, human dual-rater ≥3.5.

## Verify

```bash
cd backend
python -m pytest -q tests/unit/test_agent_redteam.py
python -m pytest -q \
  tests/unit/test_agent_policy.py tests/unit/test_agent_tools.py \
  tests/unit/test_agent_graph.py tests/unit/test_agent_chat.py \
  tests/unit/test_agent_redteam.py \
  tests/contract/test_agent_tool_contract.py \
  tests/integration/test_agent_chat_api.py
PYTHONPATH=. python scripts/run_m4_evaluation.py
python -m pytest -q tests/unit/test_evaluation_report.py
python -m pytest -q tests/unit tests/contract tests/integration
```

## Input → output mẫu

- Fixture `deny/discover_market.json` → policy `DENY_TOOL` / `TOOL_NOT_ALLOWED_IN_STAGE`
- Fixture `injection/override_policy.json` → planner still `extract_profile_evidence`
- Replay `agent_sanitized_trace.json` → tools/policy_codes/latency only; no CoT

## Known limitations

1. Live LLM planner path NOT_RUN (offline injectable planner / plain_python path measured).
2. Default demo remains `AGENT_MODE=deterministic`; langgraph optional.
3. Human dual-rater + student usefulness still NOT_RUN (M3/M1).

## Consumer ack

- M1 pitch claims review: ⬜
- M1 deterministic replay smoke: ⬜
