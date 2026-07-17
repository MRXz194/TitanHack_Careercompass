/**
 * Fetch core cho lib/api.ts — parse error envelope {"error":{code,message}} của contract §5
 * và timeout mặc định để UI không treo vô hạn khi BE không phản hồi (F1-05).
 */

export const DEFAULT_TIMEOUT_MS = 45_000; // chat LLM có thể chậm; UI vẫn có typing indicator

export function extractApiError(body: unknown, status: number): string {
  if (body && typeof body === "object" && "error" in body) {
    const err = (body as { error?: { message?: unknown } }).error;
    if (err && typeof err.message === "string" && err.message) return err.message;
  }
  return `Yêu cầu thất bại (HTTP ${status})`;
}

export async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  const signal = init?.signal ?? controller.signal;
  try {
    const res = await fetch(url, { ...init, signal });
    if (!res.ok) {
      let body: unknown = null;
      try {
        body = await res.json();
      } catch {
        // body không phải JSON (VD trang lỗi gateway) — dùng fallback theo status
      }
      throw new Error(extractApiError(body, res.status));
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}
