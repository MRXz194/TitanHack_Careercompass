"""Market stats reader — task MI-04/MI-05. Reads market.db (built by
data/pipeline/build_market_stats.py from real crawled+processed postings).

Raises MarketDataUnavailable when market.db is missing/empty/stale-schema so the
router (app/routers/market.py) can fall back to seed data without ever 500ing.
"""
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import text

from app.core.db import market_engine
from app.models.schemas import (MarketOverview, RisingCareer, SkillGapItem,
                                SkillGapResponse, TopPayingCareer)
from app.data.seed_loader import load_careers

SOURCE_NOTE_TEMPLATE = (
    "Từ {n} tin tuyển dụng thật (TopCV/ITviec/VietnamWorks), crawl 1 lần "
    "({date}) — chưa đủ dữ liệu đa thời điểm nên KHÔNG hiển thị xu hướng (trend)."
)


class MarketDataUnavailable(Exception):
    """market.db missing, empty, or built before the current schema — caller should fall back."""


def _db_exists() -> bool:
    url = str(market_engine.url)
    if not url.startswith("sqlite"):
        return True  # non-sqlite backend: assume reachable, let query errors surface normally
    path = url.split("sqlite:///", 1)[-1]
    return Path(path).exists()


def _get_meta() -> dict:
    with market_engine.connect() as conn:
        row = conn.execute(text(
            "SELECT postings_count, window_days, built_at, career_mapping_coverage_pct "
            "FROM meta LIMIT 1"
        )).mappings().first()
    if row is None:
        raise MarketDataUnavailable("meta table empty")
    return dict(row)


def get_market_meta() -> dict:
    """Used by /api/health to report whether the real pipeline output is loaded."""
    if not _db_exists():
        raise MarketDataUnavailable("market.db not found")
    return _get_meta()


def _title_for(career_id: str) -> str:
    for c in load_careers():
        if c["career_id"] == career_id:
            return c["title"]
    return career_id


def get_overview(region: str) -> MarketOverview:
    if not _db_exists():
        raise MarketDataUnavailable("market.db not found")
    meta = _get_meta()
    region_filter = region if region != "all" else "all"

    with market_engine.connect() as conn:
        rising_rows = conn.execute(text(
            "SELECT career_id, demand_count, low_confidence FROM career_stats "
            "WHERE region = :region AND demand_count > 0 "
            "ORDER BY demand_count DESC LIMIT 8"
        ), {"region": region_filter}).mappings().all()

        paying_rows = conn.execute(text(
            "SELECT career_id, salary_p50 FROM career_stats "
            "WHERE region = :region AND salary_p50 IS NOT NULL "
            "ORDER BY salary_p50 DESC LIMIT 5"
        ), {"region": region_filter}).mappings().all()

    if not rising_rows and not paying_rows:
        raise MarketDataUnavailable(f"no career_stats rows for region={region_filter}")

    source_note = SOURCE_NOTE_TEMPLATE.format(n=meta["postings_count"], date=meta["built_at"][:10])
    return MarketOverview(
        region=region, postings_count=meta["postings_count"], window_days=meta["window_days"],
        updated_at=meta["built_at"][:10], source_note=source_note,
        rising_careers=[
            # trend_pct is always 0.0 (sentinel, never a real signal — single-snapshot crawl,
            # see module docstring). RisingCareer.trend_pct is non-optional so it can't be NULL;
            # the FE never renders "▲0.0%" (it special-cases trend_pct===0), so this sentinel is
            # safe. low_confidence here is the REAL demand-sample-size signal (< 10 postings),
            # independent of trend availability — a well-sampled career must not be mislabeled
            # "hạn chế" just because trend can't be computed.
            RisingCareer(career_id=r["career_id"], title=_title_for(r["career_id"]),
                        trend_pct=0.0, demand_count=r["demand_count"],
                        low_confidence=bool(r["low_confidence"]))
            for r in rising_rows
        ],
        top_paying=[
            TopPayingCareer(career_id=r["career_id"], title=_title_for(r["career_id"]),
                            salary_p50_trieu=r["salary_p50"])
            for r in paying_rows
        ],
    )


def get_skill_gaps(region: str) -> SkillGapResponse:
    if not _db_exists():
        raise MarketDataUnavailable("market.db not found")
    meta = _get_meta()
    region_filter = region if region != "all" else "all"

    with market_engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT skill, demand_count, gap_score, low_confidence, related_careers_json "
            "FROM skill_stats WHERE region = :region ORDER BY gap_score DESC LIMIT 20"
        ), {"region": region_filter}).mappings().all()

    if not rows:
        raise MarketDataUnavailable(f"no skill_stats rows for region={region_filter}")

    source_note = SOURCE_NOTE_TEMPLATE.format(n=meta["postings_count"], date=meta["built_at"][:10])
    return SkillGapResponse(
        region=region, source_note=source_note,
        skills=[
            SkillGapItem(skill=r["skill"], gap_score=r["gap_score"], demand_count=r["demand_count"],
                        trend_pct=None, low_confidence=bool(r["low_confidence"]),
                        related_careers=json.loads(r["related_careers_json"]))
            for r in rows
        ],
    )
