"""MI-04 aggregate formulas, null behavior, and artifact guards."""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from data.pipeline.build_market_stats import (  # noqa: E402
    MarketStatsError,
    aggregate_career_stats,
    main,
)
from data.pipeline.extract_skills import records_hash  # noqa: E402


pytestmark = pytest.mark.unit
WINDOW_END = date(2026, 7, 17)


def _posting(
    index: int,
    *,
    career_id: str = "data-analyst",
    region: str = "hanoi",
    days_ago: int,
    salary: float,
) -> dict:
    return {
        "id": f"fixture-{career_id}-{index}",
        "source": "fixture",
        "career_id": career_id,
        "region": region,
        "posted_date": (WINDOW_END - timedelta(days=days_ago)).isoformat(),
        "salary_min_trieu": salary,
        "salary_max_trieu": salary,
        "seniority": "entry" if index < 3 else "mid",
        "skills": ["SQL", "Microsoft Excel" if index % 2 else "Python"],
    }


def test_aggregate_percentiles_trend_entry_count_and_low_sample_nulls() -> None:
    data_rows = [
        _posting(index, days_ago=day, salary=float(index + 1))
        for index, day in enumerate([80, 70, 60, 50, 45, 20, 15, 12, 10, 8, 5, 1])
    ]
    small_rows = [
        _posting(
            index,
            career_id="lap-trinh-vien-web",
            region="danang",
            days_ago=day,
            salary=20 + index,
        )
        for index, day in enumerate([80, 60, 10, 1])
    ]
    rows, meta = aggregate_career_stats(
        data_rows + small_rows,
        {
            "data-analyst": "Chuyên viên Phân tích Dữ liệu",
            "lap-trinh-vien-web": "Lập trình viên Web",
        },
        window_end=WINDOW_END,
    )

    data_all = next(
        row for row in rows if row["career_id"] == "data-analyst" and row["region"] == "all"
    )
    assert data_all["demand_count_90d"] == 12
    assert data_all["entry_level_count_90d"] == 3
    assert data_all["salary_sample_count"] == 12
    assert data_all["salary_p50_trieu"] == 6.5
    assert data_all["trend_pct"] == 40.0
    assert data_all["low_confidence"] is False
    assert json.loads(data_all["top_skills_json"])[0] == "SQL"

    small_all = next(
        row
        for row in rows
        if row["career_id"] == "lap-trinh-vien-web" and row["region"] == "all"
    )
    assert small_all["salary_sample_count"] == 4
    assert small_all["salary_p25_trieu"] is None
    assert small_all["salary_p50_trieu"] is None
    assert small_all["salary_p75_trieu"] is None
    assert small_all["trend_pct"] is None
    assert small_all["low_confidence"] is True
    assert meta["postings_count"] == 16


def test_aggregate_rejects_duplicate_posting_ids() -> None:
    posting = _posting(1, days_ago=1, salary=10)
    with pytest.raises(MarketStatsError, match="duplicate posting id"):
        aggregate_career_stats(
            [posting, posting],
            {"data-analyst": "Chuyên viên Phân tích Dữ liệu"},
            window_end=WINDOW_END,
        )


def test_cli_guards_input_hash_then_builds_pinned_database(tmp_path: Path) -> None:
    posting = _posting(1, days_ago=1, salary=10)
    input_path = tmp_path / "mapped.jsonl"
    input_path.write_text(
        json.dumps(posting, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "market.db"
    args = ["--input", str(input_path), "--output", str(output_path)]
    assert main(args) == 1
    assert main(args + ["--expected-input-hash", "sha256:wrong"]) == 1
    assert not output_path.exists()
    assert main(args + ["--expected-input-hash", records_hash([posting])]) == 0
    assert output_path.exists()
