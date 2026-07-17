"""Matching engine — task PR-05 (embeddings from MI-06). Design: docs/AI_DESIGN.md §4.

score(career) = w_cosine * cosine(embed(profile_text), embed(career))
              + w_skill_overlap * skill_overlap(profile, career.top_skills)
              + w_market_signal * market_signal(career, profile.constraints.region_pref)

Weights come from app.core.config.Settings (w_cosine/w_skill_overlap/w_market_signal) —
never hardcode them here. profile_text must NOT include region or gender (there's no
gender field to include). Stretch pick: highest score outside the user's dominant dimension.

Loads data/processed/careers.npy + career_ids.json (built by MI-06/data/pipeline/embed_careers.py).
Has a unit test requirement per TEAM_RULES.md §4 — this is where wrong output becomes a
silently-fabricated recommendation, not just a bug.
"""
from app.models.schemas import Profile, Recommendation


def top_k_careers(profile_text: str, k: int = 20) -> list[tuple[str, float]]:
    raise NotImplementedError("Task MI-06 — embeddings + cosine top-k")


def recommend(profile: Profile) -> tuple[list[Recommendation], Recommendation]:
    raise NotImplementedError("Task PR-05 — returns (top5, stretch)")
