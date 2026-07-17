// F1-03: Profile Card — dims + highlight, skill kèm source quote, Launch fields, empty state trung thực.
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ProfilePanel } from "@/components/profile/ProfilePanel";
import type { Profile } from "@/types";

const explore: Profile = {
  session_id: "t", journey_mode: "explore", education_stage: null, job_goal: null,
  dimensions: { ky_thuat: 0.7, phan_tich: 0.4, sang_tao: 0.8, xa_hoi: 0, quan_ly: 0 },
  skills: [{ name: "vẽ tay", level: "tự đánh giá khá", source_quote: "em thích vẽ truyện" }],
  interests: ["vẽ", "sửa đồ điện"],
  constraints: { region_pref: "danang", study_budget: "hạn chế", study_duration_pref: null, notes: "" },
  evidence_quotes: [], experiences: [], completeness: 0.6,
};

const launch: Profile = {
  ...explore, journey_mode: "launch", education_stage: "final_year", job_goal: "vai trò dữ liệu entry-level",
  experiences: [{ title: "Dashboard bán hàng", kind: "project", description: "Từ dữ liệu mở", skills: ["Excel"], source_quote: "em làm dashboard bằng Excel" }],
};

const noop = { onRemoveSkill: vi.fn(), onRemoveInterest: vi.fn(), onRemoveExperience: vi.fn() };

describe("ProfilePanel — explore", () => {
  it("profile null → placeholder thân thiện, không crash", () => {
    render(<ProfilePanel profile={null} diff={null} {...noop} />);
    expect(screen.getByText(/trò chuyện để hồ sơ hiện dần/i)).toBeInTheDocument();
  });

  it("render đủ 5 chiều với nhãn tiếng Việt và %", () => {
    render(<ProfilePanel profile={explore} diff={null} {...noop} />);
    expect(screen.getByText("Thực hành – kỹ thuật")).toBeInTheDocument();
    expect(screen.getByText("70%")).toBeInTheDocument();
  });

  it("chiều trong diff.changedDimensions có data-highlight", () => {
    render(
      <ProfilePanel profile={explore} {...noop}
        diff={{ changedDimensions: ["sang_tao"], addedSkills: [], addedInterests: [], addedExperiences: [] }} />,
    );
    expect(screen.getByTestId("dim-sang_tao")).toHaveAttribute("data-highlight", "true");
    expect(screen.getByTestId("dim-ky_thuat")).toHaveAttribute("data-highlight", "false");
  });

  it("skill hiển thị kèm source quote (minh bạch suy luận)", () => {
    render(<ProfilePanel profile={explore} diff={null} {...noop} />);
    expect(screen.getByText("vẽ tay")).toBeInTheDocument();
    expect(screen.getByText(/em thích vẽ truyện/)).toBeInTheDocument();
  });

  it("xóa skill cần 2 bước xác nhận rồi mới gọi onRemoveSkill", async () => {
    const onRemoveSkill = vi.fn();
    render(<ProfilePanel profile={explore} diff={null} {...noop} onRemoveSkill={onRemoveSkill} />);
    await userEvent.click(screen.getByRole("button", { name: /xóa kỹ năng vẽ tay/i }));
    expect(onRemoveSkill).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: /xác nhận xóa vẽ tay/i }));
    expect(onRemoveSkill).toHaveBeenCalledWith("vẽ tay");
  });

  it("constraints null → dòng 'chưa có thông tin' trung thực (không bịa)", () => {
    const p = { ...explore, constraints: { region_pref: null, study_budget: null, study_duration_pref: null, notes: "" } };
    render(<ProfilePanel profile={p} diff={null} {...noop} />);
    expect(screen.getByText(/chưa có thông tin/i)).toBeInTheDocument();
  });
});

describe("ProfilePanel — launch", () => {
  it("hiện mục tiêu việc làm + giai đoạn + experiences", () => {
    render(<ProfilePanel profile={launch} diff={null} {...noop} />);
    expect(screen.getByText(/vai trò dữ liệu entry-level/)).toBeInTheDocument();
    expect(screen.getByText(/năm cuối/i)).toBeInTheDocument();
    expect(screen.getByText("Dashboard bán hàng")).toBeInTheDocument();
    expect(screen.getByText(/em làm dashboard bằng Excel/)).toBeInTheDocument();
  });

  it("experience không có skills → vẫn render, không crash", () => {
    const p = { ...launch, experiences: [{ title: "Phụ quán cà phê", kind: "work" as const, description: "", skills: [], source_quote: "" }] };
    render(<ProfilePanel profile={p} diff={null} {...noop} />);
    expect(screen.getByText("Phụ quán cà phê")).toBeInTheDocument();
  });

  it("explore mode KHÔNG hiện khối experiences/job goal", () => {
    render(<ProfilePanel profile={explore} diff={null} {...noop} />);
    expect(screen.queryByText(/mục tiêu việc làm/i)).not.toBeInTheDocument();
  });
});
