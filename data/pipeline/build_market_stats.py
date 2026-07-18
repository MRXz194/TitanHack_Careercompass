"""[Step 4 / MI-04] Build versioned market aggregates in SQLite.

The builder scans the mapped artifact once. Online services read only aggregate
tables through SQLAlchemy; they never scan JSONL per request.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
)


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.pipeline.extract_skills import read_jsonl, records_hash  # noqa: E402
from data.pipeline.map_careers import UNMAPPED  # noqa: E402


SCHEMA_VERSION = "market-stats-v1-stub"
WINDOW_DAYS = 90
MIN_SALARY_SAMPLES = 5
MIN_TREND_POSTINGS = 10
DEFAULT_INPUT = ROOT_DIR / "data" / "processed" / "postings_mapped.jsonl"
DEFAULT_OUTPUT = ROOT_DIR / "backend" / "market.db"
DEFAULT_KB = ROOT_DIR / "data" / "seed" / "careers_seed.json"

metadata = MetaData()
career_stats = Table(
    "career_stats",
    metadata,
    Column("career_id", String(160), primary_key=True),
    Column("region", String(24), primary_key=True),
    Column("title", String(240), nullable=False),
    Column("demand_count_90d", Integer, nullable=False),
    Column("entry_level_count_90d", Integer, nullable=False),
    Column("salary_p25_trieu", Float),
    Column("salary_p50_trieu", Float),
    Column("salary_p75_trieu", Float),
    Column("salary_sample_count", Integer, nullable=False),
    Column("trend_pct", Float),
    Column("low_confidence", Boolean, nullable=False),
    Column("top_skills_json", Text, nullable=False),
    Column("top_regions_json", Text, nullable=False),
    Column("source_counts_json", Text, nullable=False),
    Column("posting_ids_json", Text, nullable=False),
)
skill_stats = Table(
    "skill_stats",
    metadata,
    Column("skill", String(240), primary_key=True),
    Column("region", String(24), primary_key=True),
    Column("gap_score", Float, nullable=False),
    Column("demand_count", Integer, nullable=False),
    Column("trend_pct", Float),
    Column("low_confidence", Boolean, nullable=False),
    Column("related_careers_json", Text, nullable=False),
    Column("posting_ids_json", Text, nullable=False),
)
market_meta = Table(
    "market_meta",
    metadata,
    Column("key", String(120), primary_key=True),
    Column("value_json", Text, nullable=False),
)


class MarketStatsError(ValueError):
    """Mapped input or build configuration violates the MI-04 contract."""


def percentile(values: list[float], quantile: float) -> float:
    """Return a deterministic linearly interpolated percentile."""
    if not values or not 0 <= quantile <= 1:
        raise MarketStatsError("percentile requires values and quantile in 0..1")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    value = ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
    return round(value, 2)


def _salary_value(posting: dict[str, Any]) -> float | None:
    low = posting.get("salary_min_trieu")
    high = posting.get("salary_max_trieu")
    values = [float(value) for value in (low, high) if value is not None]
    if not values or any(value < 0 for value in values):
        return None
    return sum(values) / len(values)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _aggregate_group(
    rows: list[dict[str, Any]],
    *,
    career_id: str,
    region: str,
    title: str,
    window_end: date,
    top_regions: list[str],
) -> dict[str, Any]:
    salaries = [value for row in rows if (value := _salary_value(row)) is not None]
    early_start = window_end - timedelta(days=WINDOW_DAYS - 1)
    late_start = window_end - timedelta(days=44)
    early = sum(early_start <= row["_posted_date"] < late_start for row in rows)
    late = sum(late_start <= row["_posted_date"] <= window_end for row in rows)
    trend_ready = len(rows) >= MIN_TREND_POSTINGS and early > 0 and late > 0
    trend = round((late - early) / max(early, 5) * 100, 2) if trend_ready else None
    salary_ready = len(salaries) >= MIN_SALARY_SAMPLES
    skill_counts = Counter(skill for row in rows for skill in row["skills"])
    source_counts = Counter(str(row.get("source") or "unknown") for row in rows)
    return {
        "career_id": career_id,
        "region": region,
        "title": title,
        "demand_count_90d": len(rows),
        "entry_level_count_90d": sum(row.get("seniority") == "entry" for row in rows),
        "salary_p25_trieu": percentile(salaries, 0.25) if salary_ready else None,
        "salary_p50_trieu": percentile(salaries, 0.5) if salary_ready else None,
        "salary_p75_trieu": percentile(salaries, 0.75) if salary_ready else None,
        "salary_sample_count": len(salaries),
        "trend_pct": trend,
        "low_confidence": not trend_ready,
        "top_skills_json": _json(
            [
                skill
                for skill, _ in sorted(
                    skill_counts.items(), key=lambda item: (-item[1], item[0])
                )[:10]
            ]
        ),
        "top_regions_json": _json(top_regions),
        "source_counts_json": _json(dict(sorted(source_counts.items()))),
        "posting_ids_json": _json(sorted(row["id"] for row in rows)),
    }


def aggregate_career_stats(
    postings: list[dict[str, Any]],
    career_titles: dict[str, str],
    *,
    window_end: date,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Validate mapped postings and aggregate career × region plus all-region rows."""
    seen: set[str] = set()
    eligible: list[dict[str, Any]] = []
    window_start = window_end - timedelta(days=WINDOW_DAYS - 1)
    for index, raw in enumerate(postings):
        posting = dict(raw)
        posting_id = posting.get("id")
        if not isinstance(posting_id, str) or not posting_id or posting_id in seen:
            raise MarketStatsError(
                f"invalid or duplicate posting id at index {index}: {posting_id}"
            )
        seen.add(posting_id)
        if not isinstance(posting.get("skills"), list) or not isinstance(
            posting.get("career_id"), str
        ):
            raise MarketStatsError(f"posting {posting_id} lacks skills[] or career_id")
        try:
            posting["_posted_date"] = date.fromisoformat(posting["posted_date"])
        except (KeyError, TypeError, ValueError) as exc:
            raise MarketStatsError(f"posting {posting_id} has invalid posted_date") from exc
        if window_start <= posting["_posted_date"] <= window_end:
            eligible.append(posting)

    mapped = [row for row in eligible if row["career_id"] != UNMAPPED]
    unknown = sorted({row["career_id"] for row in mapped} - career_titles.keys())
    if unknown:
        raise MarketStatsError(f"career IDs absent from KB: {unknown}")

    by_career: dict[str, list[dict[str, Any]]] = defaultdict(list)
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in mapped:
        by_career[row["career_id"]].append(row)
        groups[(row["career_id"], "all")].append(row)
        groups[(row["career_id"], str(row.get("region") or "other"))].append(row)

    output: list[dict[str, Any]] = []
    for (career_id, region), rows in sorted(groups.items()):
        region_counts = Counter(
            str(row.get("region") or "other") for row in by_career[career_id]
        )
        top_regions = [
            name
            for name, _ in sorted(
                region_counts.items(), key=lambda item: (-item[1], item[0])
            )
        ]
        output.append(
            _aggregate_group(
                rows,
                career_id=career_id,
                region=region,
                title=career_titles[career_id],
                window_end=window_end,
                top_regions=top_regions,
            )
        )

    meta = {
        "schema_version": SCHEMA_VERSION,
        "postings_count": len(eligible),
        "mapped_postings_count": len(mapped),
        "unmapped_postings_count": len(eligible) - len(mapped),
        "window_days": WINDOW_DAYS,
        "window_end": window_end.isoformat(),
        "source_counts": dict(
            sorted(
                Counter(str(row.get("source") or "unknown") for row in eligible).items()
            )
        ),
        "region_counts": dict(
            sorted(
                Counter(str(row.get("region") or "other") for row in eligible).items()
            )
        ),
        "career_row_count": len(output),
        "salary_min_samples": MIN_SALARY_SAMPLES,
        "trend_formula": "(late45-early45)/max(early45,5)*100",
        "limitations": [
            "Observed posting demand is not labor-supply shortage.",
            "Unmapped postings are excluded from career aggregates but counted in metadata.",
        ],
    }
    return output, meta


def aggregate_skill_stats(
    postings: list[dict[str, Any]],
    *,
    window_end: date,
) -> list[dict[str, Any]]:
    """MI-05: per (skill, region) demand + trend, mirroring aggregate_career_stats'
    windowing/trend-readiness rules. Independent from aggregate_career_stats (not
    sharing its `eligible` list) so that function's tested contract stays untouched;
    this re-applies the same window filter over the same already-id-validated postings.

    gap_score = demand_count normalized against the busiest skill in the SAME region
    (0..1) -- a demand-signal ranking score, not a claim about labor scarcity (see
    CLAUDE.md hard rule #9 "never overclaim gap_score").
    """
    window_start = window_end - timedelta(days=WINDOW_DAYS - 1)
    eligible: list[dict[str, Any]] = []
    for raw in postings:
        posting = dict(raw)
        posting["_posted_date"] = date.fromisoformat(posting["posted_date"])
        if window_start <= posting["_posted_date"] <= window_end:
            eligible.append(posting)

    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        region = str(row.get("region") or "other")
        career_id = row.get("career_id")
        for skill in row.get("skills") or []:
            groups[(skill, region)].append(row)
            groups[(skill, "all")].append(row)

    max_demand_by_region: dict[str, int] = defaultdict(int)
    for (_, region), rows in groups.items():
        max_demand_by_region[region] = max(max_demand_by_region[region], len(rows))

    early_start = window_end - timedelta(days=WINDOW_DAYS - 1)
    late_start = window_end - timedelta(days=44)
    output: list[dict[str, Any]] = []
    for (skill, region), rows in sorted(groups.items()):
        early = sum(early_start <= row["_posted_date"] < late_start for row in rows)
        late = sum(late_start <= row["_posted_date"] <= window_end for row in rows)
        trend_ready = len(rows) >= MIN_TREND_POSTINGS and early > 0 and late > 0
        trend = round((late - early) / max(early, 5) * 100, 2) if trend_ready else None
        related_careers = sorted(
            {row["career_id"] for row in rows if row.get("career_id") != UNMAPPED}
        )[:5]
        max_demand = max(max_demand_by_region[region], 1)
        output.append(
            {
                "skill": skill,
                "region": region,
                "gap_score": round(min(1.0, len(rows) / max_demand), 4),
                "demand_count": len(rows),
                "trend_pct": trend,
                "low_confidence": not trend_ready,
                "related_careers_json": _json(related_careers),
                "posting_ids_json": _json(sorted(row["id"] for row in rows)),
            }
        )
    return output


def build_database(
    output: Path,
    rows: list[dict[str, Any]],
    meta: dict[str, Any],
    skill_rows: list[dict[str, Any]] | None = None,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{output}")
    metadata.drop_all(engine)
    metadata.create_all(engine)
    with engine.begin() as connection:
        if rows:
            connection.execute(career_stats.insert(), rows)
        if skill_rows:
            connection.execute(skill_stats.insert(), skill_rows)
        connection.execute(
            market_meta.insert(),
            [
                {"key": key, "value_json": _json(value)}
                for key, value in sorted(meta.items())
            ],
        )
    engine.dispose()


def _load_titles(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {career["career_id"]: career["title"] for career in raw["careers"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--kb", type=Path, default=DEFAULT_KB)
    parser.add_argument("--expected-input-hash")
    parser.add_argument("--window-end", type=date.fromisoformat)
    parser.add_argument("--snapshot-id", default="provisional")
    parser.add_argument("--snapshot-sha256", default="unverified")
    parser.add_argument("--provisional", action="store_true")
    args = parser.parse_args(argv)
    try:
        postings = read_jsonl(args.input)
        input_hash = records_hash(postings)
        if not args.provisional and not args.expected_input_hash:
            raise MarketStatsError("production build requires --expected-input-hash")
        if args.expected_input_hash and args.expected_input_hash != input_hash:
            raise MarketStatsError(
                f"input hash mismatch: expected {args.expected_input_hash}, got {input_hash}"
            )
        inferred_end = max(date.fromisoformat(row["posted_date"]) for row in postings)
        window_end = args.window_end or inferred_end
        rows, meta = aggregate_career_stats(
            postings, _load_titles(args.kb), window_end=window_end
        )
        skill_rows = aggregate_skill_stats(postings, window_end=window_end)
        meta.update(
            {
                "input_content_hash": input_hash,
                "snapshot_id": args.snapshot_id,
                "snapshot_sha256": args.snapshot_sha256,
                "skill_row_count": len(skill_rows),
            }
        )
        build_database(args.output, rows, meta, skill_rows)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
