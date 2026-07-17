"""MI-08 salary, trend, duplicate, and source-dominance guardrails."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from data.pipeline.build_market_stats import (  # noqa: E402
    MAX_ABS_TREND_PCT,
    MarketStatsError,
    aggregate_career_stats,
    aggregate_skill_stats,
    build_guardrail_report,
)


pytestmark = pytest.mark.unit
WINDOW_END = date(2026, 7, 17)
TITLES = {"data-analyst": "Chuyên viên Phân tích Dữ liệu"}


def _posting(
    posting_id: str,
    *,
    days_ago: int,
    source: str,
    salary: float | None = None,
) -> dict:
    return {
        "id": posting_id,
        "source": source,
        "career_id": "data-analyst",
        "region": "hanoi",
        "posted_date": (WINDOW_END - timedelta(days=days_ago)).isoformat(),
        "salary_min_trieu": salary,
        "salary_max_trieu": salary,
        "seniority": "entry",
        "skills": ["SQL"],
    }


def _all_career_row(postings: list[dict]) -> dict:
    rows, _ = aggregate_career_stats(postings, TITLES, window_end=WINDOW_END)
    return next(row for row in rows if row["region"] == "all")


def test_negative_and_high_salary_are_hidden_not_clamped() -> None:
    salaries = [-5, 1_000, 10, 12, 14, 16, 18]
    postings = [
        _posting(
            f"salary-{index}",
            days_ago=index + 1,
            source=f"source-{index % 2}",
            salary=salary,
        )
        for index, salary in enumerate(salaries)
    ]
    row = _all_career_row(postings)
    assert row["salary_observed_count"] == 7
    assert row["salary_excluded_count"] == 2
    assert row["salary_sample_count"] == 5
    assert row["salary_p25_trieu"] == 12
    assert row["salary_p50_trieu"] == 14
    assert row["salary_p75_trieu"] == 16

    skill_rows = aggregate_skill_stats(postings, window_end=WINDOW_END)
    report = build_guardrail_report(
        postings, [row], skill_rows, window_end=WINDOW_END
    )
    assert report["guardrail_exclusions"]["salary_nonpositive_or_nonfinite"] == 1
    assert report["guardrail_exclusions"]["salary_above_guardrail"] == 1
    assert report["salary_coverage"] == {
        "posting_denominator": 7,
        "observed_count": 7,
        "valid_count": 5,
        "excluded_count": 2,
    }


def test_extreme_trend_is_preserved_raw_but_hidden_from_api_field() -> None:
    days = [80, 70, 60, 50, 45] + list(range(31))
    postings = [
        _posting(
            f"trend-{index}",
            days_ago=day,
            source=f"source-{index % 2}",
        )
        for index, day in enumerate(days)
    ]
    row = _all_career_row(postings)
    assert row["raw_trend_pct"] > MAX_ABS_TREND_PCT
    assert row["trend_pct"] is None
    assert row["low_confidence"] is True
    skill = next(
        item
        for item in aggregate_skill_stats(postings, window_end=WINDOW_END)
        if item["skill"] == "SQL" and item["region"] == "all"
    )
    assert skill["raw_trend_pct"] == row["raw_trend_pct"]
    assert skill["trend_pct"] is None
    assert skill["gap_score"] == 1.0


def test_source_dominance_hides_trend_and_report_compares_sources() -> None:
    days = [80, 70, 60, 50, 45, 20, 15, 10, 5, 1]
    postings = [
        _posting(
            f"source-{index}",
            days_ago=day,
            source="dominant" if index < 9 else "minority",
            salary=10 + index,
        )
        for index, day in enumerate(days)
    ]
    career_rows, _ = aggregate_career_stats(postings, TITLES, window_end=WINDOW_END)
    row = next(item for item in career_rows if item["region"] == "all")
    assert row["raw_trend_pct"] == 0
    assert row["trend_pct"] is None
    assert row["source_dominance_ratio"] == 0.9
    assert row["source_dominant"] is True
    assert row["low_confidence"] is True

    skill_rows = aggregate_skill_stats(postings, window_end=WINDOW_END)
    report = build_guardrail_report(
        postings, career_rows, skill_rows, window_end=WINDOW_END
    )
    assert report["source_only_comparison"]["dominant"]["postings"] == 9
    assert report["source_only_comparison"]["minority"]["share"] == 0.1
    assert report["source_dominant_career_rows"] >= 1


def test_duplicate_is_counted_in_report_and_rejected_by_builder() -> None:
    posting = _posting("duplicate", days_ago=1, source="fixture", salary=10)
    report = build_guardrail_report(
        [posting, posting], [], [], window_end=WINDOW_END
    )
    assert report["guardrail_exclusions"]["duplicate_postings"] == 1
    with pytest.raises(MarketStatsError, match="duplicate posting id"):
        aggregate_career_stats(
            [posting, posting], TITLES, window_end=WINDOW_END
        )
