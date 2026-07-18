"""Internal agent contracts (PR-12). Not part of public FE API."""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentStage(str, Enum):
    discover = "discover"
    confirm_profile = "confirm_profile"
    retrieve = "retrieve"
    explain = "explain"
    ready = "ready"
    research = "research"


class PolicyCode(str, Enum):
    ALLOW = "ALLOW"
    DENY_TOOL = "DENY_TOOL"
    REPAIR_ARGS = "REPAIR_ARGS"
    STOP_FALLBACK = "STOP_FALLBACK"


class AgentPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    intent: Literal["collect_evidence", "confirm", "revise_profile", "research"] = "collect_evidence"
    next_tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    public_rationale: str = ""
    stop_after_tool: bool = False
    # never store long CoT — optional short debug only
    thought_summary: str = ""


class PolicyDecision(BaseModel):
    code: PolicyCode
    reason: str = ""
    tool: str | None = None
    sanitized_args: dict[str, Any] = Field(default_factory=dict)


class TurnBudget(BaseModel):
    agent_tools_used: int = 0
    max_agent_tools: int = 2
    policy_denies: int = 0
    max_policy_denies: int = 2
    deadline_ms: int = 8000
    started_monotonic_ms: float = 0.0


class AgentObservation(BaseModel):
    tool: str
    ok: bool
    policy_code: str
    result: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, str] = Field(default_factory=dict)


class AgentTraceMeta(BaseModel):
    """Sanitized trace metadata only — no CoT/raw transcript."""

    session_id_hash: str = ""
    stage: AgentStage = AgentStage.discover
    tools: list[str] = Field(default_factory=list)
    policy_codes: list[str] = Field(default_factory=list)
    fallback: bool = False
    latency_ms: float = 0.0
    prompt_version: str = ""
    tool_policy_version: str = "agent-policy-v1"
