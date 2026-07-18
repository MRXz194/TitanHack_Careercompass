"""SQLAlchemy-only market aggregate reader for MI-04/MI-05.

Reads market.db built by data/pipeline/build_market_stats.py (M3's real
crawl -> extract_skills -> map_careers -> build_market_stats pipeline).
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import MetaData, Table, select
from sqlalchemy.engine import Engine

from app.core import db as db_module
from app.models.schemas import (
    DemandCareer,
    MarketOverview,
    MarketStats,
    RisingCareer,
    SkillGapItem,
    SkillGapResponse,
    TopPayingCareer,
)


class MarketDataUnavailable(RuntimeError):
    """The aggregate DB is missing or does not have the MI-04 schema."""


def _tables(engine: Engine) -> tuple[Table, Table]:
    metadata = MetaData()
    try:
        stats = Table("career_stats", metadata, autoload_with=engine)
        meta = Table("market_meta", metadata, autoload_with=engine)
    except Exception as exc:
        raise MarketDataUnavailable("market aggregate tables are unavailable") from exc
    return stats, meta


def _skill_stats_table(engine: Engine) -> Table:
    metadata = MetaData()
    try:
        return Table("skill_stats", metadata, autoload_with=engine)
    except Exception as exc:
        raise MarketDataUnavailable("skill_stats table is unavailable") from exc


def _meta_values(connection: Any, table: Table) -> dict[str, Any]:
    try:
        return {
            row.key: json.loads(row.value_json)
            for row in connection.execute(select(table.c.key, table.c.value_json))
        }
    except (TypeError, json.JSONDecodeError) as exc:
        raise MarketDataUnavailable("market metadata is invalid") from exc


def _source_note(postings_count: int, meta: dict[str, Any]) -> str:
    snapshot = meta.get("snapshot_id", "snapshot chưa xác minh")
    formatted_count = f"{postings_count:,}".replace(",", ".")
    return f"Từ {formatted_count} tin tuyển dụng quan sát, {snapshot}"


def get_market_meta(*, engine: Engine | None = None) -> dict[str, Any]:
    """Used by /api/health to report whether the real pipeline output is loaded."""
    engine = engine or db_module.market_engine
    _, meta_table = _tables(engine)
    with engine.connect() as connection:
        meta = _meta_values(connection, meta_table)
    if not meta:
        raise MarketDataUnavailable("market metadata is empty")
    return meta


def get_overview(region: str, *, engine: Engine | None = None) -> MarketOverview:
    engine = engine or db_module.market_engine
    stats, meta_table = _tables(engine)
    with engine.connect() as connection:
        meta = _meta_values(connection, meta_table)
        rows = connection.execute(
            select(stats).where(stats.c.region == region)
        ).mappings().all()
    if not meta:
        raise MarketDataUnavailable("market metadata is empty")
    region_counts = meta.get("region_counts", {})
    postings_count = int(
        meta.get("postings_count", 0)
        if region == "all"
        else region_counts.get(region, 0)
    )
    rising = [row for row in rows if row["trend_pct"] is not None]
    rising.sort(
        key=lambda row: (
            -row["trend_pct"],
            -row["demand_count_90d"],
            row["career_id"],
        )
    )
    paying = [row for row in rows if row["salary_p50_trieu"] is not None]
    paying.sort(key=lambda row: (-row["salary_p50_trieu"], row["career_id"]))
    demand = sorted(
        rows,
        key=lambda row: (-row["demand_count_90d"], row["career_id"]),
    )
    return MarketOverview(
        region=region,
        postings_count=postings_count,
        window_days=int(meta.get("window_days", 90)),
        updated_at=str(meta.get("window_end", "unknown")),
        source_note=_source_note(postings_count, meta),
        rising_careers=[
            RisingCareer(
                career_id=row["career_id"],
                title=row["title"],
                trend_pct=row["trend_pct"],
                demand_count=row["demand_count_90d"],
                low_confidence=bool(row["low_confidence"]),
            )
            for row in rising[:8]
        ],
        # Demand volume is a one-window observation, not a growth claim. Keep it
        # separate so a fresh snapshot remains useful without inventing a trend.
        demand_leaders=[
            DemandCareer(
                career_id=row["career_id"],
                title=row["title"],
                demand_count=row["demand_count_90d"],
                low_confidence=bool(row["low_confidence"]),
            )
            for row in demand[:8]
        ],
        top_paying=[
            TopPayingCareer(
                career_id=row["career_id"],
                title=row["title"],
                salary_p50_trieu=row["salary_p50_trieu"],
            )
            for row in paying[:5]
        ],
    )


def get_career_market(
    career_id: str, region: str, *, engine: Engine | None = None
) -> MarketStats:
    engine = engine or db_module.market_engine
    stats, meta_table = _tables(engine)
    with engine.connect() as connection:
        meta = _meta_values(connection, meta_table)
        row = connection.execute(
            select(stats).where(
                stats.c.career_id == career_id,
                stats.c.region == region,
            )
        ).mappings().first()
        all_row = connection.execute(
            select(stats).where(
                stats.c.career_id == career_id,
                stats.c.region == "all",
            )
        ).mappings().first()
    if not meta:
        raise MarketDataUnavailable("market metadata is empty")
    if row is None and all_row is not None:
        # Region informs, never filters: no per-region slice for this career, but the
        # same snapshot HAS real national data. Showing a dead "0 tin tuyển" wall for
        # every card just because the student named a region made all results look
        # identical/broken. Fall back to the national row, labeled honestly.
        row = all_row
        note_suffix = " (toàn quốc — chưa đủ dữ liệu riêng theo khu vực)"
    else:
        note_suffix = ""
    if row is None:
        # Career absent from the snapshot entirely: honest zero, never seed numbers.
        return MarketStats(
            demand_count_90d=0,
            low_confidence=True,
            top_regions=[],
            source_note=_source_note(0, meta),
        )
    return MarketStats(
        demand_count_90d=row["demand_count_90d"],
        entry_level_count_90d=row["entry_level_count_90d"],
        salary_p25_trieu=row["salary_p25_trieu"],
        salary_p50_trieu=row["salary_p50_trieu"],
        salary_p75_trieu=row["salary_p75_trieu"],
        trend_pct=row["trend_pct"],
        salary_sample_count=row["salary_sample_count"],
        low_confidence=bool(row["low_confidence"]),
        top_regions=json.loads(row["top_regions_json"]),
        top_skills=json.loads(row["top_skills_json"]),
        source_note=_source_note(row["demand_count_90d"], meta) + note_suffix,
    )


def get_skill_gaps(region: str, *, engine: Engine | None = None) -> SkillGapResponse:
    """MI-05: read skill_stats (built alongside career_stats by build_market_stats.py)."""
    engine = engine or db_module.market_engine
    skill_stats = _skill_stats_table(engine)
    _, meta_table = _tables(engine)
    with engine.connect() as connection:
        meta = _meta_values(connection, meta_table)
        rows = connection.execute(
            select(skill_stats).where(skill_stats.c.region == region)
        ).mappings().all()
    if not meta:
        raise MarketDataUnavailable("market metadata is empty")
    ranked = sorted(rows, key=lambda row: (-row["gap_score"], row["skill"]))[:20]
    postings_count = int(meta.get("postings_count", 0))
    return SkillGapResponse(
        region=region,
        source_note=_source_note(postings_count, meta),
        skills=[
            SkillGapItem(
                skill=row["skill"],
                gap_score=row["gap_score"],
                demand_count=row["demand_count"],
                trend_pct=row["trend_pct"],
                low_confidence=bool(row["low_confidence"]),
                related_careers=json.loads(row["related_careers_json"]),
            )
            for row in ranked
        ],
    )
