import re

import pytest

from app.prompts import profiler as prompts


pytestmark = pytest.mark.unit

PHASES = ("warmup", "interests", "abilities", "constraints", "wrapup")


def test_prompt_version_is_profiler_v2() -> None:
    assert prompts.PROFILER_PROMPT_VERSION == "profiler-v2"
    assert "profiler-v2" in prompts.PROFILER_SYSTEM


def test_build_system_includes_mode_and_phase() -> None:
    explore = prompts.build_profiler_system("explore", "interests")
    launch = prompts.build_profiler_system("launch", "abilities")
    assert "journey_mode=explore" in explore
    assert "phase=interests" in explore
    assert "EXPLORE" in explore.upper() or "khám phá" in explore.lower()
    assert "journey_mode=launch" in launch
    assert "phase=abilities" in launch
    assert "LAUNCH" in launch.upper() or "entry-level" in launch.lower()
    assert explore != launch


def test_shared_rules_cover_hard_ethics() -> None:
    text = prompts.SHARED_RULES.lower()
    assert "không hỏi" in text
    assert "giới" in text  # ban on gender attribute (not an ask)
    assert "một câu hỏi" in text or "chỉ đúng một" in text
    assert "gpa" in text or "trường" in text
    assert "json" in text


def test_prompts_never_instruct_to_ask_gender() -> None:
    blobs = [
        prompts.SHARED_RULES,
        prompts.EXPLORE_MODE_SECTION,
        prompts.LAUNCH_MODE_SECTION,
        prompts.PROFILER_SYSTEM,
        *(prompts.PHASE_GOALS[p] for p in PHASES),
    ]
    joined = "\n".join(blobs)
    # Must not instruct the model to solicit gender.
    assert not re.search(r"hãy\s+hỏi\s+(về\s+)?giới", joined, re.I)
    assert not re.search(r"hỏi\s+giới\s*tính\s+của", joined, re.I)
    for pat in (r"bạn\s+là\s+nam\s+hay\s+nữ", r"em\s+trai\s+hay\s+gái"):
        assert not re.search(pat, joined, re.I)
    # Ban instruction must remain present (negated form).
    assert re.search(r"không\s+hỏi", joined, re.I)


def test_fallback_banks_cover_all_phases() -> None:
    for phase in PHASES:
        assert phase in prompts.FALLBACK_QUESTIONS
        assert phase in prompts.LAUNCH_FALLBACK_QUESTIONS
        assert len(prompts.FALLBACK_QUESTIONS[phase]) >= 1
        assert len(prompts.LAUNCH_FALLBACK_QUESTIONS[phase]) >= 1
        assert all(q.strip() for q in prompts.FALLBACK_QUESTIONS[phase])
        assert all(q.strip() for q in prompts.LAUNCH_FALLBACK_QUESTIONS[phase])


def test_fallback_rotation_avoids_immediate_repeat_when_possible() -> None:
    bank = prompts.FALLBACK_QUESTIONS["interests"]
    assert len(bank) >= 2
    q0 = prompts.get_fallback_question("explore", "interests", 0)
    q1 = prompts.get_fallback_question("explore", "interests", 1)
    assert q0 == bank[0]
    assert q1 == bank[1]
    assert q0 != q1
    # Wraps
    assert prompts.get_fallback_question("explore", "interests", len(bank)) == bank[0]


def test_launch_and_explore_fallbacks_differ_on_warmup() -> None:
    e = prompts.get_fallback_question("explore", "warmup", 0)
    l = prompts.get_fallback_question("launch", "warmup", 0)
    assert e != l


def test_unknown_phase_falls_back_safely() -> None:
    text = prompts.build_profiler_system("explore", "not-a-phase")
    assert "phase=warmup" in text
    q = prompts.get_fallback_question("explore", "not-a-phase", 0)
    assert isinstance(q, str) and len(q) > 10
