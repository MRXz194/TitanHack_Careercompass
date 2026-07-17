// Mock market data — khớp shape MarketOverview / SkillGapResponse.
import type { MarketOverview, Region, SkillGapResponse } from "@/types";

export async function mockOverview(region: Region): Promise<MarketOverview> {
  await new Promise((r) => setTimeout(r, 400));
  return {
    region, postings_count: 3412, window_days: 90, updated_at: "mock",
    source_note: "Dữ liệu mẫu (mock) — thay bằng snapshot thật sau MI-04",
    rising_careers: [
      { career_id: "logistics-van-hanh", title: "Vận hành Logistics", trend_pct: 31, demand_count: 890, low_confidence: true },
      { career_id: "data-analyst", title: "Phân tích dữ liệu", trend_pct: 28, demand_count: 720, low_confidence: true },
      { career_id: "dau-bep", title: "Đầu bếp", trend_pct: 26, demand_count: 470, low_confidence: true },
      { career_id: "ky-thuat-vien-dien-lanh", title: "KTV điện lạnh", trend_pct: 23, demand_count: 412, low_confidence: true },
    ],
    top_paying: [
      { career_id: "lap-trinh-vien-web", title: "Lập trình viên Web", salary_p50_trieu: 18 },
      { career_id: "data-analyst", title: "Phân tích dữ liệu", salary_p50_trieu: 16 },
    ],
  };
}

export async function mockSkillGaps(region: Region): Promise<SkillGapResponse> {
  await new Promise((r) => setTimeout(r, 400));
  return {
    region,
    source_note: "Dữ liệu mẫu (mock) — thay bằng snapshot thật sau MI-05",
    skills: [
      { skill: "điện lạnh dân dụng", gap_score: 0.82, demand_count: 412, trend_pct: 23, low_confidence: true, related_careers: ["ky-thuat-vien-dien-lanh"] },
      { skill: "tiếng Anh", gap_score: 0.75, demand_count: 890, trend_pct: 31, low_confidence: true, related_careers: ["logistics-van-hanh"] },
      { skill: "SQL", gap_score: 0.71, demand_count: 720, trend_pct: 28, low_confidence: true, related_careers: ["data-analyst"] },
      { skill: "vận hành CNC", gap_score: 0.66, demand_count: 530, trend_pct: 18, low_confidence: true, related_careers: ["co-khi-cnc"] },
      { skill: "kỹ thuật bếp", gap_score: 0.61, demand_count: 470, trend_pct: 26, low_confidence: true, related_careers: ["dau-bep"] },
    ],
  };
}
