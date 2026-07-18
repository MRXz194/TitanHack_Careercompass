"""Deterministic one-mutation What-if preview (N4-02).

The canonical session profile is never mutated or persisted. A hypothetical skill
is clearly labelled as unverified and is only used to recompute a preview.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from app.models.schemas import (
    Profile,
    ProfileSkill,
    Recommendation,
    RecommendationResponse,
    WhatIfDelta,
    WhatIfResponse,
)
from app.services import matching

DISCLAIMER = (
    "Đây là mô phỏng một thay đổi, không phải cập nhật hồ sơ và không chứng minh em đã có kỹ năng này. "
    "Hãy quay lại hồ sơ để bổ sung trải nghiệm thật nếu em muốn xác nhận."
)


def _clean_skill(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip()[:80]
    if not cleaned or any(token in cleaned.lower() for token in ("giới tính", "gpa", "trường top")):
        raise ValueError("invalid hypothetical skill")
    return cleaned


def _rank_map(items: list[Recommendation], stretch: Recommendation) -> dict[str, tuple[int, float, str]]:
    ordered = [*items, stretch]
    return {
        item.career_id: (rank, item.match_score, item.title)
        for rank, item in enumerate(ordered, start=1)
    }


def preview_added_skill(profile: Profile, skill: str) -> WhatIfResponse:
    skill = _clean_skill(skill)
    original_snapshot = profile.model_dump_json()
    working = profile.model_copy(deep=True)
    if skill.lower() not in {item.name.lower() for item in working.skills}:
        working.skills.append(
            ProfileSkill(
                name=skill,
                level="giả định what-if",
                source_quote="Giả định để mô phỏng; chưa phải bằng chứng trong hồ sơ",
            )
        )

    before, before_stretch = matching.recommend(profile)
    after, after_stretch = matching.recommend(working)
    before_map = _rank_map(before, before_stretch)
    after_map = _rank_map(after, after_stretch)
    deltas: list[WhatIfDelta] = []
    for career_id in sorted(set(before_map) | set(after_map)):
        old = before_map.get(career_id)
        new = after_map.get(career_id)
        if old and new and old[:2] == new[:2]:
            continue
        deltas.append(
            WhatIfDelta(
                career_id=career_id,
                title=(new or old)[2],  # type: ignore[index]
                before_rank=old[0] if old else None,
                after_rank=new[0] if new else None,
                before_score=old[1] if old else None,
                after_score=new[1] if new else None,
            )
        )

    # Safety assertion: preview must remain a pure function over a deep copy.
    assert profile.model_dump_json() == original_snapshot
    generated_at = datetime.now(timezone.utc).isoformat()
    return WhatIfResponse(
        generated_at=generated_at,
        mutation_label=f"Giả định bổ sung kỹ năng: {skill}",
        disclaimer=DISCLAIMER,
        original_profile_unchanged=True,
        deltas=deltas,
        preview=RecommendationResponse(
            generated_at=generated_at,
            disclaimer=DISCLAIMER,
            recommendations=after,
            stretch=after_stretch,
        ),
    )
