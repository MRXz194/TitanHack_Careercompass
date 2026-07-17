// F1-03: phát hiện phần profile vừa thay đổi để highlight "vừa cập nhật".
import { describe, expect, it } from "vitest";
import { diffProfile } from "@/lib/profile/diff";
import type { Profile } from "@/types";

const base: Profile = {
  session_id: "t", journey_mode: "explore", education_stage: null, job_goal: null,
  dimensions: { ky_thuat: 0.2, phan_tich: 0.1, sang_tao: 0, xa_hoi: 0, quan_ly: 0 },
  skills: [{ name: "vẽ tay", level: "khá", source_quote: "em thích vẽ" }],
  interests: ["vẽ"],
  constraints: { region_pref: null, study_budget: null, study_duration_pref: null, notes: "" },
  evidence_quotes: [], experiences: [], completeness: 0.2,
};

describe("diffProfile", () => {
  it("prev=null → mọi thứ có dữ liệu coi là mới", () => {
    const d = diffProfile(null, base);
    expect(d.changedDimensions).toContain("ky_thuat");
    expect(d.addedSkills).toEqual(["vẽ tay"]);
    expect(d.addedInterests).toEqual(["vẽ"]);
  });

  it("dimension nhích ≥0.01 mới tính là đổi (tránh nhấp nháy vì làm tròn)", () => {
    const next = { ...base, dimensions: { ...base.dimensions, ky_thuat: 0.205, sang_tao: 0.4 } };
    const d = diffProfile(base, next);
    expect(d.changedDimensions).toEqual(["sang_tao"]);
  });

  it("skill/interest/experience mới được liệt kê theo tên", () => {
    const next: Profile = {
      ...base,
      skills: [...base.skills, { name: "sửa điện", level: "", source_quote: "em hay sửa đồ điện" }],
      interests: [...base.interests, "điện tử"],
      experiences: [{ title: "Dashboard", kind: "project", description: "", skills: [], source_quote: "" }],
    };
    const d = diffProfile(base, next);
    expect(d.addedSkills).toEqual(["sửa điện"]);
    expect(d.addedInterests).toEqual(["điện tử"]);
    expect(d.addedExperiences).toEqual(["Dashboard"]);
  });

  it("không đổi gì → mọi danh sách rỗng", () => {
    const d = diffProfile(base, base);
    expect(d.changedDimensions).toEqual([]);
    expect(d.addedSkills).toEqual([]);
    expect(d.addedInterests).toEqual([]);
    expect(d.addedExperiences).toEqual([]);
  });

  it("xóa skill (user correction) không nằm trong added", () => {
    const next = { ...base, skills: [] };
    expect(diffProfile(base, next).addedSkills).toEqual([]);
  });
});
