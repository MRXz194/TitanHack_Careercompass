"""PR-12 contract — tool names align with policy registry."""
from __future__ import annotations

import pytest

from app.services.agent_policy import ALL_REGISTERED_TOOLS, AGENT_SELECTABLE, DETERMINISTIC_ONLY_TOOLS
from app.services.agent_tools import get_registry


pytestmark = pytest.mark.contract


def test_registry_names_subset_of_policy_universe() -> None:
    reg = set(get_registry().names())
    assert reg == ALL_REGISTERED_TOOLS
    assert len(reg) == 10


def test_agent_selectable_and_deterministic_partition() -> None:
    agent = set().union(*AGENT_SELECTABLE.values())
    # partitions may overlap only intentionally — here they are disjoint
    assert agent.isdisjoint(DETERMINISTIC_ONLY_TOOLS)
    assert agent | DETERMINISTIC_ONLY_TOOLS == ALL_REGISTERED_TOOLS
