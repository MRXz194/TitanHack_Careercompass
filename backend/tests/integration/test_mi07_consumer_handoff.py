"""MI-07 public consumer smoke stays runnable without pipeline knowledge."""

from __future__ import annotations

import json

import pytest

from scripts.test_mi07_handoff import main


pytestmark = pytest.mark.integration


def test_mi07_handoff_smoke(capsys: pytest.CaptureFixture[str]) -> None:
    assert main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "ok"
    assert output["fixture_version"] == "mi07-consumer-v1"
    assert len(output["top_k"]) == 5
    assert output["market_source_note"]
    assert output["skill_source_note"]

