"""MI-04 SQLite build → SQLAlchemy reader → public API contract."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from app.core import db as db_module
from app.routers import market as market_router
from app.services import market as market_service


ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from data.pipeline.build_market_stats import (  # noqa: E402
    aggregate_career_stats,
    build_database,
)


pytestmark = pytest.mark.integration


def test_api_reads_aggregate_db_and_handles_empty_region(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    window_end = date(2026, 7, 17)
    postings = [
        {
            "id": f"api-fixture-{index}",
            "source": "fixture",
            "career_id": "data-analyst",
            "region": "hanoi",
            "posted_date": (window_end - timedelta(days=day)).isoformat(),
            "salary_min_trieu": 10 + index,
            "salary_max_trieu": 10 + index,
            "seniority": "entry" if index < 4 else "mid",
            "skills": ["SQL", "Microsoft Excel"],
        }
        for index, day in enumerate([80, 70, 60, 50, 45, 20, 15, 12, 10, 8, 5, 1])
    ]
    rows, meta = aggregate_career_stats(
        postings,
        {"data-analyst": "Chuyên viên Phân tích Dữ liệu"},
        window_end=window_end,
    )
    meta.update({"snapshot_id": "fixture-mi04", "snapshot_sha256": "sha256:fixture"})
    db_path = tmp_path / "market.db"
    build_database(db_path, rows, meta)
    engine = create_engine(f"sqlite:///{db_path}")
    monkeypatch.setattr(db_module, "market_engine", engine)

    overview = market_router.overview("hanoi")
    assert overview.postings_count == 12
    assert overview.rising_careers[0].career_id == "data-analyst"
    assert overview.demand_leaders[0].career_id == "data-analyst"
    assert overview.demand_leaders[0].demand_count == 12
    assert "fixture-mi04" in overview.source_note

    detail = market_router.career_detail("data-analyst", "all")
    assert detail.market.salary_sample_count == 12
    assert detail.market.salary_p50_trieu == 15.5

    empty = market_router.overview("danang")
    assert empty.postings_count == 0
    assert empty.rising_careers == []
    assert empty.demand_leaders == []

    # A career absent from a valid real snapshot must return an honest zero,
    # never silently mix in seed demand/salary numbers.
    absent = market_service.get_career_market("lap-trinh-vien-web", "all")
    assert absent.demand_count_90d == 0
    assert absent.salary_p50_trieu is None
    assert absent.low_confidence is True
    assert "fixture-mi04" in absent.source_note

    # Region informs, never filters: a career that HAS national data but no row
    # for the student's region must fall back to the (real) national stats with
    # an honest note — not display a dead "0 tin tuyển" wall for every card,
    # which made all results look identical/broken for any region-pref user.
    regional_fallback = market_service.get_career_market("data-analyst", "danang")
    assert regional_fallback.demand_count_90d == 12
    assert regional_fallback.salary_p50_trieu == 15.5
    assert "toàn quốc" in regional_fallback.source_note
    engine.dispose()
