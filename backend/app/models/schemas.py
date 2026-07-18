"""Pydantic models — MUST mirror docs/API_CONTRACT.md exactly.

Contract change process: TEAM_RULES.md §2 (update contract + this file + frontend/types/index.ts in one PR).
NOTE: Profile intentionally has NO gender field — anti-bias by design. Do not add one.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

Region = Literal["hanoi", "hcm", "danang", "other", "all"]
RouteType = Literal["university", "college", "vocational", "certificate"]
Phase = Literal["warmup", "interests", "abilities", "constraints", "wrapup"]
JourneyMode = Literal["explore", "launch"]
EducationStage = Literal[
    "high_school", "vocational_student", "college_student", "university_student",
    "final_year", "recent_graduate", "other",
]
ExperienceKind = Literal["project", "internship", "work", "volunteer", "coursework", "other"]
ReadinessBand = Literal["ready_now", "near_ready", "build_foundation"]
ResearchIntent = Literal["overview", "skills", "routes", "local_market"]
ResearchStatus = Literal["live", "cached", "replay", "unavailable"]


# ---------- Service health ----------

class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    llm_configured: bool
    llm_ok: bool
    data_loaded: bool
    market_db_loaded: bool
    postings_count: int


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


class ExperienceEvidence(BaseModel):
    title: str
    kind: ExperienceKind
    description: str = ""
    skills: list[str] = Field(default_factory=list)
    source_quote: str = ""


class Profile(BaseModel):
    session_id: str
    journey_mode: JourneyMode = "explore"
    education_stage: Optional[EducationStage] = None
    job_goal: Optional[str] = None
    dimensions: dict[str, float] = Field(
        default_factory=lambda: {
            "ky_thuat": 0.0, "phan_tich": 0.0, "sang_tao": 0.0, "xa_hoi": 0.0, "quan_ly": 0.0,
        }
    )
    skills: list[ProfileSkill] = []
    interests: list[str] = []
    constraints: Constraints = Constraints()
    evidence_quotes: list[EvidenceQuote] = []
    experiences: list[ExperienceEvidence] = Field(default_factory=list)
    completeness: float = 0.0


# ---------- Chat ----------

class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    message: Optional[str] = Field(default=None, max_length=2000)  # None = opening turn
    journey_mode: JourneyMode = "explore"


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
    remove_interests: list[str] = []
    education_stage: Optional[EducationStage] = None
    job_goal: Optional[str] = None
    add_experiences: list[ExperienceEvidence] = Field(default_factory=list)
    remove_experience_titles: list[str] = Field(default_factory=list)


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
    entry_level_count_90d: int = 0
    salary_p25_trieu: Optional[float] = None
    salary_p50_trieu: Optional[float] = None
    salary_p75_trieu: Optional[float] = None
    trend_pct: Optional[float] = None
    salary_sample_count: int = 0
    low_confidence: bool = True
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


class SkillEvidence(BaseModel):
    skill: str
    evidence: str


class LaunchAction(BaseModel):
    week: int
    action: str
    deliverable: str
    why: str


class JobReadiness(BaseModel):
    band: ReadinessBand
    band_reason: str
    matched_skills: list[SkillEvidence] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(default_factory=list)
    actions_30d: list[LaunchAction] = Field(default_factory=list)


class Recommendation(BaseModel):
    career_id: str
    title: str
    match_score: float
    is_stretch: bool = False
    why: Why
    market: MarketStats
    routes: list[Route]  # invariant: len ≥ 2, ≥1 non-university (checked in service)
    skill_roadmap: list[SkillRoadmapItem] = []
    job_readiness: Optional[JobReadiness] = None


class RecommendationResponse(BaseModel):
    generated_at: str
    disclaimer: str
    recommendations: list[Recommendation]
    stretch: Recommendation


class WhatIfRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=160)
    skill: str = Field(min_length=1, max_length=80)


class WhatIfDelta(BaseModel):
    career_id: str
    title: str
    before_rank: Optional[int] = None
    after_rank: Optional[int] = None
    before_score: Optional[float] = None
    after_score: Optional[float] = None


class WhatIfResponse(BaseModel):
    generated_at: str
    mutation_label: str
    disclaimer: str
    original_profile_unchanged: bool = True
    deltas: list[WhatIfDelta]
    preview: RecommendationResponse


# ---------- Market ----------

class RisingCareer(BaseModel):
    career_id: str
    title: str
    trend_pct: Optional[float] = None
    demand_count: int
    low_confidence: bool = True


class TopPayingCareer(BaseModel):
    career_id: str
    title: str
    salary_p50_trieu: float


class MarketOverview(BaseModel):
    region: Region
    postings_count: int
    window_days: int
    updated_at: str
    source_note: str = ""
    rising_careers: list[RisingCareer]
    top_paying: list[TopPayingCareer]


class SkillGapItem(BaseModel):
    skill: str
    gap_score: float
    demand_count: int
    trend_pct: Optional[float] = None
    low_confidence: bool = True
    related_careers: list[str] = []


class SkillGapResponse(BaseModel):
    region: Region
    skills: list[SkillGapItem]
    source_note: str = ""


class CareerDetail(BaseModel):
    career_id: str
    title: str
    description: str
    market: MarketStats
    routes: list[Route]


# ---------- Bounded career research (Day 3) ----------

class CareerResearchRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=160)
    career_ids: list[str] = Field(min_length=1, max_length=2)
    intent: ResearchIntent = "overview"
    region: Region = "all"


class ResearchSourceCard(BaseModel):
    title: str
    url: str
    domain: str
    snippet: str
    source_tier: Literal["official", "job_board", "education", "other"] = "other"
    retrieved_at: str


class CareerResearchBlock(BaseModel):
    career_id: str
    title: str
    local_market: MarketStats
    sources: list[ResearchSourceCard] = Field(default_factory=list)


class CareerResearchResponse(BaseModel):
    status: ResearchStatus
    generated_at: str
    intent: ResearchIntent
    region: Region
    disclaimer: str
    limitation: str
    careers: list[CareerResearchBlock]
