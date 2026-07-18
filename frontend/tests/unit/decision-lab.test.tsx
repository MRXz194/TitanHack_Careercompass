import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import DecisionLab from "@/components/results/DecisionLab";
import { mockRecommendations } from "@/lib/mock/recommendations";

const { fetchCareerResearch, previewWhatIfSkill } = vi.hoisted(() => ({
  fetchCareerResearch: vi.fn(),
  previewWhatIfSkill: vi.fn(),
}));

vi.mock("@/lib/api", () => ({ fetchCareerResearch, previewWhatIfSkill }));

describe("DecisionLab", () => {
  beforeEach(() => {
    fetchCareerResearch.mockReset();
    previewWhatIfSkill.mockReset();
  });

  it("chỉ giữ tối đa hai lựa chọn với trọng lượng thị giác ngang nhau", async () => {
    const data = await mockRecommendations("explore");
    render(<DecisionLab options={data.recommendations} />);
    expect(screen.getByRole("button", { name: new RegExp(data.recommendations[0].title, "i") })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: new RegExp(data.recommendations[1].title, "i") })).toHaveAttribute("aria-pressed", "true");
    await userEvent.click(screen.getByRole("button", { name: new RegExp(data.recommendations[2].title, "i") }));
    expect(screen.getByRole("button", { name: new RegExp(data.recommendations[0].title, "i") })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("button", { name: new RegExp(data.recommendations[1].title, "i") })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: new RegExp(data.recommendations[2].title, "i") })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText(/không có “người thắng”/i)).toBeInTheDocument();
  });

  it("research hiển thị trạng thái và citation nhưng không đổi options", async () => {
    const data = await mockRecommendations("explore");
    const first = data.recommendations[0];
    fetchCareerResearch.mockResolvedValue({
      status: "live",
      generated_at: new Date().toISOString(),
      intent: "overview",
      region: "all",
      disclaimer: "Nguồn chỉ để kiểm chứng.",
      limitation: "Kết quả có thể thay đổi.",
      careers: [{
        career_id: first.career_id,
        title: first.title,
        local_market: first.market,
        sources: [{
          title: "Nguồn nghề nghiệp",
          url: "https://example.com/source",
          domain: "example.com",
          snippet: "Thông tin có trích nguồn.",
          source_tier: "other",
          retrieved_at: new Date().toISOString(),
        }],
      }],
    });
    render(<DecisionLab options={[first]} />);
    await userEvent.click(screen.getByRole("button", { name: /nghiên cứu thêm/i }));
    expect(await screen.findByText("LIVE")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /nguồn nghề nghiệp/i })).toHaveAttribute("href", "https://example.com/source");
    expect(fetchCareerResearch).toHaveBeenCalledWith([first.career_id], "overview", "all");
  });

  it("what-if là preview có undo và thông báo hồ sơ không đổi", async () => {
    const data = await mockRecommendations("explore");
    const first = data.recommendations[0];
    previewWhatIfSkill.mockResolvedValue({
      generated_at: new Date().toISOString(),
      mutation_label: "Giả định bổ sung kỹ năng: SQL",
      disclaimer: "Hồ sơ gốc chưa thay đổi.",
      original_profile_unchanged: true,
      deltas: [{
        career_id: first.career_id,
        title: first.title,
        before_rank: 2,
        after_rank: 1,
        before_score: 0.7,
        after_score: 0.8,
      }],
      preview: data,
    });
    render(<DecisionLab options={[first]} />);
    await userEvent.type(screen.getByLabelText(/kỹ năng muốn thử/i), "SQL");
    await userEvent.click(screen.getByRole("button", { name: /thử thay đổi/i }));
    expect(await screen.findByText(/hạng 2/i)).toBeInTheDocument();
    expect(screen.getByText(/hồ sơ gốc chưa thay đổi/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /hoàn tác preview/i }));
    expect(screen.queryByText(/hạng 2/i)).not.toBeInTheDocument();
  });
});
