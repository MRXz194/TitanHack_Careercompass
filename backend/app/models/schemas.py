"""Pydantic models — MUST mirror docs/API_CONTRACT.md exactly.

Contract change process: TEAM_RULES.md §2 (update contract + this file + frontend/types/index.ts in one PR).
NOTE: Profile intentionally has NO gender field — anti-bias by design. Do not add one.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

Region = Literal["hanoi", "hcm", "danang", "other", "all"]
RouteType = Literal["university", "college", "vocational", "certificate"]
Phase = Literal["warmup", "interests", "abilities", "constraints", "wrapup"]


# ---------- Profile ----------

class ProfileSkill(BaseModel):
    name: str
    level: str = ""
    source_quote: str = ""


class Constraints(BaseModel):
    region_pref: Optional[str] = None  # preference only — NEVER a hard filter
    study_budget: Optional[str] = None
    study_duration_pref: Optional[str] = None
    notes: str = ""


class EvidenceQuote(BaseModel):
    turn: int
    quote: str
    mapped_to: str


class Profile(BaseModel):
    session_id: str
    dimensions: dict[str, float] = Field(
        default_factory=lambda: {
            "ky_thuat": 0.0, "phan_tich": 0.0, "sang_tao": 0.0, "xa_hoi": 0.0, "quan_ly": 0.0,
        }
    )
    skills: list[ProfileSkill] = []
    interests: list[str] = []
    constraints: Constraints = Constraints()
    evidence_quotes: list[EvidenceQuote] = []
    completeness: float = 0.0


# ---------- Chat ----------

class ChatRequest(BaseModel):
    session_id: str
    message: Optional[str] = None  # None = opening turn


class ChatResponse(BaseModel):
    reply: str
    phase: Phase
    turn: int
    done: bool
    profile: Profile


class ProfilePatch(BaseModel):
    dimensions: dict[str, float] = {}
    remove_skills: list[str] = []
    add_interests: list[str] = []


# ---------- Recommendations ----------

class WhyFromYou(BaseModel):
    quote: str
    reason: str


class WhyFromMarket(BaseModel):
    stat: str
    stat_key: str


class Why(BaseModel):
    from_you: list[WhyFromYou]
    from_market: list[WhyFromMarket]
    counterfactual: str


class MarketStats(BaseModel):
    demand_count_90d: int
    salary_p25_trieu: Optional[float] = None
    salary_p50_trieu: Optional[float] = None
    salary_p75_trieu: Optional[float] = None
    trend_pct: Optional[float] = None
    top_regions: list[str] = []
    top_skills: list[str] = []
    source_note: str = ""


class Route(BaseModel):
    type: RouteType
    label: str
    detail: str = ""
    first_steps: list[str] = []


class SkillRoadmapItem(BaseModel):
    skill: str
    status: str


class Recommendation(BaseModel):
    career_id: str
    title: str
    match_score: float
    is_stretch: bool = False
    why: Why
    market: MarketStats
    routes: list[Route]  # invariant: len ≥ 2, ≥1 non-university (checked in service)
    skill_roadmap: list[SkillRoadmapItem] = []


class RecommendationResponse(BaseModel):
    generated_at: str
    disclaimer: str
    recommendations: list[Recommendation]
    stretch: Recommendation


# ---------- Market ----------

class RisingCareer(BaseModel):
    career_id: str
    title: str
    trend_pct: float
    demand_count: int


class TopPayingCareer(BaseModel):
    career_id: str
    title: str
    salary_p50_trieu: float


class MarketOverview(BaseModel):
    region: Region
    postings_count: int
    window_days: int
    updated_at: str
    rising_careers: list[RisingCareer]
    top_paying: list[TopPayingCareer]


class SkillGapItem(BaseModel):
    skill: str
    gap_score: float
    demand_count: int
    trend_pct: Optional[float] = None
    related_careers: list[str] = []


class SkillGapResponse(BaseModel):
    region: Region
    skills: list[SkillGapItem]
