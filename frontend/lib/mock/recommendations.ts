// Mock recommendations — khớp shape RecommendationResponse. Số liệu khớp data/seed/careers_seed.json.
import type { JourneyMode, Profile, Recommendation, RecommendationResponse } from "@/types";
import { getMockProfile } from "./chat";

const rec = (
  career_id: string, title: string, match_score: number, demand: number,
  p25: number, p50: number, p75: number, trend: number, skills: string[],
  is_stretch = false,
): Recommendation => ({
  career_id, title, match_score, is_stretch,
  why: {
    // Filled from the current mock profile below. Static persona quotes here used
    // to invent the same dashboard/electrical story for unrelated users.
    from_you: [],
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
    source_note: "Dữ liệu mô phỏng cho chế độ dự phòng — không phải snapshot production",
  },
  routes: [
    { type: "vocational", label: "Trung cấp nghề (18–24 tháng)", detail: "Vừa học vừa làm từ năm 2", first_steps: ["Tìm hiểu trường nghề gần em"] },
    { type: "college", label: "Cao đẳng (2.5–3 năm)", detail: "", first_steps: ["Tìm hiểu CĐ địa phương"] },
  ],
  skill_roadmap: skills.slice(0, 2).map((s) => ({ skill: s, status: "hoc-trong-truong" })),
  job_readiness: null,
});

const normalise = (value: string) => value.trim().toLocaleLowerCase("vi");

function relatedSkill(left: string, right: string): boolean {
  const a = normalise(left);
  const b = normalise(right);
  return a === b || (Math.min(a.length, b.length) >= 4 && (a.includes(b) || b.includes(a)));
}

function mockReadiness(
  item: Recommendation,
  profile: Profile,
): NonNullable<Recommendation["job_readiness"]> {
  const signals: { name: string; evidence: string }[] = profile.skills.map((skill) => ({
    name: skill.name,
    evidence: skill.source_quote || `Kỹ năng ${skill.name} do người dùng xác nhận`,
  }));
  for (const experience of profile.experiences) {
    for (const skill of experience.skills) {
      signals.push({ name: skill, evidence: experience.source_quote || experience.title });
    }
  }
  const matchedSkills = item.market.top_skills.flatMap((careerSkill) => {
    const signal = signals.find((candidate) => relatedSkill(candidate.name, careerSkill));
    return signal ? [{ skill: careerSkill, evidence: signal.evidence }] : [];
  });
  const missingSkills = item.market.top_skills
    .filter((skill) => !matchedSkills.some((matched) => matched.skill === skill))
    .slice(0, 3);
  const hasExperience = profile.experiences.length > 0;
  const band = hasExperience && matchedSkills.length >= 2
    ? "ready_now"
    : hasExperience || matchedSkills.length >= 1
      ? "near_ready"
      : "build_foundation";
  const bandReason = band === "ready_now"
    ? `Hồ sơ có trải nghiệm và ${matchedSkills.length} kỹ năng trùng tín hiệu vai trò; vẫn cần kiểm chứng với tin tuyển thật.`
    : band === "near_ready"
      ? `Hồ sơ có ${hasExperience ? "trải nghiệm" : "một kỹ năng có evidence"}, nhưng còn khoảng trống cần tạo output kiểm tra được.`
      : "Hồ sơ chưa có project/thực tập hoặc kỹ năng trùng rõ với vai trò; đây là hướng cần xây nền tảng, không phải kết luận không phù hợp.";
  const focus = missingSkills[0] || item.market.top_skills[0] || "một kỹ năng cốt lõi";
  const actions = [
    { action: `Chọn một yêu cầu ${focus} ở 3 tin tuyển thật`, deliverable: "Bảng ghi nguồn và yêu cầu lặp lại", why: "Kiểm chứng tín hiệu trước khi học" },
    { action: `Làm bài thực hành nhỏ về ${focus}`, deliverable: "Một file hoặc link output có thể mở", why: "Biến việc học thành evidence" },
    { action: "Nhờ một người có kinh nghiệm review output", deliverable: "Danh sách phản hồi và bản sửa", why: "Giảm tự đánh giá chủ quan" },
    { action: "Cập nhật hồ sơ và so lại hai hướng", deliverable: "Bản hồ sơ mới và quyết định bước thử tiếp theo", why: "Giữ quyền tự quyết, không khóa vào top-1" },
  ];
  return {
    band,
    band_reason: bandReason,
    matched_skills: matchedSkills,
    missing_skills: missingSkills,
    search_queries: [`${item.title} fresher`, `${item.title} entry level`],
    actions_30d: actions.map((action, index) => ({ week: index + 1, ...action })),
  };
}

function personaliseMock(
  item: Recommendation,
  profile: Profile,
  journeyMode: JourneyMode,
): Recommendation {
  const evidence = profile.evidence_quotes.at(-1)?.quote
    || profile.skills.find((skill) => skill.source_quote)?.source_quote
    || profile.interests.at(-1)
    || "Tín hiệu chiều năng lực do bạn tự chỉnh trong hồ sơ demo";
  const dominant = Object.entries(profile.dimensions).sort((a, b) => b[1] - a[1])[0]?.[0];
  const labels: Record<string, string> = {
    ky_thuat: "thực hành–kỹ thuật",
    phan_tich: "phân tích–logic",
    sang_tao: "sáng tạo",
    xa_hoi: "làm việc với con người",
    quan_ly: "tổ chức–quản lý",
  };
  item.why.from_you = [{
    quote: evidence,
    reason: `tạo tín hiệu ${labels[dominant] || "cá nhân"}; thứ tự này chỉ là mô phỏng để bạn kiểm chứng thêm`,
  }];
  if (journeyMode === "launch") item.job_readiness = mockReadiness(item, profile);
  return item;
}

export async function mockRecommendations(journeyMode: JourneyMode = "explore"): Promise<RecommendationResponse> {
  await new Promise((r) => setTimeout(r, 900));
  const profile = getMockProfile();
  const hasPersonalSignal = profile.interests.length > 0
    || profile.skills.length > 0
    || profile.experiences.length > 0
    || Math.max(...Object.values(profile.dimensions)) > 0;
  if (!hasPersonalSignal) {
    throw new Error("Hồ sơ demo chưa có tín hiệu cá nhân; hãy hoàn thành hội thoại trước.");
  }
  const candidates: Record<string, Recommendation> = {
    electrical: rec("ky-thuat-vien-dien-lanh", "Kỹ thuật viên điện lạnh", 0.8, 412, 9, 12, 15, 23, ["điện lạnh dân dụng", "đọc sơ đồ mạch", "kỹ năng khách hàng"]),
    cnc: rec("co-khi-cnc", "Kỹ thuật viên cơ khí CNC", 0.8, 530, 10, 14, 19, 18, ["đọc bản vẽ", "vận hành CNC"]),
    design: rec("thiet-ke-do-hoa", "Thiết kế đồ họa", 0.8, 580, 8, 12, 18, 5, ["Photoshop", "Figma"]),
    web: rec("lap-trinh-vien-web", "Lập trình viên Web", 0.8, 1850, 12, 18, 28, 15, ["JavaScript", "React", "SQL"]),
    data: rec("data-analyst", "Chuyên viên phân tích dữ liệu", 0.8, 720, 12, 16, 25, 28, ["SQL", "Excel", "Power BI"]),
    logistics: rec("logistics-van-hanh", "Nhân viên vận hành Logistics", 0.8, 890, 9, 13, 19, 31, ["tiếng Anh", "Excel", "điều phối"]),
    marketing: rec("digital-marketing", "Chuyên viên Digital Marketing", 0.8, 1320, 9, 13, 20, 8, ["content", "quảng cáo", "phân tích số liệu"]),
    nursing: rec("dieu-duong", "Điều dưỡng viên", 0.8, 640, 8, 11, 16, 19, ["chăm sóc bệnh nhân", "giao tiếp", "chịu áp lực"]),
  };

  const dominant = Object.entries(profile.dimensions)
    .sort((a, b) => b[1] - a[1])[0];
  const family = !dominant || dominant[1] <= 0
    ? "empty"
    : dominant[0];
  const orders: Record<string, string[]> = {
    ky_thuat: ["electrical", "cnc", "web", "data", "logistics", "design"],
    phan_tich: ["data", "web", "logistics", "marketing", "design", "nursing"],
    sang_tao: ["design", "marketing", "web", "data", "logistics", "electrical"],
    xa_hoi: ["nursing", "marketing", "logistics", "design", "data", "web"],
    quan_ly: ["logistics", "marketing", "data", "web", "electrical", "nursing"],
    empty: ["web", "logistics", "data", "marketing", "electrical", "design"],
  };
  const order = orders[family] ?? orders.empty;
  const scores = [0.82, 0.76, 0.71, 0.67, 0.63];
  const evidence = profile.evidence_quotes.at(-1)?.quote;
  const recommendations = order.slice(0, 5).map((key, index) => {
    const item = structuredClone(candidates[key]);
    item.match_score = scores[index];
    if (evidence) {
      item.why.from_you = [{
        quote: evidence,
        reason: `tín hiệu trong câu trả lời này được dùng để tạo thứ tự mô phỏng cho ${item.title}`,
      }];
    }
    return personaliseMock(item, profile, journeyMode);
  });
  const stretch = personaliseMock(structuredClone(candidates[order[5]]), profile, journeyMode);
  stretch.match_score = 0.56;
  stretch.is_stretch = true;
  return {
    generated_at: new Date().toISOString(),
    disclaimer: "Đây là gợi ý tham khảo dựa trên hồ sơ của em và dữ liệu thị trường — quyết định là của em.",
    recommendations,
    stretch,
  };
}
