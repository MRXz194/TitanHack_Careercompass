/**
 * Profile diff — detects what just changed between two profile snapshots so the
 * ProfilePanel can flash a "vừa cập nhật" highlight (F1-03). Pure, unit-tested.
 */
import type { Profile } from "@/types";

export interface ProfileDiff {
  changedDimensions: string[];
  addedSkills: string[];
  addedInterests: string[];
  addedExperiences: string[];
}

/** Dimension moves smaller than this are rounding noise, not real updates. */
const DIM_EPSILON = 0.01;

export function diffProfile(prev: Profile | null, next: Profile): ProfileDiff {
  const prevDims = prev?.dimensions ?? {};
  const changedDimensions = Object.entries(next.dimensions)
    .filter(([k, v]) => Math.abs(v - (prevDims[k] ?? 0)) >= DIM_EPSILON)
    .map(([k]) => k);

  const prevSkills = new Set((prev?.skills ?? []).map((s) => s.name));
  const prevInterests = new Set(prev?.interests ?? []);
  const prevExperiences = new Set((prev?.experiences ?? []).map((e) => e.title));

  return {
    changedDimensions,
    addedSkills: next.skills.map((s) => s.name).filter((n) => !prevSkills.has(n)),
    addedInterests: next.interests.filter((i) => !prevInterests.has(i)),
    addedExperiences: next.experiences.map((e) => e.title).filter((t) => !prevExperiences.has(t)),
  };
}
