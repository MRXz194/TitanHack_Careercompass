// Mock recommendations — khớp shape RecommendationResponse. Số liệu khớp data/seed/careers_seed.json.
import type { JourneyMode, Recommendation, RecommendationResponse } from "@/types";

const rec = (
  career_id: string, title: string, match_score: number, demand: number,
  p25: number, p50: number, p75: number, trend: number, skills: string[],
  is_stretch = false, journeyMode: JourneyMode = "explore",
): Recommendation => ({
  career_id, title, match_score, is_stretch,
  why: {
    from_you: journeyMode === "launch"
      ? [{ quote: "em đã làm dashboard bán hàng bằng Excel", reason: "cho thấy bạn đã có project tạo evidence cho kỹ năng công cụ và phân tích" }]
      : [{ quote: "em hay sửa đồ điện trong nhà", reason: "cho thấy thiên hướng thực hành - kỹ thuật rõ" }],
    from_market: [
      { stat: `${demand} tin tuyển trong 90 ngày`, stat_key: "demand_count" },
      { stat: `Lương phổ biến ${p25}–${p75} triệu`, stat_key: "salary" },
    ],
    counterfactual: "Nếu em thiên về sáng tạo hơn thực hành, gợi ý đầu bảng sẽ là Thiết kế đồ họa.",
  },
  market: {
    demand_count_90d: demand, entry_level_count_90d: Math.round(demand * 0.25),
    salary_p25_trieu: p25, salary_p50_trieu: p50, salary_p75_trieu: p75,
    trend_pct: trend, salary_sample_count: 30, low_confidence: false,
    top_regions: ["danang", "hcm"], top_skills: skills,
    source_note: "Dữ liệu mẫu (mock) — thay bằng số thật sau MI-04",
  },
  routes: [
    { type: "vocational", label: "Trung cấp nghề (18–24 tháng)", detail: "Vừa học vừa làm từ năm 2", first_steps: ["Tìm hiểu trường nghề gần em"] },
    { type: "college", label: "Cao đẳng (2.5–3 năm)", detail: "", first_steps: ["Tìm hiểu CĐ địa phương"] },
  ],
  skill_roadmap: skills.slice(0, 2).map((s) => ({ skill: s, status: "hoc-trong-truong" })),
  job_readiness: journeyMode === "launch" ? {
    band: skills.includes("Excel") ? "near_ready" : "build_foundation",
    band_reason: skills.includes("Excel")
      ? "Bạn đã có bằng chứng Excel qua project nhưng còn kỹ năng vai trò thường yêu cầu chưa xuất hiện trong hồ sơ."
      : "Project hiện chưa tạo evidence cho các kỹ năng cốt lõi của vai trò này; hãy xem đây là hướng cần xây nền tảng.",
    matched_skills: skills.includes("Excel") ? [{ skill: "Excel", evidence: "Project Dashboard bán hàng" }] : [],
    missing_skills: skills.filter((s) => s !== "Excel").slice(0, 2),
    search_queries: [`${title} fresher`, `${title} entry level`],
    actions_30d: [1, 2, 3, 4].map((week) => ({
      week, action: `Hoàn thiện phần ${week} của project minh chứng`,
      deliverable: `Output tuần ${week} có link hoặc file kiểm tra được`,
      why: "Tạo evidence cụ thể cho kỹ năng nhà tuyển dụng thường yêu cầu",
    })),
  } : null,
});

export async function mockRecommendations(journeyMode: JourneyMode = "explore"): Promise<RecommendationResponse> {
  await new Promise((r) => setTimeout(r, 900));
  return {
    generated_at: new Date().toISOString(),
    disclaimer: "Đây là gợi ý tham khảo dựa trên hồ sơ của em và dữ liệu thị trường — quyết định là của em.",
    recommendations: [
      rec("ky-thuat-vien-dien-lanh", "Kỹ thuật viên điện lạnh", 0.86, 412, 9, 12, 15, 23, ["điện lạnh dân dụng", "đọc sơ đồ mạch", "kỹ năng khách hàng"], false, journeyMode),
      rec("co-khi-cnc", "Kỹ thuật viên cơ khí CNC", 0.79, 530, 10, 14, 19, 18, ["đọc bản vẽ", "vận hành CNC"], false, journeyMode),
      rec("thiet-ke-do-hoa", "Thiết kế đồ họa", 0.74, 580, 8, 12, 18, 5, ["Photoshop", "Figma"], false, journeyMode),
      rec("lap-trinh-vien-web", "Lập trình viên Web", 0.68, 1850, 12, 18, 28, 15, ["JavaScript", "React"], false, journeyMode),
      rec("logistics-van-hanh", "Nhân viên vận hành Logistics", 0.63, 890, 9, 13, 19, 31, ["tiếng Anh", "Excel"], false, journeyMode),
    ],
    stretch: rec("dau-bep", "Đầu bếp", 0.61, 470, 8, 12, 20, 26, ["kỹ thuật bếp", "sáng tạo món"], true, journeyMode),
  };
}
