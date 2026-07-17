"""CareerCompass agent policy — PR-12.

Authority lives here, not in prompts. Stage allowlist, privacy strip, budget, provenance.
"""
from __future__ import annotations

import hashlib
import re
import time
from typing import Any

from app.models.agent_schemas import (
    AgentPlan,
    AgentStage,
    PolicyCode,
    PolicyDecision,
    TurnBudget,
)

TOOL_POLICY_VERSION = "agent-policy-v1"

# Stage → agent-selectable tools (chat path). Deterministic-only tools listed separately.
AGENT_SELECTABLE: dict[AgentStage, frozenset[str]] = {
    AgentStage.discover: frozenset(
        {
            "inspect_profile_gaps",
            "ask_clarifying_question",
            "extract_profile_evidence",
            "apply_profile_correction",
        }
    ),
    AgentStage.confirm_profile: frozenset(
        {
            "inspect_profile_gaps",
            "ask_clarifying_question",
            "extract_profile_evidence",
            "apply_profile_correction",
            "get_market_context",
        }
    ),
    AgentStage.retrieve: frozenset(),
    AgentStage.explain: frozenset(),
    AgentStage.ready: frozenset(),
}

DETERMINISTIC_ONLY_TOOLS = frozenset(
    {
        "retrieve_career_candidates",
        "diversify_with_stretch",
        "assess_launch_readiness",
        "compose_grounded_explanation",
        "prepare_result",
    }
)

ALL_REGISTERED_TOOLS = frozenset(set().union(*AGENT_SELECTABLE.values()) | DETERMINISTIC_ONLY_TOOLS)

_PRIVACY_RE = re.compile(
    r"(?i)\b("
    r"giới\s*tính|con\s+trai|con\s+gái|\bnữ\b|\bnam\b|"
    r"GPA|ĐH\s+Bách\s+Khoa|Bách\s+Khoa|NEU|FTU|RMIT|"
    r"trường\s+top|trường\s+nổi\s+tiếng"
    r")\b"
)


def session_id_hash(session_id: str) -> str:
    return hashlib.sha256((session_id or "").encode("utf-8")).hexdigest()[:16]


def strip_privacy_text(text: str) -> str:
    cleaned = _PRIVACY_RE.sub(" ", text or "")
    return re.sub(r"\s+", " ", cleaned).strip()


def strip_privacy_args(args: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in (args or {}).items():
        if k in ("gender", "sex", "school", "school_name", "school_prestige", "gpa", "name"):
            continue
        if isinstance(v, str):
            out[k] = strip_privacy_text(v)
        elif isinstance(v, dict):
            out[k] = strip_privacy_args(v)
        else:
            out[k] = v
    return out


def budget_start(deadline_ms: int = 8000) -> TurnBudget:
    return TurnBudget(
        deadline_ms=deadline_ms,
        started_monotonic_ms=time.monotonic() * 1000,
    )


def budget_expired(budget: TurnBudget) -> bool:
    now = time.monotonic() * 1000
    return (now - budget.started_monotonic_ms) > budget.deadline_ms


def authorize_plan(
    plan: AgentPlan,
    stage: AgentStage,
    budget: TurnBudget,
    *,
    agent_selected: bool = True,
) -> PolicyDecision:
    """Pre-tool policy gate."""
    if budget_expired(budget):
        return PolicyDecision(
            code=PolicyCode.STOP_FALLBACK,
            reason="DEADLINE_EXCEEDED",
            tool=plan.next_tool,
        )
    if budget.policy_denies >= budget.max_policy_denies:
        return PolicyDecision(
            code=PolicyCode.STOP_FALLBACK,
            reason="POLICY_DENY_BUDGET",
            tool=plan.next_tool,
        )
    tool = (plan.next_tool or "").strip()
    if tool not in ALL_REGISTERED_TOOLS:
        return PolicyDecision(
            code=PolicyCode.DENY_TOOL,
            reason="UNKNOWN_TOOL",
            tool=tool,
        )
    if agent_selected:
        allowed = AGENT_SELECTABLE.get(stage, frozenset())
        if tool not in allowed:
            return PolicyDecision(
                code=PolicyCode.DENY_TOOL,
                reason="TOOL_NOT_ALLOWED_IN_STAGE",
                tool=tool,
            )
        if budget.agent_tools_used >= budget.max_agent_tools:
            return PolicyDecision(
                code=PolicyCode.STOP_FALLBACK,
                reason="TOOL_BUDGET_EXCEEDED",
                tool=tool,
            )
    else:
        if tool not in DETERMINISTIC_ONLY_TOOLS and tool not in AGENT_SELECTABLE.get(
            stage, frozenset()
        ):
            return PolicyDecision(
                code=PolicyCode.DENY_TOOL,
                reason="TOOL_NOT_DETERMINISTIC_PATH",
                tool=tool,
            )

    sanitized = strip_privacy_args(plan.arguments or {})
    # reject if args still contain prohibited keys after strip attempt
    if any(k in (plan.arguments or {}) for k in ("gender", "gpa", "school_prestige")):
        # strip already removed; allow with REPAIR semantics by using sanitized
        pass
    return PolicyDecision(
        code=PolicyCode.ALLOW,
        reason="OK",
        tool=tool,
        sanitized_args=sanitized,
    )


def authorize_observation(
    tool: str,
    result: dict[str, Any],
    budget: TurnBudget,
) -> PolicyDecision:
    """Post-tool policy gate — provenance + privacy on observation."""
    if budget_expired(budget):
        return PolicyDecision(code=PolicyCode.STOP_FALLBACK, reason="DEADLINE_EXCEEDED", tool=tool)
    if not isinstance(result, dict):
        return PolicyDecision(code=PolicyCode.DENY_TOOL, reason="INVALID_OBSERVATION", tool=tool)
    # market tools must carry provenance when numbers present
    if tool == "get_market_context":
        if "error" not in result and not result.get("provenance"):
            return PolicyDecision(
                code=PolicyCode.DENY_TOOL,
                reason="MISSING_PROVENANCE",
                tool=tool,
            )
    cleaned = strip_privacy_args(result)
    return PolicyDecision(
        code=PolicyCode.ALLOW,
        reason="OK",
        tool=tool,
        sanitized_args=cleaned,
    )


def record_deny(budget: TurnBudget) -> TurnBudget:
    budget.policy_denies += 1
    return budget


def record_tool_use(budget: TurnBudget) -> TurnBudget:
    budget.agent_tools_used += 1
    return budget
