/**
 * Phase → fixed product-level status copy (F1-10). This is FE-owned static copy keyed
 * on the contract `phase` — never derived from agent traces, tool JSON or reasoning.
 * Copy rule: describe what the CONVERSATION is doing, never claim the AI "decided".
 */
import type { JourneyMode, Phase } from "@/types";

const EXPLORE_STATUS: Record<Phase, string> = {
  warmup: "Mình đang làm quen với bạn một chút…",
  interests: "Mình đang tìm hiểu điều bạn thích làm",
  abilities: "Mình đang ghi nhận điểm mạnh của bạn",
  constraints: "Mình đang hỏi về điều kiện học tập của bạn",
  wrapup: "Cùng xem lại hồ sơ trước khi khám phá hướng đi nhé",
};

const LAUNCH_STATUS: Record<Phase, string> = {
  warmup: "Mình đang tìm hiểu mục tiêu công việc của bạn",
  interests: "Mình đang tìm hiểu trải nghiệm bạn muốn phát triển tiếp",
  abilities: "Mình đang ghi nhận bằng chứng kỹ năng từ project của bạn",
  constraints: "Mình đang hỏi về khu vực và thời gian tìm việc",
  wrapup: "Cùng kiểm tra lại kỹ năng và trải nghiệm trước khi xem việc phù hợp",
};

export function phaseStatus(phase: Phase, mode: JourneyMode): string {
  return (mode === "launch" ? LAUNCH_STATUS : EXPLORE_STATUS)[phase];
}

/** Coarse progress per phase for the progress indicator — no false precision. */
export const PHASE_PROGRESS: Record<Phase, number> = {
  warmup: 0.15,
  interests: 0.4,
  abilities: 0.65,
  constraints: 0.85,
  wrapup: 1,
};
