/**
 * API client — MỌI call API của FE đi qua file này. Không fetch() rải rác trong components.
 *
 * Mock mode: NEXT_PUBLIC_USE_MOCK=1 → trả mock data (lưới an toàn demo, giữ hoạt động
 * đến phút chót — TEAM_RULES.md §2). Mock phải luôn khớp shape API_CONTRACT.md.
 */
import type {
  ChatResponse, MarketOverview, Profile, RecommendationResponse, Region, SkillGapResponse,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "1";

export function getSessionId(): string {
  if (typeof window === "undefined") return "ssr";
  let id = localStorage.getItem("cc_session_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("cc_session_id", id);
  }
  return id;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  return res.json();
}

// ---------- Public API ----------

export async function sendChat(message: string | null): Promise<ChatResponse> {
  if (USE_MOCK) return (await import("./mock/chat")).mockChat(message);
  return post<ChatResponse>("/api/chat", { session_id: getSessionId(), message });
}

export async function fetchRecommendations(): Promise<RecommendationResponse> {
  if (USE_MOCK) return (await import("./mock/recommendations")).mockRecommendations();
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

export async function patchProfile(patch: {
  dimensions?: Record<string, number>;
  remove_skills?: string[];
  add_interests?: string[];
}): Promise<{ profile: Profile }> {
  // Mock mode: chỉnh sửa profile là no-op trả profile hiện tại (F1-04 hoàn thiện)
  return fetch(`${API_BASE}/api/profile/${getSessionId()}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  }).then((r) => r.json());
}
