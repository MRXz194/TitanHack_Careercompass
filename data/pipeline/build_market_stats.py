"""[Bước 4] Market stats — task MI-04/MI-05. Design: docs/AI_DESIGN.md §3.

Input:  data/processed/postings.jsonl (M2, has `skills` from MI-02/03 dict-tier extraction)
        data/seed/careers_seed.json (`title_patterns` used for posting -> career_id mapping,
        since postings.jsonl has no career_id field yet — see manifest career_mapping_coverage_pct: 0.0)
Output: backend/market.db (SQLite) — tables career_stats, skill_stats, meta.

Honesty guard (CLAUDE.md hard rule #2 "no invented numbers", #9 "never overclaim"):
this crawl is a SINGLE snapshot (posted_date is ~98% one day — see manifest), so a real
trend_pct (45-day-early vs 45-day-late split, per AI_DESIGN.md §3) is NOT computable from
this dataset. Every row is written with trend_pct=NULL and low_confidence=1 rather than a
fabricated or misleading number. demand_count/salary are real aggregates of real postings.

Run (from repo root, backend venv active):
    python data/pipeline/build_market_stats.py
"""
import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
POSTINGS_PATH = ROOT / "data" / "processed" / "postings.jsonl"
CAREERS_SEED_PATH = ROOT / "data" / "seed" / "careers_seed.json"
DB_PATH = ROOT / "backend" / "market.db"

REGIONS = ["hanoi", "hcm", "danang", "other"]
MIN_SALARY_SAMPLES = 5  # below this -> salary_* stay NULL (contract: no invented numbers)
MIN_DEMAND_SAMPLES = 10  # below this -> low_confidence stays true regardless


def _norm(text: str) -> str:
    return unicodedata.normalize("NFC", text or "").lower()


def load_postings() -> list[dict]:
    postings = []
    with POSTINGS_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                postings.append(json.loads(line))
    return postings


def load_careers() -> list[dict]:
    return json.loads(CAREERS_SEED_PATH.read_text(encoding="utf-8"))["careers"]


def map_career_id(title: str, careers: list[dict]) -> str | None:
    """Rule-based mapping via title_patterns substring match (AI_DESIGN.md §2)."""
    t = _norm(title)
    for career in careers:
        for pattern in career["title_patterns"]:
            if _norm(pattern) in t:
                return career["career_id"]
    return None


def percentile(values: list[float], p: float) -> float:
    if not values:
        raise ValueError("empty")
    s = sorted(values)
    k = (len(s) - 1) * p
    f, c = int(k), min(int(k) + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def salary_stats(postings: list[dict]) -> tuple[float | None, float | None, float | None, int]:
    """Per-posting salary point = midpoint of (min,max) when both present, else whichever exists."""
    points = []
    for p in postings:
        lo, hi = p.get("salary_min_trieu"), p.get("salary_max_trieu")
        if lo is not None and hi is not None:
            points.append((lo + hi) / 2)
        elif lo is not None:
            points.append(lo)
        elif hi is not None:
            points.append(hi)
    n = len(points)
    if n < MIN_SALARY_SAMPLES:
        return None, None, None, n
    return (round(percentile(points, 0.25), 1), round(percentile(points, 0.5), 1),
            round(percentile(points, 0.75), 1), n)


def top_skills(postings: list[dict], k: int = 8) -> list[str]:
    counter = Counter()
    for p in postings:
        for skill in p.get("skills") or []:
            counter[skill] += 1
    return [s for s, _ in counter.most_common(k)]


def build() -> None:
    postings = load_postings()
    careers = load_careers()

    mapped = 0
    by_career_region: dict[tuple[str, str], list[dict]] = defaultdict(list)
    by_skill_region: dict[tuple[str, str], list[str]] = defaultdict(list)  # skill -> [career_ids]

    for p in postings:
        career_id = map_career_id(p.get("title", ""), careers)
        region = p.get("region") or "other"
        if career_id:
            mapped += 1
            by_career_region[(career_id, region)].append(p)
            by_career_region[(career_id, "all")].append(p)
        for skill in p.get("skills") or []:
            by_skill_region[(skill, region)].append(career_id)
            by_skill_region[(skill, "all")].append(career_id)

    mapping_coverage_pct = round(100 * mapped / len(postings), 1) if postings else 0.0

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()  # rebuild clean each run — idempotent
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE career_stats (
            career_id TEXT, region TEXT,
            demand_count INTEGER, entry_level_count INTEGER,
            salary_p25 REAL, salary_p50 REAL, salary_p75 REAL, salary_sample_count INTEGER,
            trend_pct REAL, low_confidence INTEGER,
            top_skills_json TEXT, top_regions_json TEXT,
            PRIMARY KEY (career_id, region)
        );
        CREATE TABLE skill_stats (
            skill TEXT, region TEXT,
            demand_count INTEGER, gap_score REAL,
            trend_pct REAL, low_confidence INTEGER,
            related_careers_json TEXT,
            PRIMARY KEY (skill, region)
        );
        CREATE TABLE meta (
            postings_count INTEGER, window_days INTEGER, built_at TEXT,
            sources_json TEXT, career_mapping_coverage_pct REAL, note TEXT
        );
    """)

    # career_stats
    max_demand_all = max(
        (len(v) for (cid, reg), v in by_career_region.items() if reg == "all"), default=1
    )
    for (career_id, region), rows in by_career_region.items():
        demand = len(rows)
        entry = sum(1 for r in rows if r.get("seniority") == "entry")
        p25, p50, p75, n_sal = salary_stats(rows)
        low_conf = demand < MIN_DEMAND_SAMPLES
        regions_present = sorted({r.get("region") or "other" for r in rows})
        conn.execute(
            "INSERT INTO career_stats VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (career_id, region, demand, entry, p25, p50, p75, n_sal,
             None, int(low_conf), json.dumps(top_skills(rows), ensure_ascii=False),
             json.dumps(regions_present, ensure_ascii=False)),
        )

    # skill_stats — gap_score = demand normalized against the busiest career/region bucket
    # (documented simplified fallback from AI_DESIGN.md §3 since scarcity_hint isn't computable
    # from a single crawl either)
    for (skill, region), career_ids in by_skill_region.items():
        demand = len(career_ids)
        gap_score = round(min(1.0, demand / max(max_demand_all, 1)), 2)
        related = sorted({c for c in career_ids if c})[:5]
        # low_confidence reflects DEMAND sample size only (< MIN_DEMAND_SAMPLES) — trend_pct is
        # separately always NULL (single-snapshot crawl) and that's conveyed by trend_pct=None
        # itself, not by this flag. Do not set this True for well-sampled skills just because
        # trend is unavailable — that would mislabel confident demand signals as "hạn chế".
        low_conf = demand < MIN_DEMAND_SAMPLES
        conn.execute(
            "INSERT INTO skill_stats VALUES (?,?,?,?,?,?,?)",
            (skill, region, demand, gap_score, None, int(low_conf), json.dumps(related, ensure_ascii=False)),
        )

    conn.execute(
        "INSERT INTO meta VALUES (?,?,?,?,?,?)",
        (len(postings), 90, datetime.now(timezone.utc).isoformat(),
         json.dumps(sorted({p.get("source") for p in postings if p.get("source")})),
         mapping_coverage_pct,
         "Single-snapshot crawl: trend_pct intentionally NULL (not computable), "
         "low_confidence=1 below 10 postings/bucket or 5 salary samples."),
    )
    conn.commit()
    conn.close()

    print(f"postings={len(postings)} mapped={mapped} ({mapping_coverage_pct}%) "
          f"career_buckets={len({k[0] for k in by_career_region})} "
          f"skill_buckets={len({k[0] for k in by_skill_region})}")
    print(f"wrote {DB_PATH}")


if __name__ == "__main__":
    build()
