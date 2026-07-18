/**
 * Optimistic local application of a ProfilePatch (F1-04) — mirrors backend PATCH
 * semantics so the UI updates instantly; the server's profile (PROFILE_PATCHED)
 * replaces it on success, and the caller restores the previous profile on failure.
 */
import type { Profile, ProfilePatch } from "@/types";

export function applyPatchLocal(profile: Profile, patch: ProfilePatch): Profile {
  const normalize = (value: string) => value.trim().toLocaleLowerCase("vi");
  const removedSkills = new Set((patch.remove_skills ?? []).map(normalize));
  const removedInterests = new Set((patch.remove_interests ?? []).map(normalize));
  const removedExperiences = new Set((patch.remove_experience_titles ?? []).map(normalize));
  const interests = [...profile.interests];
  const seenInterests = new Set(interests.map(normalize));
  for (const raw of patch.add_interests ?? []) {
    const interest = raw.trim();
    if (interest && !seenInterests.has(normalize(interest))) {
      interests.push(interest);
      seenInterests.add(normalize(interest));
    }
  }
  return {
    ...profile,
    dimensions: { ...profile.dimensions, ...(patch.dimensions ?? {}) },
    skills: profile.skills.filter((skill) => !removedSkills.has(normalize(skill.name))),
    interests: interests.filter((interest) => !removedInterests.has(normalize(interest))),
    education_stage: "education_stage" in patch ? (patch.education_stage ?? null) : profile.education_stage,
    job_goal: "job_goal" in patch ? (patch.job_goal ?? null) : profile.job_goal,
    experiences: [
      ...profile.experiences.filter((experience) => !removedExperiences.has(normalize(experience.title))),
      ...(patch.add_experiences ?? []),
    ],
  };
}
