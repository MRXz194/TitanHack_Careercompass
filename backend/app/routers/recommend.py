"""Recommendation endpoint.

STATUS: STUB — returns seed careers with template evidence so FE (F2-01..03)
renders the full result screen from hour 1. Tasks PR-05..07 replace the picking
logic with the real matching engine + LLM evidence + counterfactual.
"""
from datetime import datetime, timezone

from fastapi import APIRouter

from app.data.seed_loader import load_careers
from app.models.schemas import (MarketStats, Recommendation, RecommendationResponse,
                                Route, SkillRoadmapItem, Why, WhyFromMarket, WhyFromYou)

router = APIRouter(prefix="/api", tags=["recommendations"])

DISCLAIMER = "Đây là gợi ý tham khảo dựa trên hồ sơ của em và dữ liệu thị trường — quyết định là của em."


def _to_rec(c: dict, score: float, stretch: bool = False) -> Recommendation:
    m = c["seed_market"]
    return Recommendation(
        career_id=c["career_id"], title=c["title"], match_score=score, is_stretch=stretch,
        why=Why(
            from_you=[WhyFromYou(quote="(mock) em hay sửa đồ điện trong nhà",
                                 reason="cho thấy thiên hướng thực hành - kỹ thuật rõ")],
            from_market=[
                WhyFromMarket(stat=f"{m['demand_count_90d']} tin tuyển trong 90 ngày", stat_key="demand_count"),
                WhyFromMarket(stat=f"Lương phổ biến {m['salary_p25_trieu']}–{m['salary_p75_trieu']} triệu", stat_key="salary"),
            ],
            counterfactual="(mock) Nếu em thiên về sáng tạo hơn thực hành, gợi ý đầu bảng sẽ là Thiết kế đồ họa.",
        ),
        market=MarketStats(demand_count_90d=m["demand_count_90d"],
                           salary_p25_trieu=m["salary_p25_trieu"], salary_p50_trieu=m["salary_p50_trieu"],
                           salary_p75_trieu=m["salary_p75_trieu"], trend_pct=m["trend_pct"],
                           top_regions=m["top_regions"], top_skills=m["top_skills"],
                           source_note="Dữ liệu mẫu (seed) — thay bằng số thật sau MI-04"),
        routes=[Route(**r) for r in c["routes"]],
        skill_roadmap=[SkillRoadmapItem(**s) for s in c["skill_roadmap"]],
    )


@router.post("/recommendations", response_model=RecommendationResponse)
def recommendations(body: dict) -> RecommendationResponse:
    # STUB ONLY: picks by seed order, not real matching. PR-05 replaces this whole
    # function with the scoring engine in docs/AI_DESIGN.md §4 — do not extend this
    # index-based logic once the career KB grows past 10 entries (D-07).
    careers = load_careers()
    top5 = [_to_rec(c, round(0.9 - i * 0.06, 2)) for i, c in enumerate(careers[:5])]
    stretch = _to_rec(careers[min(5, len(careers) - 1)], 0.61, stretch=True)
    return RecommendationResponse(
        generated_at=datetime.now(timezone.utc).isoformat(),
        disclaimer=DISCLAIMER, recommendations=top5, stretch=stretch,
    )
