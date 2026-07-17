// F1-05: live mode phải đọc được error envelope {"error":{code,message}} của BE (API_CONTRACT §5)
// và không treo vô hạn khi BE không phản hồi (timeout → lỗi để UI hiện nút "Gửi lại").
import { afterEach, describe, expect, it, vi } from "vitest";
import { extractApiError, requestJson } from "@/lib/api-core";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("extractApiError", () => {
  it("đọc message từ envelope chuẩn của contract", () => {
    expect(extractApiError({ error: { code: "404", message: "career not found" } }, 404))
      .toBe("career not found");
  });
  it("body không đúng envelope → fallback theo status", () => {
    expect(extractApiError({ detail: "x" }, 500)).toMatch(/500/);
    expect(extractApiError(null, 422)).toMatch(/422/);
  });
});

describe("requestJson", () => {
  it("2xx → trả JSON đã parse", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ ok: 1 }), { status: 200 })));
    await expect(requestJson<{ ok: number }>("http://x/api/health")).resolves.toEqual({ ok: 1 });
  });

  it("lỗi có envelope → throw Error mang message của BE", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      new Response(JSON.stringify({ error: { code: "404", message: "session not found" } }), { status: 404 })));
    await expect(requestJson("http://x/api/profile/abc")).rejects.toThrow("session not found");
  });

  it("lỗi body không phải JSON → vẫn throw (không crash vì parse)", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("<html>gateway</html>", { status: 502 })));
    await expect(requestJson("http://x/api/chat")).rejects.toThrow(/502/);
  });

  it("truyền AbortSignal — fetch bị abort → reject (UI hiện retry)", async () => {
    vi.stubGlobal("fetch", vi.fn((_url: string, init?: RequestInit) =>
      new Promise((_res, rej) => init?.signal?.addEventListener("abort", () => rej(new DOMException("aborted", "AbortError"))))));
    const controller = new AbortController();
    const p = requestJson("http://x/api/chat", { signal: controller.signal });
    controller.abort();
    await expect(p).rejects.toThrow();
  });
});
