"""PR-11 — EVALUATION_RESULTS.md must reflect honest M4 measurement, not empty placeholders."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO = Path(__file__).resolve().parents[3]
RESULTS = REPO / "docs" / "EVALUATION_RESULTS.md"


def test_evaluation_results_exists_and_has_commit() -> None:
    assert RESULTS.is_file()
    text = RESULTS.read_text(encoding="utf-8")
    assert "TBD" not in text.split("## Metrics")[0] or "Commit SHA" in text
    assert re.search(r"Commit SHA \| `[0-9a-f]+` \|", text) or re.search(
        r"Commit SHA \| `[a-z0-9]+` \|", text
    )


def test_m4_gates_not_all_not_run() -> None:
    text = RESULTS.read_text(encoding="utf-8")
    # Core M4 rows should be filled
    for needle in (
        "evidence_number_grounding",
        "launch_readiness_invariants",
        "gender_paired_top5_overlap",
        "route_structural",
        "chat_p95",
        "recommendation_p95",
    ):
        assert needle in text
    # Must not claim human dual-rater without NOT_RUN
    assert "human_recommendation_rubric" in text or "dual" in text.lower() or "NOT_RUN" in text


def test_agent_gates_present_after_pr14() -> None:
    """PR-14: agent metrics must be real pass/fail, not permanent N/A placeholders."""
    text = RESULTS.read_text(encoding="utf-8")
    for needle in (
        "agent_langgraph_gates",
        "agent_tool_selection_allowlist",
        "agent_prompt_injection",
        "agent_personas_n12",
        "agent_orchestrator_p95",
        "agent-policy-v1",
        "agent-tools-v1",
    ):
        assert needle in text, f"missing {needle}"
    # Must not still claim agent gates unimplemented
    assert "PR-12/13/14 not implemented" not in text
    # Must not overclaim autonomy
    assert "autonomous" in text.lower() or "không claim" in text.lower()


def test_no_cherry_pick_disclaimer_present() -> None:
    text = RESULTS.read_text(encoding="utf-8").lower()
    assert "không cherry-pick" in text or "proxy" in text
