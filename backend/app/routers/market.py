"""Market intelligence endpoints.

Prefers real stats from market.db (built by data/pipeline/build_market_stats.py from
crawled postings, MI-04/05) and falls back to seed data (data/seed/careers_seed.json)
when market.db is absent/empty — e.g. a fresh checkout before anyone has run the pipeline.
The fallback is NOT a demo trick: it's the same seed data FE has used since hour 1, so the
API never breaks, it just labels its source honestly via `source_note`.
"""
import logging

from fastapi import APIRouter, HTTPException, Query

from app.data.seed_loader import get_career, load_careers
from app.models.schemas import (CareerDetail, MarketOverview, MarketStats, Route,
                                RisingCareer, SkillGapItem, SkillGapResponse, TopPayingCareer)
from app.services import market as market_service
from app.services.market import MarketDataUnavailable

router = APIRouter(prefix="/api/market", tags=["market"])
log = logging.getLogger("app.market")

SEED_NOTE = "Dữ liệu mẫu (seed) — pipeline chưa chạy hoặc chưa đủ dữ liệu cho vùng này"


def _seed_overview(region: str) -> MarketOverview:
    careers = load_careers()
    rising = sorted(careers, key=lambda c: c["seed_market"]["trend_pct"], reverse=True)[:8]
    paying = sorted(careers, key=lambda c: c["seed_market"]["salary_p50_trieu"], reverse=True)[:5]
    return MarketOverview(
        region=region, postings_count=sum(c["seed_market"]["demand_count_90d"] for c in careers),
        window_days=90, updated_at="seed", source_note=SEED_NOTE,
        rising_careers=[RisingCareer(career_id=c["career_id"], title=c["title"],
                                     trend_pct=c["seed_market"]["trend_pct"],
                                     demand_count=c["seed_market"]["demand_count_90d"],
                                     low_confidence=False) for c in rising],
        top_paying=[TopPayingCareer(career_id=c["career_id"], title=c["title"],
                                    salary_p50_trieu=c["seed_market"]["salary_p50_trieu"]) for c in paying],
    )


def _seed_skill_gaps(region: str) -> SkillGapResponse:
    items: dict[str, SkillGapItem] = {}
    for c in load_careers():
        m = c["seed_market"]
        if region not in ("all",) and region not in m["top_regions"]:
            continue
        for skill in m["top_skills"][:3]:
            cur = items.get(skill)
            score = min(1.0, m["demand_count_90d"] / 2000 * 0.6 + max(m["trend_pct"], 0) / 100 * 0.4)
            if cur is None or score > cur.gap_score:
                items[skill] = SkillGapItem(skill=skill, gap_score=round(score, 2),
                                            demand_count=m["demand_count_90d"],
                                            trend_pct=m["trend_pct"], low_confidence=False,
                                            related_careers=[c["career_id"]])
    top = sorted(items.values(), key=lambda i: i.gap_score, reverse=True)[:20]
    return SkillGapResponse(region=region, skills=top, source_note=SEED_NOTE)


@router.get("/overview", response_model=MarketOverview)
def overview(region: str = Query("all")) -> MarketOverview:
    try:
        return market_service.get_overview(region)
    except MarketDataUnavailable as e:
        log.info("market.db unavailable for overview(region=%s): %s — falling back to seed", region, e)
        return _seed_overview(region)


@router.get("/skills", response_model=SkillGapResponse)
def skill_gaps(region: str = Query("all")) -> SkillGapResponse:
    try:
        return market_service.get_skill_gaps(region)
    except MarketDataUnavailable as e:
        log.info("market.db unavailable for skill_gaps(region=%s): %s — falling back to seed", region, e)
        return _seed_skill_gaps(region)


@router.get("/careers/{career_id}", response_model=CareerDetail)
def career_detail(career_id: str, region: str = Query("all")) -> CareerDetail:
    c = get_career(career_id)
    if not c:
        raise HTTPException(404, detail="career not found")
    try:
        stats = market_service.get_career_market(career_id, region)
    except MarketDataUnavailable:
        seed = dict(c["seed_market"])
        seed["source_note"] = SEED_NOTE
        stats = MarketStats(**seed)
    return CareerDetail(career_id=c["career_id"], title=c["title"], description=c["description"],
                        market=stats, routes=[Route(**r) for r in c["routes"]])
