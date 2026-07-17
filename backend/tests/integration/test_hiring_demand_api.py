"""MI-05 aggregate → SQLite → service/router handoff."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from app.core import db as db_module
from app.routers import market as market_router


ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from data.pipeline.build_market_stats import (  # noqa: E402
    aggregate_career_stats,
    aggregate_skill_stats,
    build_database,
)


pytestmark = pytest.mark.integration


def test_skill_radar_reads_live_rows_limits_top_20_and_handles_empty_region(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    window_end = date(2026, 7, 17)
    skills = [f"skill-{index:02d}" for index in range(25)]
    postings = [
        {
            "id": f"skill-api-{index}",
            "source": "fixture",
            "career_id": "data-analyst",
            "region": "hanoi",
            "posted_date": (window_end - timedelta(days=day)).isoformat(),
            "salary_min_trieu": None,
            "salary_max_trieu": None,
            "seniority": "entry",
            "skills": skills,
        }
        for index, day in enumerate([80, 70, 60, 50, 45, 20, 15, 12, 10, 8, 5, 1])
    ]
    career_rows, meta = aggregate_career_stats(
        postings,
        {"data-analyst": "Chuyên viên Phân tích Dữ liệu"},
        window_end=window_end,
    )
    skill_rows = aggregate_skill_stats(postings, window_end=window_end)
    meta.update(
        {
            "snapshot_id": "fixture-mi05",
            "skill_row_count": len(skill_rows),
            "gap_score_formula": "fixture uses production formula",
        }
    )
    db_path = tmp_path / "market.db"
    build_database(db_path, career_rows, meta, skill_rows)
    engine = create_engine(f"sqlite:///{db_path}")
    monkeypatch.setattr(db_module, "market_engine", engine)

    radar = market_router.skill_gaps("hanoi")
    assert len(radar.skills) == 20
    assert [item.skill for item in radar.skills] == skills[:20]
    assert all(item.gap_score == 1.0 for item in radar.skills)
    assert all(item.low_confidence is False for item in radar.skills)
    assert all(item.related_careers == ["data-analyst"] for item in radar.skills)
    assert "fixture-mi05" in radar.source_note

    empty = market_router.skill_gaps("danang")
    assert empty.skills == []
    engine.dispose()

