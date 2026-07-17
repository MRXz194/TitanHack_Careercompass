// Mock chat — khớp shape ChatResponse trong API_CONTRACT.md. Dùng khi NEXT_PUBLIC_USE_MOCK=1.
import type { ChatResponse, JourneyMode, Phase, Profile } from "@/types";

const SCRIPT: { phase: Phase; reply: string }[] = [
  { phase: "warmup", reply: "Chào bạn! Mình là CareerCompass 🧭 Mình sẽ trò chuyện để hiểu bạn hơn — không phải bài kiểm tra đâu. Bạn đang học lớp mấy, và điều gì khiến bạn nghĩ đến chuyện chọn nghề lúc này?" },
  { phase: "interests", reply: "Kể mình nghe một việc bạn từng làm mà quên cả thời gian — học, chơi, hay việc nhà đều được!" },
  { phase: "interests", reply: "Nghe thú vị đó! Trong việc đó, bạn thích nhất khoảnh khắc nào?" },
  { phase: "abilities", reply: "Bạn bè hoặc thầy cô hay khen bạn làm tốt việc gì?" },
  { phase: "abilities", reply: "Có môn học nào bạn thấy mình học nhanh hơn các bạn không?" },
  { phase: "constraints", reply: "Về chuyện học sau này, gia đình bạn có mong muốn hay điều kiện gì đặc biệt không?" },
  { phase: "wrapup", reply: "Cảm ơn bạn! Mình đã phác được hồ sơ bên cạnh — bạn xem có đúng là bạn không? Sẵn sàng xem các hướng đi chưa?" },
];

const LAUNCH_SCRIPT: { phase: Phase; reply: string }[] = [
  { phase: "warmup", reply: "Bạn đang ở giai đoạn nào và muốn bắt đầu tìm loại công việc gì, dù mới chỉ là ý tưởng ban đầu?" },
  { phase: "interests", reply: "Trong project, môn học, việc làm thêm hoặc hoạt động từng làm, việc nào khiến bạn muốn làm tiếp?" },
  { phase: "abilities", reply: "Với project đó, bạn đã trực tiếp làm phần nào và dùng công cụ gì?" },
  { phase: "abilities", reply: "Có output nào bạn có thể đưa cho người khác xem hoặc kiểm tra không?" },
  { phase: "constraints", reply: "Bạn muốn tìm việc ở khu vực hoặc trong khoảng thời gian nào?" },
  { phase: "wrapup", reply: "Bạn xem lại kỹ năng và trải nghiệm bên cạnh nhé — chỗ nào chưa đúng, hãy sửa trước khi xem nhóm việc phù hợp." },
];

let turn = 0;
let activeMode: JourneyMode = "explore";

export async function mockChat(_message: string | null, journeyMode: JourneyMode = "explore"): Promise<ChatResponse> {
  await new Promise((r) => setTimeout(r, 600)); // giả lập latency
  if (journeyMode !== activeMode) {
    activeMode = journeyMode;
    turn = 0;
  }
  const script = journeyMode === "launch" ? LAUNCH_SCRIPT : SCRIPT;
  turn = Math.min(turn + 1, script.length);
  const step = script[turn - 1];
  const growth = turn / script.length;
  const profile: Profile = {
    session_id: "mock",
    journey_mode: journeyMode,
    education_stage: journeyMode === "launch" ? "final_year" : "high_school",
    job_goal: journeyMode === "launch" ? "tìm vai trò dữ liệu entry-level" : null,
    dimensions: journeyMode === "launch" ? {
      ky_thuat: +(0.2 * growth).toFixed(2), phan_tich: +(0.8 * growth).toFixed(2),
      sang_tao: +(0.4 * growth).toFixed(2), xa_hoi: +(0.3 * growth).toFixed(2), quan_ly: +(0.4 * growth).toFixed(2),
    } : {
      ky_thuat: +(0.7 * growth).toFixed(2), phan_tich: +(0.4 * growth).toFixed(2),
      sang_tao: +(0.8 * growth).toFixed(2), xa_hoi: +(0.3 * growth).toFixed(2), quan_ly: +(0.2 * growth).toFixed(2),
    },
    skills: turn >= 4 ? (journeyMode === "launch"
      ? [{ name: "Excel", level: "đã dùng trong project", source_quote: "em đã làm dashboard bán hàng bằng Excel" }]
      : [{ name: "vẽ tay", level: "tự đánh giá khá", source_quote: "em thích vẽ" }]) : [],
    interests: turn >= 2 ? (journeyMode === "launch" ? ["phân tích dữ liệu"] : ["vẽ", "sửa chữa đồ điện"].slice(0, Math.max(1, turn - 1))) : [],
    constraints: { region_pref: turn >= 6 ? "danang" : null, study_budget: turn >= 6 ? "hạn chế" : null, study_duration_pref: null, notes: "" },
    evidence_quotes: turn >= 2 ? (journeyMode === "launch"
      ? [{ turn: 2, quote: "em đã làm dashboard bán hàng bằng Excel", mapped_to: "phan_tich" }]
      : [{ turn: 2, quote: "em hay sửa đồ điện trong nhà", mapped_to: "ky_thuat" }]) : [],
    experiences: journeyMode === "launch" && turn >= 4 ? [{
      title: "Dashboard bán hàng", kind: "project", description: "Dashboard từ dữ liệu mở",
      skills: ["Excel"], source_quote: "em đã làm dashboard bán hàng bằng Excel",
    }] : [],
    completeness: +growth.toFixed(2),
  };
  return { reply: step.reply, phase: step.phase, turn, done: turn >= script.length, profile };
}
