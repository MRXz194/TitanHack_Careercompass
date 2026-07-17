// Mock recommendations — khớp shape RecommendationResponse. Số liệu khớp data/seed/careers_seed.json.
import type { Recommendation, RecommendationResponse } from "@/types";

const rec = (
  career_id: string, title: string, match_score: number, demand: number,
  p25: number, p50: number, p75: number, trend: number, skills: string[], is_stretch = false,
): Recommendation => ({
  career_id, title, match_score, is_stretch,
  why: {
    from_you: [{ quote: "em hay sửa đồ điện trong nhà", reason: "cho thấy thiên hướng thực hành - kỹ thuật rõ" }],
    from_market: [
      { stat: `${demand} tin tuyển trong 90 ngày`, stat_key: "demand_count" },
      { stat: `Lương phổ biến ${p25}–${p75} triệu`, stat_key: "salary" },
    ],
    counterfactual: "Nếu em thiên về sáng tạo hơn thực hành, gợi ý đầu bảng sẽ là Thiết kế đồ họa.",
  },
  market: {
    demand_count_90d: demand, salary_p25_trieu: p25, salary_p50_trieu: p50, salary_p75_trieu: p75,
    trend_pct: trend, top_regions: ["danang", "hcm"], top_skills: skills,
    source_note: "Dữ liệu mẫu (mock) — thay bằng số thật sau MI-04",
  },
  routes: [
    { type: "vocational", label: "Trung cấp nghề (18–24 tháng)", detail: "Vừa học vừa làm từ năm 2", first_steps: ["Tìm hiểu trường nghề gần em"] },
    { type: "college", label: "Cao đẳng (2.5–3 năm)", detail: "", first_steps: ["Tìm hiểu CĐ địa phương"] },
  ],
  skill_roadmap: skills.slice(0, 2).map((s) => ({ skill: s, status: "hoc-trong-truong" })),
});

export async function mockRecommendations(): Promise<RecommendationResponse> {
  await new Promise((r) => setTimeout(r, 900));
  return {
    generated_at: new Date().toISOString(),
    disclaimer: "Đây là gợi ý tham khảo dựa trên hồ sơ của em và dữ liệu thị trường — quyết định là của em.",
    recommendations: [
      rec("ky-thuat-vien-dien-lanh", "Kỹ thuật viên điện lạnh", 0.86, 412, 9, 12, 15, 23, ["điện lạnh dân dụng", "đọc sơ đồ mạch", "kỹ năng khách hàng"]),
      rec("co-khi-cnc", "Kỹ thuật viên cơ khí CNC", 0.79, 530, 10, 14, 19, 18, ["đọc bản vẽ", "vận hành CNC"]),
      rec("thiet-ke-do-hoa", "Thiết kế đồ họa", 0.74, 580, 8, 12, 18, 5, ["Photoshop", "Figma"]),
      rec("lap-trinh-vien-web", "Lập trình viên Web", 0.68, 1850, 12, 18, 28, 15, ["JavaScript", "React"]),
      rec("logistics-van-hanh", "Nhân viên vận hành Logistics", 0.63, 890, 9, 13, 19, 31, ["tiếng Anh", "Excel"]),
    ],
    stretch: rec("dau-bep", "Đầu bếp", 0.61, 470, 8, 12, 20, 26, ["kỹ thuật bếp", "sáng tạo món"], true),
  };
}
