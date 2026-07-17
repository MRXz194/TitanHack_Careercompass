"""PR-13 — stage mapping, agent enrichment, degradation, no CoT leak."""
from __future__ import annotations

import pytest

from app.core.config import get_settings
from app.models.agent_schemas import AgentStage
from app.models.schemas import Profile
from app.services import agent_chat, agent_graph
from app.services.session_store import Corrections, SessionState


pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _clear_settings(monkeypatch: pytest.MonkeyPatch):
    agent_graph.reset_graph_cache()
    monkeypatch.setenv("AGENT_MODE", "deterministic")
    monkeypatch.setenv("DEMO_MODE", "off")
    get_settings.cache_clear()
    yield
    agent_graph.reset_graph_cache()
    get_settings.cache_clear()


def _state(**kwargs) -> SessionState:
    base = dict(
        session_id="ac-1",
        journey_mode="explore",
        phase="interests",
        turn=2,
        done=False,
        profile=Profile(session_id="ac-1", journey_mode="explore"),
        corrections=Corrections(),
        messages=[],
        turns_in_phase=1,
        constraint_declined=False,
        fallback_index=0,
    )
    base.update(kwargs)
    return SessionState(**base)  # type: ignore[arg-type]


def test_map_phase_to_stage() -> None:
    assert agent_chat.map_phase_to_agent_stage("warmup") == AgentStage.discover
    assert agent_chat.map_phase_to_agent_stage("interests") == AgentStage.discover
    assert agent_chat.map_phase_to_agent_stage("wrapup") == AgentStage.confirm_profile
    assert agent_chat.map_phase_to_agent_stage("interests", done=True) == AgentStage.confirm_profile


def test_agent_disabled_in_deterministic_and_replay(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MODE", "deterministic")
    get_settings.cache_clear()
    assert agent_chat.agent_enabled_for_chat() is False
    monkeypatch.setenv("AGENT_MODE", "langgraph")
    monkeypatch.setenv("DEMO_MODE", "replay")
    get_settings.cache_clear()
    assert agent_chat.agent_enabled_for_chat() is False
    monkeypatch.setenv("DEMO_MODE", "off")
    get_settings.cache_clear()
    assert agent_chat.agent_enabled_for_chat() is True


def test_run_agent_enrichment_langgraph_no_trace_leak(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MODE", "langgraph")
    get_settings.cache_clear()
    agent_graph.reset_graph_cache()
    st = _state()
    out = agent_chat.run_agent_enrichment(st, "Em hay sửa đồ điện")
    assert "reply" in out
    trace = out.get("trace") or {}
    assert "messages" not in trace
    assert "cot" not in str(trace).lower()
    assert "transcript" not in str(trace).lower()
    # response path must not put thought_summary on ChatResponse — enrichment only
    assert "thought_summary" not in out


def test_enrichment_degrades_on_bad_planner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MODE", "langgraph")
    get_settings.cache_clear()
    agent_graph.reset_graph_cache()

    def boom(_state):
        raise RuntimeError("planner_down")

    # patch invoke to raise
    monkeypatch.setattr(
        agent_graph,
        "invoke_agent_turn",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("down")),
    )
    out = agent_chat.run_agent_enrichment(_state(), "hello")
    assert out["fallback"] is True
    assert out["delta"] is None


def test_deterministic_extract_tools_only() -> None:
    st = _state(phase="interests", turn=3)
    delta = agent_chat.maybe_run_extract_tools_only(st, "Em hay sửa quạt điện")
    assert delta is not None
    # should capture some signal without requiring LLM
    assert delta.interests or delta.skills or delta.dimensions
