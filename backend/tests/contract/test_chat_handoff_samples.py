"""PR-04: sample handoff fixtures match ChatResponse / Profile contract."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.models.schemas import ChatResponse, Profile
from app.prompts.profiler import PROFILER_PROMPT_VERSION


pytestmark = pytest.mark.contract

REPLAY = Path(__file__).resolve().parents[2] / "app" / "data" / "replay"
SAMPLES = (
    REPLAY / "explore_sample_session.json",
    REPLAY / "launch_sample_session.json",
)


@pytest.mark.parametrize("path", SAMPLES, ids=lambda p: p.name)
def test_handoff_sample_metadata(path: Path) -> None:
    assert path.is_file(), f"missing handoff sample {path}"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc.get("fictional") is True
    assert doc.get("contract_version") == "v1"
    assert doc.get("prompt_version") == PROFILER_PROMPT_VERSION
    assert doc.get("journey_mode") in ("explore", "launch")
    assert isinstance(doc.get("turns"), list) and len(doc["turns"]) >= 3
    assert "notes" in doc and "errors" in doc["notes"]
    assert "latency_ms" in doc["notes"]


@pytest.mark.parametrize("path", SAMPLES, ids=lambda p: p.name)
def test_handoff_sample_turns_parse_as_chat_response(path: Path) -> None:
    doc = json.loads(path.read_text(encoding="utf-8"))
    for i, turn in enumerate(doc["turns"]):
        req = turn["request"]
        assert req["session_id"] == doc["session_id"]
        assert req["journey_mode"] == doc["journey_mode"]
        resp = ChatResponse.model_validate(turn["response"])
        assert resp.profile.session_id
        assert resp.profile.journey_mode == doc["journey_mode"]
        assert "gender" not in resp.profile.model_dump()
        assert resp.turn == i + 1
        assert resp.reply.strip()


@pytest.mark.parametrize("path", SAMPLES, ids=lambda p: p.name)
def test_handoff_patch_sample_parses(path: Path) -> None:
    doc = json.loads(path.read_text(encoding="utf-8"))
    patch = doc["patch_sample"]
    profile = Profile.model_validate(patch["response"]["profile"])
    assert profile.session_id == doc["session_id"]
    assert "sample-interest-from-patch" in profile.interests


def test_explore_and_launch_samples_both_present() -> None:
    names = {p.name for p in REPLAY.glob("*_sample_session.json")}
    assert "explore_sample_session.json" in names
    assert "launch_sample_session.json" in names
