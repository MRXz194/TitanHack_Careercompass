"""Market intelligence endpoints.

STATUS: serves SEED data (data/seed/careers_seed.json).
Task MI-04/MI-05 swaps the data source to market.db — the response shapes must not change.
"""
from fastapi import APIRouter, HTTPException, Query

from app.data.seed_loader import get_career, load_careers
from app.models.schemas import (CareerDetail, MarketOverview, MarketStats, Route,
                                RisingCareer, SkillGapItem, SkillGapResponse, TopPayingCareer)

router = APIRouter(prefix="/api/market", tags=["market"])

SEED_NOTE = "Dữ liệu mẫu (seed) — sẽ thay bằng số thật từ pipeline (MI-04)"


@router.get("/overview", response_model=MarketOverview)
def overview(region: str = Query("all")) -> MarketOverview:
    careers = load_careers()
    rising = sorted(careers, key=lambda c: c["seed_market"]["trend_pct"], reverse=True)[:8]
    paying = sorted(careers, key=lambda c: c["seed_market"]["salary_p50_trieu"], reverse=True)[:5]
    return MarketOverview(
        region=region, postings_count=sum(c["seed_market"]["demand_count_90d"] for c in careers),
        window_days=90, updated_at="seed", source_note=SEED_NOTE,
        rising_careers=[RisingCareer(career_id=c["career_id"], title=c["title"],
                                     trend_pct=c["seed_market"]["trend_pct"],
                                     demand_count=c["seed_market"]["demand_count_90d"]) for c in rising],
        top_paying=[TopPayingCareer(career_id=c["career_id"], title=c["title"],
                                    salary_p50_trieu=c["seed_market"]["salary_p50_trieu"]) for c in paying],
    )


@router.get("/skills", response_model=SkillGapResponse)
def skill_gaps(region: str = Query("all")) -> SkillGapResponse:
    # STUB: derive pseudo gap scores from seed careers. MI-05 replaces with skill_stats table.
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
                                            trend_pct=m["trend_pct"], related_careers=[c["career_id"]])
    top = sorted(items.values(), key=lambda i: i.gap_score, reverse=True)[:20]
    return SkillGapResponse(region=region, skills=top, source_note=SEED_NOTE)


@router.get("/careers/{career_id}", response_model=CareerDetail)
def career_detail(career_id: str, region: str = Query("all")) -> CareerDetail:
    c = get_career(career_id)
    if not c:
        raise HTTPException(404, detail="career not found")
    m = dict(c["seed_market"])
    m["source_note"] = SEED_NOTE
    return CareerDetail(career_id=c["career_id"], title=c["title"], description=c["description"],
                        market=MarketStats(**m), routes=[Route(**r) for r in c["routes"]])
