// Mock market data — Khớp shape MarketOverview / SkillGapResponse và hỗ trợ thay đổi dữ liệu theo vùng miền.
import type { MarketOverview, Region, SkillGapResponse } from "@/types";

const REGION_OVERVIEW: Record<Region, Omit<MarketOverview, "region" | "demand_leaders">> = {
  hanoi: {
    postings_count: 1420,
    window_days: 90,
    updated_at: "18/07/2026",
    source_note: "Dữ liệu mẫu Hà Nội — thay bằng snapshot thật sau MI-04",
    rising_careers: [
      { career_id: "lap-trinh-vien-web", title: "Lập trình viên Web", trend_pct: 35, demand_count: 650, low_confidence: false },
      { career_id: "data-analyst", title: "Phân tích dữ liệu", trend_pct: 22, demand_count: 310, low_confidence: false },
      { career_id: "thiet-ke-do-hoa", title: "Thiết kế đồ họa", trend_pct: 12, demand_count: 240, low_confidence: false },
    ],
    top_paying: [
      { career_id: "lap-trinh-vien-web", title: "Lập trình viên Web", salary_p50_trieu: 22 },
      { career_id: "data-analyst", title: "Phân tích dữ liệu", salary_p50_trieu: 18 },
    ],
  },
  hcm: {
    postings_count: 1980,
    window_days: 90,
    updated_at: "18/07/2026",
    source_note: "Dữ liệu mẫu TP.HCM — thay bằng snapshot thật sau MI-04",
    rising_careers: [
      { career_id: "logistics-van-hanh", title: "Vận hành Logistics", trend_pct: 42, demand_count: 780, low_confidence: false },
      { career_id: "marketing-digital", title: "Marketing Digital", trend_pct: 30, demand_count: 510, low_confidence: false },
      { career_id: "thiet-ke-do-hoa", title: "Thiết kế đồ họa", trend_pct: 15, demand_count: 290, low_confidence: false },
    ],
    top_paying: [
      { career_id: "logistics-van-hanh", title: "Vận hành Logistics", salary_p50_trieu: 19 },
      { career_id: "thiet-ke-do-hoa", title: "Thiết kế đồ họa", salary_p50_trieu: 15 },
    ],
  },
  danang: {
    postings_count: 612,
    window_days: 90,
    updated_at: "18/07/2026",
    source_note: "Dữ liệu mẫu Đà Nẵng — thay bằng snapshot thật sau MI-04",
    rising_careers: [
      { career_id: "ky-thuat-vien-dien-lanh", title: "KTV điện lạnh", trend_pct: 23, demand_count: 412, low_confidence: false },
      { career_id: "dau-bep", title: "Đầu bếp chuyên nghiệp", trend_pct: 18, demand_count: 180, low_confidence: false },
      { career_id: "co-khi-cnc", title: "Kỹ thuật CNC", trend_pct: 12, demand_count: 90, low_confidence: true },
    ],
    top_paying: [
      { career_id: "dau-bep", title: "Đầu bếp chuyên nghiệp", salary_p50_trieu: 14 },
      { career_id: "ky-thuat-vien-dien-lanh", title: "KTV điện lạnh", salary_p50_trieu: 12 },
    ],
  },
  all: {
    postings_count: 4012,
    window_days: 90,
    updated_at: "18/07/2026",
    source_note: "Dữ liệu mẫu toàn quốc — thay bằng snapshot thật sau MI-04",
    rising_careers: [
      { career_id: "lap-trinh-vien-web", title: "Lập trình viên Web", trend_pct: 25, demand_count: 1850, low_confidence: false },
      { career_id: "logistics-van-hanh", title: "Vận hành Logistics", trend_pct: 20, demand_count: 890, low_confidence: false },
      { career_id: "data-analyst", title: "Phân tích dữ liệu", trend_pct: 18, demand_count: 720, low_confidence: false },
    ],
    top_paying: [
      { career_id: "lap-trinh-vien-web", title: "Lập trình viên Web", salary_p50_trieu: 20 },
      { career_id: "data-analyst", title: "Phân tích dữ liệu", salary_p50_trieu: 17 },
    ],
  },
  other: {
    postings_count: 120,
    window_days: 90,
    updated_at: "18/07/2026",
    source_note: "Dữ liệu mẫu vùng khác — thay bằng snapshot thật sau MI-04",
    rising_careers: [
      { career_id: "dau-bep", title: "Đầu bếp", trend_pct: 5, demand_count: 40, low_confidence: true },
    ],
    top_paying: [
      { career_id: "dau-bep", title: "Đầu bếp", salary_p50_trieu: 10 },
    ],
  }
};

const REGION_SKILLS: Record<Region, Omit<SkillGapResponse, "region">> = {
  hanoi: {
    source_note: "Dữ liệu mẫu kỹ năng Hà Nội — thay bằng snapshot thật sau MI-05",
    skills: [
      { skill: "JavaScript", gap_score: 0.85, demand_count: 650, trend_pct: 35, low_confidence: false, related_careers: ["lap-trinh-vien-web"] },
      { skill: "React", gap_score: 0.78, demand_count: 520, trend_pct: 28, low_confidence: false, related_careers: ["lap-trinh-vien-web"] },
      { skill: "SQL", gap_score: 0.72, demand_count: 310, trend_pct: 22, low_confidence: false, related_careers: ["data-analyst"] },
      { skill: "Python", gap_score: 0.65, demand_count: 280, trend_pct: 18, low_confidence: false, related_careers: ["data-analyst"] },
      { skill: "Photoshop", gap_score: 0.58, demand_count: 240, trend_pct: 12, low_confidence: false, related_careers: ["thiet-ke-do-hoa"] },
    ]
  },
  hcm: {
    source_note: "Dữ liệu mẫu kỹ năng TP.HCM — thay bằng snapshot thật sau MI-05",
    skills: [
      { skill: "Tiếng Anh thương mại", gap_score: 0.89, demand_count: 780, trend_pct: 42, low_confidence: false, related_careers: ["logistics-van-hanh"] },
      { skill: "Excel nâng cao", gap_score: 0.81, demand_count: 720, trend_pct: 35, low_confidence: false, related_careers: ["logistics-van-hanh"] },
      { skill: "Digital Ads (Facebook/Google)", gap_score: 0.76, demand_count: 510, trend_pct: 30, low_confidence: false, related_careers: ["marketing-digital"] },
      { skill: "Figma", gap_score: 0.69, demand_count: 290, trend_pct: 15, low_confidence: false, related_careers: ["thiet-ke-do-hoa"] },
    ]
  },
  danang: {
    source_note: "Dữ liệu mẫu kỹ năng Đà Nẵng — thay bằng snapshot thật sau MI-05",
    skills: [
      { skill: "Điện lạnh dân dụng", gap_score: 0.82, demand_count: 412, trend_pct: 23, low_confidence: false, related_careers: ["ky-thuat-vien-dien-lanh"] },
      { skill: "Kỹ thuật nấu bếp", gap_score: 0.71, demand_count: 180, trend_pct: 18, low_confidence: false, related_careers: ["dau-bep"] },
      { skill: "Vận hành máy CNC", gap_score: 0.62, demand_count: 90, trend_pct: 12, low_confidence: true, related_careers: ["co-khi-cnc"] },
      { skill: "Đọc sơ đồ mạch", gap_score: 0.58, demand_count: 240, trend_pct: 8, low_confidence: false, related_careers: ["ky-thuat-vien-dien-lanh"] },
    ]
  },
  all: {
    source_note: "Dữ liệu mẫu kỹ năng toàn quốc — thay bằng snapshot thật sau MI-05",
    skills: [
      { skill: "Tiếng Anh", gap_score: 0.88, demand_count: 2100, trend_pct: 28, low_confidence: false, related_careers: ["logistics-van-hanh", "lap-trinh-vien-web"] },
      { skill: "JavaScript", gap_score: 0.82, demand_count: 1850, trend_pct: 25, low_confidence: false, related_careers: ["lap-trinh-vien-web"] },
      { skill: "Excel", gap_score: 0.75, demand_count: 1420, trend_pct: 18, low_confidence: false, related_careers: ["logistics-van-hanh"] },
      { skill: "SQL", gap_score: 0.68, demand_count: 950, trend_pct: 15, low_confidence: false, related_careers: ["data-analyst"] },
      { skill: "Figma/Design tools", gap_score: 0.61, demand_count: 620, trend_pct: 10, low_confidence: false, related_careers: ["thiet-ke-do-hoa"] },
    ]
  },
  other: {
    source_note: "Dữ liệu mẫu kỹ năng vùng khác — thay bằng snapshot thật sau MI-05",
    skills: [
      { skill: "Kỹ năng khách hàng", gap_score: 0.55, demand_count: 40, trend_pct: 5, low_confidence: true, related_careers: ["dau-bep"] },
    ]
  }
};

export async function mockOverview(region: Region): Promise<MarketOverview> {
  await new Promise((r) => setTimeout(r, 450));
  const data = REGION_OVERVIEW[region] || REGION_OVERVIEW["all"];
  return {
    region,
    ...data,
    demand_leaders: data.rising_careers
      .map(({ career_id, title, demand_count, low_confidence }) => ({
        career_id,
        title,
        demand_count,
        low_confidence,
      }))
      .sort((a, b) => b.demand_count - a.demand_count),
  };
}

export async function mockSkillGaps(region: Region): Promise<SkillGapResponse> {
  await new Promise((r) => setTimeout(r, 450));
  const data = REGION_SKILLS[region] || REGION_SKILLS["all"];
  return {
    region,
    ...data
  };
}
