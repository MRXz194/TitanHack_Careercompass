// Mock chat — khớp shape ChatResponse trong API_CONTRACT.md. Dùng khi NEXT_PUBLIC_USE_MOCK=1.
import type { ChatResponse, Phase, Profile } from "@/types";

const SCRIPT: { phase: Phase; reply: string }[] = [
  { phase: "warmup", reply: "Chào bạn! Mình là CareerCompass 🧭 Mình sẽ trò chuyện để hiểu bạn hơn — không phải bài kiểm tra đâu. Bạn đang học lớp mấy, và điều gì khiến bạn nghĩ đến chuyện chọn nghề lúc này?" },
  { phase: "interests", reply: "Kể mình nghe một việc bạn từng làm mà quên cả thời gian — học, chơi, hay việc nhà đều được!" },
  { phase: "interests", reply: "Nghe thú vị đó! Trong việc đó, bạn thích nhất khoảnh khắc nào?" },
  { phase: "abilities", reply: "Bạn bè hoặc thầy cô hay khen bạn làm tốt việc gì?" },
  { phase: "abilities", reply: "Có môn học nào bạn thấy mình học nhanh hơn các bạn không?" },
  { phase: "constraints", reply: "Về chuyện học sau này, gia đình bạn có mong muốn hay điều kiện gì đặc biệt không?" },
  { phase: "wrapup", reply: "Cảm ơn bạn! Mình đã phác được hồ sơ bên cạnh — bạn xem có đúng là bạn không? Sẵn sàng xem các hướng đi chưa?" },
];

let turn = 0;

export async function mockChat(_message: string | null): Promise<ChatResponse> {
  await new Promise((r) => setTimeout(r, 600)); // giả lập latency
  turn = Math.min(turn + 1, SCRIPT.length);
  const step = SCRIPT[turn - 1];
  const growth = turn / SCRIPT.length;
  const profile: Profile = {
    session_id: "mock",
    dimensions: {
      ky_thuat: +(0.7 * growth).toFixed(2),
      phan_tich: +(0.4 * growth).toFixed(2),
      sang_tao: +(0.8 * growth).toFixed(2),
      xa_hoi: +(0.3 * growth).toFixed(2),
      quan_ly: +(0.2 * growth).toFixed(2),
    },
    skills: turn >= 4 ? [{ name: "vẽ tay", level: "tự đánh giá khá", source_quote: "em thích vẽ" }] : [],
    interests: turn >= 2 ? ["vẽ", "sửa chữa đồ điện"].slice(0, Math.max(1, turn - 1)) : [],
    constraints: { region_pref: turn >= 6 ? "danang" : null, study_budget: turn >= 6 ? "hạn chế" : null, study_duration_pref: null, notes: "" },
    evidence_quotes: turn >= 2 ? [{ turn: 2, quote: "em hay sửa đồ điện trong nhà", mapped_to: "ky_thuat" }] : [],
    completeness: +growth.toFixed(2),
  };
  return { reply: step.reply, phase: step.phase, turn, done: turn >= SCRIPT.length, profile };
}
