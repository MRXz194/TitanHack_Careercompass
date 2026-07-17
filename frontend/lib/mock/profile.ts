// Mock profile patch — task F1-04 nối API thật; giữ mock hoạt động độc lập không cần backend.
import type { Profile, ProfilePatch } from "@/types";

let current: Profile = {
  session_id: "mock",
  journey_mode: "explore",
  education_stage: "high_school",
  job_goal: null,
  dimensions: { ky_thuat: 0.7, phan_tich: 0.4, sang_tao: 0.8, xa_hoi: 0.3, quan_ly: 0.2 },
  skills: [{ name: "vẽ tay", level: "tự đánh giá khá", source_quote: "em thích vẽ" }],
  interests: ["vẽ", "sửa chữa đồ điện"],
  constraints: { region_pref: "danang", study_budget: "hạn chế", study_duration_pref: null, notes: "" },
  evidence_quotes: [],
  experiences: [],
  completeness: 1,
};

export async function mockPatchProfile(patch: ProfilePatch): Promise<{ profile: Profile }> {
  await new Promise((r) => setTimeout(r, 300));
  current = {
    ...current,
    dimensions: { ...current.dimensions, ...(patch.dimensions ?? {}) },
    skills: current.skills.filter((s) => !(patch.remove_skills ?? []).includes(s.name)),
    interests: [...new Set([...current.interests, ...(patch.add_interests ?? [])])],
    education_stage: "education_stage" in patch ? (patch.education_stage ?? null) : current.education_stage,
    job_goal: "job_goal" in patch ? (patch.job_goal ?? null) : current.job_goal,
    experiences: [
      ...current.experiences.filter((e) => !(patch.remove_experience_titles ?? []).includes(e.title)),
      ...(patch.add_experiences ?? []),
    ],
  };
  return { profile: current };
}
