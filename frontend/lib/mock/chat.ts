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
const MOCK_PROFILE_KEY = "cc_mock_profile";
const MOCK_TURN_KEY = "cc_mock_turn";
const MOCK_MODE_KEY = "cc_mock_mode";

const emptyProfile = (journeyMode: JourneyMode): Profile => ({
  session_id: "mock",
  journey_mode: journeyMode,
  education_stage: null,
  job_goal: null,
  dimensions: { ky_thuat: 0, phan_tich: 0, sang_tao: 0, xa_hoi: 0, quan_ly: 0 },
  skills: [],
  interests: [],
  constraints: { region_pref: null, study_budget: null, study_duration_pref: null, notes: "" },
  evidence_quotes: [],
  experiences: [],
  completeness: 0,
});

let currentProfile: Profile = emptyProfile(activeMode);

const fold = (value: string) => value
  .toLowerCase()
  .replace(/đ/g, "d")
  .normalize("NFD")
  .replace(/[\u0300-\u036f]/g, "");

function redactForProfile(value: string): string {
  return value
    .replace(/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, "[email đã ẩn]")
    .replace(/(?<!\d)(?:\+?84|0)(?:[\s.\-]?\d){8,10}(?!\d)/g, "[số điện thoại đã ẩn]")
    .replace(/\bsk-[A-Z0-9_-]{8,}\b/gi, "[khóa bí mật đã ẩn]")
    .replace(/\b(?:GPA|điểm\s+trung\s+bình|diem\s+trung\s+binh)\s*[:=]?\s*\d+(?:[.,]\d+)?(?:\s*\/\s*\d+(?:[.,]\d+)?)?/gi, "")
    .replace(/(^|[^\p{L}\p{N}_])(?:địa\s*chỉ|dia\s*chi)\s*[:=\-]?\s*[^\n,;.!?]{1,120}/giu, "$1")
    .replace(
      /(^|[^\p{L}\p{N}_])(?:(?:tên|ten)\s+(?:em|tôi|toi|mình|minh|cháu|chau)|(?:em|tôi|toi|mình|minh|cháu|chau)\s+(?:tên|ten))\s+(?:là|la)\s+[^\n,;.!?]{1,80}/giu,
      "$1",
    )
    .replace(
      /(^|[^\p{L}\p{N}_])(?:em|tôi|toi|mình|minh|cháu|chau)\s+(?:là|la)\s+(?:nam|nữ|nu)(?=$|[^\p{L}\p{N}_])/giu,
      "$1",
    )
    .replace(/\b(?:GPA|Bách\s+Khoa|NEU|FTU|RMIT)\b/gi, "")
    .replace(/\s+/g, " ")
    .trim();
}

function hasMeaningfulProfileText(value: string): boolean {
  const withoutRedactedFields = value.replace(
    /\b(?:e-?mail|mail|số(?:\s+điện\s+thoại)?|sđt|phone|điện\s+thoại|api\s*key|key)\s*[:=]?\s*\[(?:email|số điện thoại|khóa bí mật) đã ẩn\]/gi,
    " ",
  );
  const withoutMarkers = withoutRedactedFields.replace(
    /\[(?:email|số điện thoại|khóa bí mật) đã ẩn\]/gi,
    " ",
  );
  const withoutPrivacyBoilerplate = withoutMarkers.replace(
    /(^|[^\p{L}\p{N}_])(?:em|tôi|toi|mình|minh|cháu|chau|của|cua|là|la|và|va|liên\s+hệ|lien\s+he|qua|số|so|điện\s+thoại|dien\s+thoai|e-?mail|mail|sđt|sdt|phone|api|key)(?=$|[^\p{L}\p{N}_])/giu,
    "$1",
  );
  return /[\p{L}\p{N}_]/u.test(withoutPrivacyBoilerplate);
}

function persistMockProfile(profile: Profile): void {
  currentProfile = profile;
  if (typeof window !== "undefined") {
    localStorage.setItem(MOCK_PROFILE_KEY, JSON.stringify(profile));
  }
}

export function getMockProfile(): Profile {
  if (typeof window !== "undefined") {
    const raw = localStorage.getItem(MOCK_PROFILE_KEY);
    if (raw) {
      try {
        currentProfile = JSON.parse(raw) as Profile;
      } catch {
        localStorage.removeItem(MOCK_PROFILE_KEY);
      }
    }
  }
  return structuredClone(currentProfile);
}

export function setMockProfile(profile: Profile): void {
  persistMockProfile(structuredClone(profile));
}

export function resetMockChat(mode: JourneyMode = "explore"): void {
  turn = 0;
  activeMode = mode;
  currentProfile = emptyProfile(mode);
  if (typeof window !== "undefined") {
    localStorage.removeItem(MOCK_PROFILE_KEY);
    localStorage.removeItem(MOCK_TURN_KEY);
    localStorage.removeItem(MOCK_MODE_KEY);
  }
}

function hydrateMockRuntime(): void {
  if (typeof window === "undefined") return;
  const rawTurn = localStorage.getItem(MOCK_TURN_KEY);
  const rawMode = localStorage.getItem(MOCK_MODE_KEY);
  if (rawTurn === null) {
    // Profiles from an older mock build have no phase/turn authority. Reusing one
    // would pair old evidence with a fresh scripted conversation.
    if (localStorage.getItem(MOCK_PROFILE_KEY)) {
      localStorage.removeItem(MOCK_PROFILE_KEY);
      currentProfile = emptyProfile(activeMode);
    }
    return;
  }
  const parsed = Number.parseInt(rawTurn, 10);
  turn = Number.isFinite(parsed) ? Math.max(0, parsed) : 0;
  if (rawMode === "explore" || rawMode === "launch") activeMode = rawMode;
}

function persistMockRuntime(): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(MOCK_TURN_KEY, String(turn));
  localStorage.setItem(MOCK_MODE_KEY, activeMode);
}

function containsPhrase(text: string, phrase: string): boolean {
  const escaped = fold(phrase).replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/\s+/g, "\\s+");
  return new RegExp(`(^|[^a-z0-9])${escaped}(?=$|[^a-z0-9])`).test(text);
}

function includesAny(text: string, words: string[]): boolean {
  return words.some((word) => containsPhrase(text, word));
}

function isNegatedSkill(text: string, token: string): boolean {
  const matches = [...text.matchAll(new RegExp(`(^|[^a-z0-9])${token}(?=$|[^a-z0-9])`, "g"))];
  if (matches.length === 0) return false;
  return matches.every((match) => {
    const start = match.index ?? 0;
    const context = text.slice(Math.max(0, start - 64), start)
      .split(/[,.!?;]|\b(?:nhung|tuy nhien|con|song)\b/).at(-1) ?? "";
    return includesAny(context, [
      "không biết", "chưa biết", "không dùng", "chưa dùng",
      "không giỏi", "chưa giỏi", "không có kinh nghiệm",
    ]);
  });
}

function inferMockProfile(message: string, journeyMode: JourneyMode): Profile {
  const profile = getMockProfile();
  profile.journey_mode = journeyMode;
  const safeMessage = redactForProfile(message);
  const text = fold(safeMessage);
  const bump = (dimension: keyof Profile["dimensions"], words: string[]) => {
    if (includesAny(text, words)) {
      profile.dimensions[dimension] = Math.min(0.9, Math.max(0.55, profile.dimensions[dimension] + 0.15));
    }
  };
  bump("ky_thuat", [
    "sửa đồ", "sửa quạt", "sửa xe", "sửa máy", "sửa chữa", "đồ điện", "điện lạnh",
    "mạch điện", "máy móc", "vận hành máy", "lắp ráp", "code", "lập trình", "cơ khí", "hàn dây",
  ]);
  bump("phan_tich", ["dữ liệu", "excel", "phân tích", "dashboard", "số liệu", "logic", "toán", "sql"]);
  bump("sang_tao", [
    "vẽ tranh", "vẽ tay", "vẽ logo", "thiết kế", "nhạc", "sáng tạo", "viết bài",
    "viết truyện", "viết content", "photoshop", "figma", "quay video", "dựng phim",
  ]);
  bump("xa_hoi", [
    "dạy học", "dạy bạn", "dạy trẻ", "dạy tiếng", "hướng dẫn", "giúp", "tình nguyện",
    "chăm sóc", "tư vấn", "giao tiếp",
  ]);
  bump("quan_ly", ["tổ chức", "lịch", "nhóm", "quản lý", "điều phối", "kinh doanh"]);

  const tools: [string, string][] = [
    ["excel", "Excel"], ["sql", "SQL"], ["python", "Python"], ["react", "React"],
    ["figma", "Figma"], ["photoshop", "Photoshop"], ["javascript", "JavaScript"],
  ];
  for (const [token, name] of tools) {
    if (containsPhrase(text, token) && !isNegatedSkill(text, token)
      && !profile.skills.some((skill) => skill.name === name)) {
      profile.skills.push({ name, level: "đã đề cập trong bản demo", source_quote: safeMessage.slice(0, 240) });
    }
  }

  const uncertain = includesAny(text, ["không biết", "chưa biết", "không rõ", "chưa rõ"]);
  const activityWords = [
    "sửa đồ", "sửa quạt", "sửa xe", "vẽ tranh", "vẽ tay", "code", "lập trình",
    "dashboard", "excel", "nấu ăn", "dạy học", "dạy bạn", "thiết kế", "chăm sóc",
    "phân tích", "máy móc", "hàn dây", "game", "viết bài", "quay video", "tổ chức",
  ];
  const activity = includesAny(text, activityWords);
  if (!uncertain && activity) {
    const activityClause = safeMessage
      .split(/[,.!?;]+/)
      .map((part) => part.trim())
      .find((part) => includesAny(fold(part), activityWords));
    const label = (activityClause || safeMessage).trim().slice(0, 60);
    if (label && !profile.interests.includes(label)) profile.interests.push(label);
  }

  if (includesAny(text, ["ha noi", "hanoi"])) profile.constraints.region_pref = "hanoi";
  if (includesAny(text, ["da nang", "danang"])) profile.constraints.region_pref = "danang";
  if (includesAny(text, ["hcm", "sai gon"])) profile.constraints.region_pref = "hcm";
  if (includesAny(text, ["hạn chế", "ngân sách thấp", "không có nhiều tiền"])) profile.constraints.study_budget = "hạn chế";

  if (journeyMode === "launch") {
    if (includesAny(text, ["năm cuối", "final year"])) profile.education_stage = "final_year";
    if (includesAny(text, ["mới tốt nghiệp", "tốt nghiệp"])) profile.education_stage = "recent_graduate";
    if (includesAny(text, ["data", "dữ liệu", "excel", "dashboard"])) profile.job_goal = "vai trò dữ liệu entry-level";
    else if (includesAny(text, ["lập trình", "react", "python", "web", "code"])) profile.job_goal = "vai trò lập trình entry-level";
    const noExperience = includesAny(text, [
      "chưa có project", "không có project", "chưa có thực tập", "không có thực tập",
      "chưa có kinh nghiệm", "chưa từng thực tập",
    ]);
    if (noExperience) profile.constraints.notes = "Chưa có project/thực tập — do người dùng xác nhận";
    if (!noExperience && includesAny(text, ["project", "dashboard", "thực tập", "internship"])
      && profile.experiences.length === 0) {
      profile.experiences.push({
        title: containsPhrase(text, "dashboard") ? "Dashboard" : "Project đã kể",
        kind: containsPhrase(text, "thuc tap") || containsPhrase(text, "internship") ? "internship" : "project",
        description: safeMessage.slice(0, 200),
        skills: profile.skills.map((skill) => skill.name),
        source_quote: safeMessage.slice(0, 240),
      });
    }
  }

  if (safeMessage) {
    profile.evidence_quotes.push({ turn, quote: safeMessage.slice(0, 240), mapped_to: "mock-evidence" });
  }
  const signalParts = [profile.interests.length > 0, profile.skills.length > 0,
    Math.max(...Object.values(profile.dimensions)) > 0, Boolean(profile.constraints.region_pref || profile.constraints.study_budget)];
  profile.completeness = Math.min(1, signalParts.filter(Boolean).length / 4 + Math.max(0, turn - 1) / 12);
  persistMockProfile(profile);
  return profile;
}

function adaptiveMockReply(
  fallback: string,
  phase: Phase,
  profile: Profile,
  message: string | null,
): string {
  if (!message || phase === "warmup" || phase === "constraints" || phase === "wrapup") return fallback;
  const [dimension, strength] = Object.entries(profile.dimensions).sort((a, b) => b[1] - a[1])[0];
  if (!dimension || strength <= 0) return fallback;
  const focus: Record<string, string> = {
    ky_thuat: "việc sửa chữa hoặc thực hành đó",
    phan_tich: "lúc phân tích và tìm ra nguyên nhân",
    sang_tao: "sản phẩm sáng tạo đó",
    xa_hoi: "lúc giúp hoặc hướng dẫn người khác",
    quan_ly: "việc tổ chức và điều phối đó",
  };
  if (phase === "interests") {
    return `Trong ${focus[dimension]}, khoảnh khắc nào làm bạn thấy cuốn nhất?`;
  }
  if (phase === "abilities") {
    return `Với ${focus[dimension]}, bạn đã trực tiếp làm phần nào và có kết quả cụ thể nào để kể lại?`;
  }
  return fallback;
}

export async function mockChat(_message: string | null, journeyMode: JourneyMode = "explore"): Promise<ChatResponse> {
  await new Promise((r) => setTimeout(r, 600)); // giả lập latency
  hydrateMockRuntime();
  if (journeyMode !== activeMode) {
    resetMockChat(journeyMode);
  }
  const script = journeyMode === "launch" ? LAUNCH_SCRIPT : SCRIPT;
  if (_message !== null && _message.trim() && !hasMeaningfulProfileText(redactForProfile(_message))) {
    const step = script[Math.min(Math.max(turn - 1, 0), script.length - 1)];
    return {
      reply: "Mình không dùng thông tin nhận dạng đó để định hướng. Bạn hãy kể một hoạt động, kỹ năng hoặc điều kiện học tập liên quan nhé.",
      phase: step.phase,
      turn,
      done: turn >= script.length,
      profile: getMockProfile(),
    };
  }
  if (_message === null && turn > 0) {
    const step = script[Math.min(turn - 1, script.length - 1)];
    const profile = getMockProfile();
    return {
      reply: turn >= script.length
        ? "Hồ sơ demo này đã sẵn sàng. Bạn có thể xem kết quả hoặc bắt đầu một hồ sơ mới."
        : "Mình đã mở lại hồ sơ demo đang làm dở. Bạn tiếp tục từ chỗ trước nhé.",
      phase: step.phase,
      turn,
      done: turn >= script.length,
      profile,
    };
  }
  turn = Math.min(turn + 1, script.length);
  const step = script[turn - 1];
  const profile = _message ? inferMockProfile(_message, journeyMode) : getMockProfile();
  const reply = adaptiveMockReply(step.reply, step.phase, profile, _message);
  persistMockRuntime();
  return { reply, phase: step.phase, turn, done: turn >= script.length, profile };
}
