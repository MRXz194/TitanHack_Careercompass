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


def test_strip_direct_contact_and_secret_but_keep_vietnam_country_name() -> None:
    cleaned = pol.strip_privacy_text(
        "Em ở Việt Nam, email student@example.com, số 0912 345 678 và key sk-abcdefgh123456"
    )
    assert "Việt Nam" in cleaned
    assert "student@example.com" not in cleaned
    assert "0912 345 678" not in cleaned
    assert "sk-abcdefgh123456" not in cleaned
    assert "đã ẩn" in cleaned


def test_strip_unaccented_gender_self_label_but_keep_career_signal() -> None:
    cleaned = pol.strip_privacy_text("Em la nu, em thích thiết kế poster")
    assert "em la nu" not in cleaned.lower()
    assert "thiết kế poster" in cleaned


def test_strip_explicit_real_name_but_keep_activity() -> None:
    cleaned = pol.strip_privacy_text("Tên em là Nguyễn Văn An, em thích sửa đồ điện")
    assert "Nguyễn Văn An" not in cleaned
    assert "sửa đồ điện" in cleaned


def test_strip_gpa_value_and_explicit_address() -> None:
    cleaned = pol.strip_privacy_text(
        "GPA 3.8/4, địa chỉ: 123 Đường ABC; em thích phân tích dữ liệu"
    )
    assert "3.8" not in cleaned
    assert "123 Đường ABC" not in cleaned
    assert "phân tích dữ liệu" in cleaned


def test_strip_privacy_args_sanitizes_strings_inside_lists() -> None:
    cleaned = pol.strip_privacy_args(
        {"remove_interests": ["Em là nữ", "student@example.com", "vẽ tranh"]}
    )
    values = cleaned["remove_interests"]
    assert "nữ" not in str(values).lower()
    assert "student@example.com" not in str(values)
    assert "vẽ tranh" in values


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


def test_research_tool_is_bounded_to_research_stage() -> None:
    budget = pol.budget_start()
    plan = AgentPlan(
        intent="research",
        next_tool="search_career_sources",
        arguments={"career_ids": ["data-analyst"], "intent": "skills", "region": "all"},
    )
    assert pol.authorize_plan(plan, AgentStage.discover, budget).code == PolicyCode.DENY_TOOL
    assert pol.authorize_plan(plan, AgentStage.research, budget).code == PolicyCode.ALLOW


def test_research_observation_requires_status_and_citations() -> None:
    budget = pol.budget_start()
    denied = pol.authorize_observation("search_career_sources", {"careers": []}, budget)
    assert denied.code == PolicyCode.DENY_TOOL
    allowed = pol.authorize_observation(
        "search_career_sources",
        {"status": "unavailable", "careers": []},
        budget,
    )
    assert allowed.code == PolicyCode.ALLOW
