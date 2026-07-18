// F1-04: áp patch optimistic lên profile local (trước khi server trả) — phải khớp semantics BE.
import { describe, expect, it } from "vitest";
import { applyPatchLocal } from "@/lib/profile/apply";
import type { Profile } from "@/types";

const base: Profile = {
  session_id: "t", journey_mode: "launch", education_stage: "final_year", job_goal: "data entry-level",
  dimensions: { ky_thuat: 0.2, phan_tich: 0.6, sang_tao: 0.1, xa_hoi: 0.3, quan_ly: 0.2 },
  skills: [
    { name: "Excel", level: "đã dùng trong project", source_quote: "em làm dashboard" },
    { name: "SQL", level: "cơ bản", source_quote: "" },
  ],
  interests: ["phân tích dữ liệu"],
  constraints: { region_pref: "danang", study_budget: null, study_duration_pref: null, notes: "" },
  evidence_quotes: [],
  experiences: [{ title: "Dashboard bán hàng", kind: "project", description: "", skills: ["Excel"], source_quote: "" }],
  completeness: 0.8,
};

describe("applyPatchLocal", () => {
  it("remove_skills xóa đúng skill theo tên, không đụng skill khác", () => {
    const p = applyPatchLocal(base, { remove_skills: ["SQL"] });
    expect(p.skills.map((s) => s.name)).toEqual(["Excel"]);
  });

  it("remove skill không tồn tại → không crash, giữ nguyên", () => {
    const p = applyPatchLocal(base, { remove_skills: ["Python"] });
    expect(p.skills).toHaveLength(2);
  });

  it("dimensions merge từng key, key khác giữ nguyên", () => {
    const p = applyPatchLocal(base, { dimensions: { sang_tao: 0.7 } });
    expect(p.dimensions.sang_tao).toBe(0.7);
    expect(p.dimensions.phan_tich).toBe(0.6);
  });

  it("add_interests dedup (không thêm trùng)", () => {
    const p = applyPatchLocal(base, { add_interests: ["PHÂN TÍCH DỮ LIỆU", " trực quan hóa "] });
    expect(p.interests).toEqual(["phân tích dữ liệu", "trực quan hóa"]);
  });

  it("remove_interests xóa không phân biệt hoa thường như backend", () => {
    const p = applyPatchLocal(base, { remove_interests: ["PHÂN TÍCH DỮ LIỆU"] });
    expect(p.interests).toEqual([]);
  });

  it("education_stage/job_goal chỉ đổi khi key có mặt trong patch (kể cả set null)", () => {
    expect(applyPatchLocal(base, {}).job_goal).toBe("data entry-level");
    expect(applyPatchLocal(base, { job_goal: null }).job_goal).toBeNull();
    expect(applyPatchLocal(base, { education_stage: "recent_graduate" }).education_stage).toBe("recent_graduate");
  });

  it("remove_experience_titles xóa đúng experience", () => {
    const p = applyPatchLocal(base, { remove_experience_titles: ["Dashboard bán hàng"] });
    expect(p.experiences).toEqual([]);
  });

  it("không mutate profile gốc", () => {
    applyPatchLocal(base, { remove_skills: ["Excel"], dimensions: { ky_thuat: 0.9 } });
    expect(base.skills).toHaveLength(2);
    expect(base.dimensions.ky_thuat).toBe(0.2);
  });
});
