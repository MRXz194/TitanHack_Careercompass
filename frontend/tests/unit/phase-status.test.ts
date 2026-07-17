// F1-10: phase → copy trạng thái CỐ ĐỊNH (không suy diễn "AI đã quyết định", không lộ reasoning).
import { describe, expect, it } from "vitest";
import { phaseStatus, PHASE_PROGRESS } from "@/lib/chat/status";
import type { Phase } from "@/types";

const PHASES: Phase[] = ["warmup", "interests", "abilities", "constraints", "wrapup"];

describe("phaseStatus", () => {
  it("mỗi phase có copy tiếng Việt riêng, không rỗng", () => {
    const texts = PHASES.map((p) => phaseStatus(p, "explore"));
    texts.forEach((t) => expect(t.length).toBeGreaterThan(5));
    expect(new Set(texts).size).toBe(PHASES.length); // không trùng nhau
  });

  it("copy không chứa từ ngữ suy diễn quyết định thay người dùng", () => {
    for (const p of PHASES) {
      for (const mode of ["explore", "launch"] as const) {
        const t = phaseStatus(p, mode).toLowerCase();
        expect(t).not.toMatch(/ai đã quyết|hệ thống quyết định|chắc chắn phù hợp/);
      }
    }
  });

  it("launch mode có copy riêng cho abilities (hỏi evidence project)", () => {
    expect(phaseStatus("abilities", "launch")).not.toBe(phaseStatus("abilities", "explore"));
  });

  it("PHASE_PROGRESS tăng dần và nằm trong (0,1]", () => {
    const vals = PHASES.map((p) => PHASE_PROGRESS[p]);
    for (let i = 1; i < vals.length; i++) expect(vals[i]).toBeGreaterThan(vals[i - 1]);
    expect(vals[0]).toBeGreaterThan(0);
    expect(vals.at(-1)).toBe(1);
  });
});
