/**
 * Optimistic local application of a ProfilePatch (F1-04) — mirrors backend PATCH
 * semantics so the UI updates instantly; the server's profile (PROFILE_PATCHED)
 * replaces it on success, and the caller restores the previous profile on failure.
 */
import type { Profile, ProfilePatch } from "@/types";

export function applyPatchLocal(profile: Profile, patch: ProfilePatch): Profile {
  return {
    ...profile,
    dimensions: { ...profile.dimensions, ...(patch.dimensions ?? {}) },
    skills: profile.skills.filter((s) => !(patch.remove_skills ?? []).includes(s.name)),
    interests: [...new Set([...profile.interests, ...(patch.add_interests ?? [])])],
    education_stage: "education_stage" in patch ? (patch.education_stage ?? null) : profile.education_stage,
    job_goal: "job_goal" in patch ? (patch.job_goal ?? null) : profile.job_goal,
    experiences: [
      ...profile.experiences.filter((e) => !(patch.remove_experience_titles ?? []).includes(e.title)),
      ...(patch.add_experiences ?? []),
    ],
  };
}
