import type { WhatIfResponse } from "@/types";
import { mockRecommendations } from "./recommendations";

export async function mockWhatIfSkill(skill: string): Promise<WhatIfResponse> {
  const preview = await mockRecommendations("explore");
  const first = preview.recommendations[0];
  const nextScore = Math.min(1, first.match_score + 0.06);
  preview.recommendations[0] = { ...first, match_score: nextScore };
  return {
    generated_at: new Date().toISOString(),
    mutation_label: `Giả định bổ sung kỹ năng: ${skill}`,
    disclaimer: "Đây là mô phỏng; hồ sơ gốc chưa thay đổi và kỹ năng chưa được coi là bằng chứng thật.",
    original_profile_unchanged: true,
    deltas: [{
      career_id: first.career_id,
      title: first.title,
      before_rank: 1,
      after_rank: 1,
      before_score: first.match_score,
      after_score: nextScore,
    }],
    preview,
  };
}
