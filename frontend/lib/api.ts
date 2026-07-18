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
  CareerResearchResponse, ChatResponse, JourneyMode, MarketOverview, Profile, ProfilePatch,
  RecommendationResponse, Region, ResearchIntent, SkillGapResponse, WhatIfResponse,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "1";
const SESSION_KEY = "cc_session_id";

/** FE hiện badge "dữ liệu mẫu" khi mock — minh bạch với người xem demo (F1-05). */
export const IS_MOCK = USE_MOCK;

export function getSessionId(): string {
  if (typeof window === "undefined") return "ssr";
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

/** Start a genuinely clean journey; old server cleanup is best-effort and never blocks the UI. */
export async function resetSession(): Promise<string> {
  if (typeof window === "undefined") return "ssr";
  const previous = localStorage.getItem(SESSION_KEY);
  const next = crypto.randomUUID();
  localStorage.setItem(SESSION_KEY, next);

  if (USE_MOCK) {
    const { resetMockChat } = await import("./mock/chat");
    resetMockChat();
  } else if (previous) {
    const signal = typeof AbortSignal !== "undefined" && "timeout" in AbortSignal
      ? AbortSignal.timeout(2_000)
      : undefined;
    void requestJson<{ ok: boolean }>(`${API_BASE}/api/profile/${previous}`, {
      method: "DELETE",
      signal,
    }).catch(() => undefined);
  }
  return next;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  return requestJson<T>(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function get<T>(path: string): Promise<T> {
  return requestJson<T>(`${API_BASE}${path}`);
}

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

export async function fetchCareerResearch(
  careerIds: string[],
  intent: ResearchIntent = "overview",
  region: Region = "all",
): Promise<CareerResearchResponse> {
  if (USE_MOCK) return (await import("./mock/research")).mockCareerResearch(careerIds, intent, region);
  return requestJson<CareerResearchResponse>(`${API_BASE}/api/research/careers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: getSessionId(), career_ids: careerIds.slice(0, 2), intent, region }),
  });
}

export async function previewWhatIfSkill(skill: string): Promise<WhatIfResponse> {
  if (USE_MOCK) return (await import("./mock/what-if")).mockWhatIfSkill(skill);
  return requestJson<WhatIfResponse>(`${API_BASE}/api/recommendations/what-if`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: getSessionId(), skill }),
  });
}
