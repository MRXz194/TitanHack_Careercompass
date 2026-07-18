"""Internal profiler LLM I/O models (not part of public FE/BE API contract).

Used by PR-02 prompts/tests and PR-03 session engine merge.
Public Profile remains in app.models.schemas.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.schemas import (
    EducationStage,
    EvidenceQuote,
    ExperienceEvidence,
    ProfileSkill,
)


class ConstraintsDelta(BaseModel):
    model_config = ConfigDict(extra="ignore")

    region_pref: Optional[str] = None
    study_budget: Optional[str] = None
    study_duration_pref: Optional[str] = None
    notes: Optional[str] = None


class CorrectionsDelta(BaseModel):
    """A conversation turn's signal that the user is retracting/contradicting something
    said earlier — never additive. Distinct from ProfilePatch (which is the explicit
    out-of-band PATCH /profile shape): this is what a single turn can plausibly signal."""

    model_config = ConfigDict(extra="ignore")

    remove_skills: list[str] = Field(default_factory=list)
    remove_interests: list[str] = Field(default_factory=list)
    reset_dimensions: list[str] = Field(default_factory=list)


class ProfileDelta(BaseModel):
    """Partial profile update from one profiler turn. Empty fields mean 'no change'."""

    model_config = ConfigDict(extra="ignore")

    dimensions: dict[str, float] = Field(default_factory=dict)
    skills: list[ProfileSkill] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    constraints: Optional[ConstraintsDelta] = None
    experiences: list[ExperienceEvidence] = Field(default_factory=list)
    education_stage: Optional[EducationStage] = None
    job_goal: Optional[str] = None
    evidence_quotes: list[EvidenceQuote] = Field(default_factory=list)
    corrections: Optional[CorrectionsDelta] = None


class ProfilerTurnOutput(BaseModel):
    """Structured LLM turn. Matches prompt JSON keys."""

    model_config = ConfigDict(extra="ignore")

    reply: str
    profile_delta: ProfileDelta = Field(default_factory=ProfileDelta)
    phase_done: bool = False
