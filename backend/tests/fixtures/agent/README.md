# Agent fixtures (PR-12 / PR-13 / PR-14)

Fictional, sanitized, versioned fixtures for offline agent evaluation and red-team.
**No chain-of-thought, no raw student transcripts, no API keys.**

## Layout

| Dir | Purpose |
|---|---|
| `allow/` | Plans that policy must ALLOW for the given stage |
| `deny/` | Plans that policy must DENY (stage, unknown tool, injection) |
| `fallback/` | Budget / provenance / deadline cases → STOP_FALLBACK or DENY |
| `injection/` | User messages that try to override policy; plan still constrained |
| `personas/` | 12 structural personas (8 Explore + 4 Launch) for agent turns |
| `replay/` | Sanitized trace metadata only (tools, versions, latency, fallback) |

## Schema (tool-selection)

```json
{
  "id": "unique-id",
  "stage": "discover|confirm_profile|retrieve|explain|ready",
  "plan": {
    "intent": "collect_evidence|confirm|revise_profile",
    "next_tool": "tool_name",
    "arguments": {},
    "public_rationale": "user-facing status only",
    "stop_after_tool": true
  },
  "expect": {
    "policy_code": "ALLOW|DENY_TOOL|STOP_FALLBACK",
    "reason_contains": "optional substring"
  },
  "notes": "optional"
}
```

## Version pins (record in EVALUATION_RESULTS)

- `tool_policy_version`: `agent-policy-v1`
- `tool_registry_version`: `agent-tools-v2-research`
- Planner is offline/fixture or injectable; no live model required for red-team gates.
