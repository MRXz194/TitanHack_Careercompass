// F1-04 (Launch): sửa giai đoạn học + mục tiêu việc làm → gọi onPatch đúng shape ProfilePatch.
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ProfileEditor } from "@/components/profile/ProfileEditor";

describe("ProfileEditor", () => {
  it("hiện giá trị hiện tại của stage và job goal", () => {
    render(<ProfileEditor educationStage="final_year" jobGoal="data entry-level" onPatch={() => {}} />);
    expect(screen.getByRole("combobox")).toHaveValue("final_year");
    expect(screen.getByRole("textbox")).toHaveValue("data entry-level");
  });

  it("đổi stage + bấm Lưu → onPatch nhận education_stage mới", async () => {
    const onPatch = vi.fn();
    render(<ProfileEditor educationStage="final_year" jobGoal={null} onPatch={onPatch} />);
    await userEvent.selectOptions(screen.getByRole("combobox"), "recent_graduate");
    await userEvent.click(screen.getByRole("button", { name: /lưu/i }));
    expect(onPatch).toHaveBeenCalledWith({ education_stage: "recent_graduate", job_goal: null });
  });

  it("sửa job goal + Lưu → onPatch nhận job_goal mới (trim)", async () => {
    const onPatch = vi.fn();
    render(<ProfileEditor educationStage={null} jobGoal={null} onPatch={onPatch} />);
    await userEvent.type(screen.getByRole("textbox"), "  thực tập marketing  ");
    await userEvent.click(screen.getByRole("button", { name: /lưu/i }));
    expect(onPatch).toHaveBeenCalledWith({ education_stage: null, job_goal: "thực tập marketing" });
  });

  it("không đổi gì → nút Lưu disabled (tránh patch thừa)", () => {
    render(<ProfileEditor educationStage="final_year" jobGoal="x" onPatch={() => {}} />);
    expect(screen.getByRole("button", { name: /lưu/i })).toBeDisabled();
  });
});
