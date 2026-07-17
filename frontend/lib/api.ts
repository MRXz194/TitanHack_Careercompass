/**
 * API client — MỌI call API của FE đi qua file này. Không fetch() rải rác trong components.
 *
 * Mock mode: NEXT_PUBLIC_USE_MOCK=1 → trả mock data (lưới an toàn demo, giữ hoạt động
 * đến phút chót — TEAM_RULES.md §2). Mock phải luôn khớp shape API_CONTRACT.md.
 * Live mode: lỗi BE được parse từ envelope {"error":{code,message}} (contract §5),
 * có timeout — UI hiện fallback tiếng Việt + nút thử lại, không bao giờ treo.
 */
import { requestJson } from "@/lib/api-core";
import type {
  ChatResponse, JourneyMode, MarketOverview, Profile, ProfilePatch, RecommendationResponse, Region, SkillGapResponse,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "1";

/** FE hiện badge "dữ liệu mẫu" khi mock — minh bạch với người xem demo (F1-05). */
export const IS_MOCK = USE_MOCK;

export function getSessionId(): string {
  if (typeof window === "undefined") return "ssr";
  let id = localStorage.getItem("cc_session_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("cc_session_id", id);
  }
  return id;
}

const post = <T,>(path: string, body: unknown) =>
  requestJson<T>(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

const get = <T,>(path: string) => requestJson<T>(`${API_BASE}${path}`);

// ---------- Public API ----------

export async function sendChat(message: string | null, journeyMode: JourneyMode = "explore"): Promise<ChatResponse> {
  if (USE_MOCK) return (await import("./mock/chat")).mockChat(message, journeyMode);
  return post<ChatResponse>("/api/chat", { session_id: getSessionId(), message, journey_mode: journeyMode });
}

export async function fetchRecommendations(journeyMode: JourneyMode = "explore"): Promise<RecommendationResponse> {
  if (USE_MOCK) return (await import("./mock/recommendations")).mockRecommendations(journeyMode);
  return post<RecommendationResponse>("/api/recommendations", { session_id: getSessionId() });
}

export async function fetchMarketOverview(region: Region): Promise<MarketOverview> {
  if (USE_MOCK) return (await import("./mock/market")).mockOverview(region);
  return get<MarketOverview>(`/api/market/overview?region=${region}`);
}

export async function fetchSkillGaps(region: Region): Promise<SkillGapResponse> {
  if (USE_MOCK) return (await import("./mock/market")).mockSkillGaps(region);
  return get<SkillGapResponse>(`/api/market/skills?region=${region}`);
}

export async function patchProfile(patch: ProfilePatch): Promise<{ profile: Profile }> {
  if (USE_MOCK) return (await import("./mock/profile")).mockPatchProfile(patch);
  return requestJson<{ profile: Profile }>(`${API_BASE}/api/profile/${getSessionId()}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
}
