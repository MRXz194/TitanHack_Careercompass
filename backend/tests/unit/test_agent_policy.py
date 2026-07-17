"""PR-12 — policy allowlist, privacy strip, budget."""
from __future__ import annotations

import pytest

from app.models.agent_schemas import AgentPlan, AgentStage, PolicyCode
from app.services import agent_policy as pol


pytestmark = pytest.mark.unit


def test_unknown_tool_denied() -> None:
    budget = pol.budget_start()
    plan = AgentPlan(next_tool="delete_database", arguments={})
    d = pol.authorize_plan(plan, AgentStage.discover, budget)
    assert d.code == PolicyCode.DENY_TOOL
    assert d.reason == "UNKNOWN_TOOL"


def test_stage_allowlist_matrix() -> None:
    budget = pol.budget_start()
    plan = AgentPlan(next_tool="get_market_context", arguments={})
    # discover cannot read market
    d = pol.authorize_plan(plan, AgentStage.discover, budget)
    assert d.code == PolicyCode.DENY_TOOL
    assert "STAGE" in d.reason
    # confirm can
    d2 = pol.authorize_plan(plan, AgentStage.confirm_profile, budget)
    assert d2.code == PolicyCode.ALLOW


def test_deterministic_stage_has_no_agent_tools() -> None:
    budget = pol.budget_start()
    plan = AgentPlan(next_tool="ask_clarifying_question", arguments={})
    d = pol.authorize_plan(plan, AgentStage.retrieve, budget)
    assert d.code == PolicyCode.DENY_TOOL


def test_tool_budget_max_two() -> None:
    budget = pol.budget_start()
    budget.agent_tools_used = 2
    plan = AgentPlan(next_tool="inspect_profile_gaps", arguments={})
    d = pol.authorize_plan(plan, AgentStage.discover, budget)
    assert d.code == PolicyCode.STOP_FALLBACK
    assert "BUDGET" in d.reason


def test_strip_gender_and_school_from_args() -> None:
    cleaned = pol.strip_privacy_args(
        {
            "message": "em là nữ học Bách Khoa GPA 3.8 thích sửa điện",
            "gender": "female",
            "school_prestige": "top",
        }
    )
    assert "gender" not in cleaned
    assert "school_prestige" not in cleaned
    assert "nữ" not in cleaned["message"].lower()
    assert "bách khoa" not in cleaned["message"].lower()
    assert "sửa điện" in cleaned["message"]


def test_market_requires_provenance_post() -> None:
    budget = pol.budget_start()
    d = pol.authorize_observation("get_market_context", {"demand_count_90d": 10}, budget)
    assert d.code == PolicyCode.DENY_TOOL
    d2 = pol.authorize_observation(
        "get_market_context",
        {"demand_count_90d": 10, "provenance": {"source": "seed"}},
        budget,
    )
    assert d2.code == PolicyCode.ALLOW
