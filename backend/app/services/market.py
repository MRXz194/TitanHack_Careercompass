"""Market stats reader — task MI-04. Reads market.db (built by data/pipeline/build_market_stats.py).

Replaces the seed-based logic in app/routers/market.py once market.db exists — keep
the response shapes in docs/API_CONTRACT.md §4 identical when swapping the data source.
"""
from app.models.schemas import MarketOverview, SkillGapResponse


def get_overview(region: str) -> MarketOverview:
    raise NotImplementedError("Task MI-04 — read career_stats table")


def get_skill_gaps(region: str) -> SkillGapResponse:
    raise NotImplementedError("Task MI-05 — read skill_stats table")
