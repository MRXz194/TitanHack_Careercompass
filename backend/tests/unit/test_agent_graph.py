"""PR-12 — graph compile/invoke offline + deterministic mode isolation + overhead."""
from __future__ import annotations

import time

import pytest

from app.core.config import get_settings
from app.models.agent_schemas import AgentPlan, AgentStage, PolicyCode
from app.services import agent_graph


pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _reset_graph_and_mode(monkeypatch: pytest.MonkeyPatch):
    agent_graph.reset_graph_cache()
    # default deterministic for most tests
    monkeypatch.setenv("AGENT_MODE", "deterministic")
    get_settings.cache_clear()
    yield
    agent_graph.reset_graph_cache()
    get_settings.cache_clear()


def test_deterministic_mode_does_not_compile_graph(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MODE", "deterministic")
    get_settings.cache_clear()
    agent_graph.reset_graph_cache()
    assert agent_graph.should_use_graph() is False
    with pytest.raises(RuntimeError, match="GRAPH_DISABLED"):
        agent_graph.get_compiled_graph()
    assert agent_graph.graph_was_compiled() is False
    out = agent_graph.invoke_agent_turn(session_id="det-1")
    assert out["engine"] == "plain_python"
    assert out["reply"]
    assert "trace" in out
    assert out["trace"].get("session_id_hash")
    # still no graph compile
    assert agent_graph.graph_was_compiled() is False


def test_langgraph_mode_compile_and_invoke(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MODE", "langgraph")
    get_settings.cache_clear()
    agent_graph.reset_graph_cache()
    assert agent_graph.should_use_graph() is True
    g = agent_graph.get_compiled_graph()
    assert g is not None
    assert agent_graph.graph_was_compiled() is True
    out = agent_graph.invoke_agent_turn(session_id="lg-1")
    assert out["engine"] == "langgraph"
    assert out["reply"]
    assert isinstance(out["observations"], list)


def test_unknown_tool_plan_falls_back() -> None:
    def bad_planner(_state):
        return AgentPlan(next_tool="rm_rf_root", arguments={})

    out = agent_graph.plain_python_orchestrator(
        session_id="bad-tool",
        planner=bad_planner,
    )
    assert out["fallback"] is True
    assert out["reply"]


def test_invalid_stage_tool_denied() -> None:
    def market_in_discover(_state):
        return AgentPlan(
            next_tool="get_market_context",
            arguments={"career_id": "data-analyst"},
        )

    out = agent_graph.plain_python_orchestrator(
        session_id="stage-deny",
        stage=AgentStage.discover,
        planner=market_in_discover,
    )
    assert out["fallback"] is True


def test_plain_orchestrator_allow_path() -> None:
    def good(_state):
        return AgentPlan(
            next_tool="ask_clarifying_question",
            arguments={"phase": "interests", "turn_index": 1},
            stop_after_tool=True,
            public_rationale="status",
        )

    out = agent_graph.plain_python_orchestrator(session_id="ok-1", planner=good)
    assert out["engine"] == "plain_python"
    assert out["observations"]
    assert out["observations"][0]["policy_code"] == PolicyCode.ALLOW.value


def test_orchestration_overhead_p95_under_100ms() -> None:
    """Spike gate: 100 fixture turns without model, p95 < 100ms."""
    latencies: list[float] = []

    def planner(_state):
        return AgentPlan(
            next_tool="inspect_profile_gaps",
            arguments={"completeness": 0.2, "interest_count": 0},
            stop_after_tool=True,
        )

    for i in range(100):
        t0 = time.perf_counter()
        agent_graph.plain_python_orchestrator(
            session_id=f"ov-{i}",
            planner=planner,
        )
        latencies.append((time.perf_counter() - t0) * 1000)
    latencies.sort()
    p95 = latencies[int(round(0.95 * (len(latencies) - 1)))]
    assert p95 < 100.0, f"p95={p95:.2f}ms"


def test_trace_has_no_raw_transcript_keys() -> None:
    out = agent_graph.invoke_agent_turn(session_id="priv-1")
    trace = out["trace"]
    blob = str(trace).lower()
    assert "cot" not in blob
    assert "transcript" not in blob
    assert "messages" not in trace
