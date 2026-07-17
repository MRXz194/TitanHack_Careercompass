"""MI-05 confidence-aware hiring-demand proxy tests."""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from data.pipeline.build_market_stats import aggregate_skill_stats  # noqa: E402


pytestmark = pytest.mark.unit
WINDOW_END = date(2026, 7, 17)


def _posting(
    posting_id: str,
    *,
    days_ago: int,
    skills: list[str],
    career_id: str = "data-analyst",
    region: str = "hanoi",
) -> dict:
    return {
        "id": posting_id,
        "career_id": career_id,
        "region": region,
        "posted_date": (WINDOW_END - timedelta(days=days_ago)).isoformat(),
        "skills": skills,
    }


def test_proxy_is_bounded_monotonic_and_confidence_aware() -> None:
    rows: list[dict] = []
    growth_days = [80, 70, 60, 50, 45, 30, 20, 15, 12, 10, 8, 6, 4, 2, 1]
    for index, day in enumerate(growth_days):
        skills = ["SQL"]
        if index < 8:
            skills.append("Microsoft Excel")
        if index >= 11:
            skills.append("Python")
        rows.append(_posting(f"growth-{index}", days_ago=day, skills=skills))

    rows.extend(
        _posting(
            f"recent-{index}",
            days_ago=index + 1,
            skills=["NoTrend"],
            career_id="lap-trinh-vien-web",
        )
        for index in range(10)
    )
    rows.extend(
        _posting(
            f"declining-{index}",
            days_ago=80 - index if index < 7 else index,
            skills=["Declining"],
        )
        for index in range(10)
    )
    rows.extend(
        _posting(
            f"tiny-{index}",
            days_ago=index + 1,
            skills=["TinyRegion"],
            region="danang",
        )
        for index in range(2)
    )

    stats = aggregate_skill_stats(rows, window_end=WINDOW_END)
    all_rows = {row["skill"]: row for row in stats if row["region"] == "all"}
    assert all(0 <= row["gap_score"] <= 1 for row in stats)
    assert all_rows["SQL"]["gap_score"] == 1.0
    assert all_rows["SQL"]["low_confidence"] is False
    assert all_rows["NoTrend"]["trend_pct"] is None
    assert all_rows["NoTrend"]["low_confidence"] is True
    assert all_rows["NoTrend"]["gap_score"] > all_rows["Microsoft Excel"]["gap_score"]
    assert all_rows["Microsoft Excel"]["gap_score"] > all_rows["Python"]["gap_score"]
    assert all_rows["Declining"]["trend_pct"] < 0
    assert all_rows["Declining"]["gap_score"] < all_rows["NoTrend"]["gap_score"]
    assert json.loads(all_rows["SQL"]["related_careers_json"]) == ["data-analyst"]

    tiny = next(
        row
        for row in stats
        if row["skill"] == "TinyRegion" and row["region"] == "danang"
    )
    assert tiny["low_confidence"] is True
    assert tiny["gap_score"] == 0.2


def test_proxy_rejects_duplicate_skills_within_posting() -> None:
    with pytest.raises(ValueError, match="invalid skills"):
        aggregate_skill_stats(
            [_posting("duplicate-skills", days_ago=1, skills=["SQL", "SQL"])],
            window_end=WINDOW_END,
        )

