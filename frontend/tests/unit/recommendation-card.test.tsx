import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import RecommendationCard from "@/components/results/RecommendationCard";
import type { Recommendation } from "@/types";

const launchRecommendation: Recommendation = {
  career_id: "data-analyst",
  title: "Chuyên viên phân tích dữ liệu",
  match_score: 0.78,
  is_stretch: false,
  why: {
    from_you: [{ quote: "Em mới học Excel cơ bản", reason: "tạo tín hiệu phân tích" }],
    from_market: [{ stat: "100 tin tuyển trong 90 ngày", stat_key: "demand_count" }],
    counterfactual: "Nếu evidence thay đổi, thứ tự có thể thay đổi.",
  },
  market: {
    demand_count_90d: 100,
    entry_level_count_90d: 25,
    salary_p25_trieu: 10,
    salary_p50_trieu: 14,
    salary_p75_trieu: 20,
    trend_pct: null,
    salary_sample_count: 20,
    low_confidence: false,
    top_regions: ["hanoi"],
    top_skills: ["Excel", "SQL"],
    source_note: "Snapshot kiểm thử",
  },
  routes: [
    { type: "certificate", label: "Chứng chỉ ngắn hạn", detail: "", first_steps: ["Thử một bài thực hành"] },
    { type: "college", label: "Cao đẳng", detail: "", first_steps: ["So chương trình học"] },
  ],
  skill_roadmap: [{ skill: "SQL", status: "can-bo-sung" }],
  job_readiness: {
    band: "build_foundation",
    band_reason: "Hồ sơ chưa có project hoặc thực tập.",
    matched_skills: [{ skill: "Excel", evidence: "Em mới học Excel cơ bản" }],
    missing_skills: ["SQL"],
    search_queries: ["data analyst fresher"],
    actions_30d: [
      {
        week: 1,
        action: "Làm bài SQL nhỏ",
        deliverable: "Một file truy vấn có thể kiểm tra",
        why: "Tạo evidence thay vì tự nhận",
      },
    ],
  },
};

describe("RecommendationCard — Launch discoverability", () => {
  it("hiện readiness khi card đóng và mở thẳng kế hoạch bằng một click", async () => {
    render(<RecommendationCard rec={launchRecommendation} rank={1} />);

    expect(screen.getByText("Cần xây thêm nền tảng")).toBeInTheDocument();
    expect(screen.getByText(/1 kỹ năng có minh chứng · 1 khoảng trống/i)).toBeInTheDocument();
    expect(screen.queryByText("Làm bài SQL nhỏ")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /xem khoảng trống.*30 ngày/i }));

    expect(screen.getByRole("tab", { name: "Độ sẵn sàng" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("Làm bài SQL nhỏ")).toBeInTheDocument();
    expect(screen.getByText("Một file truy vấn có thể kiểm tra")).toBeInTheDocument();
  });
});
