// F1-02/F1-01/F1-06 logic: one message at a time, retry, done gating, mode reset semantics.
import { describe, expect, it } from "vitest";
import {
  chatReducer, initialChatState, canSend, canChangeModeFreely, type ChatState,
} from "@/lib/chat/machine";
import type { Profile } from "@/types";

const profile = (over: Partial<Profile> = {}): Profile => ({
  session_id: "t", journey_mode: "explore", education_stage: null, job_goal: null,
  dimensions: { ky_thuat: 0.1, phan_tich: 0, sang_tao: 0, xa_hoi: 0, quan_ly: 0 },
  skills: [], interests: [], constraints: { region_pref: null, study_budget: null, study_duration_pref: null, notes: "" },
  evidence_quotes: [], experiences: [], completeness: 0.1, ...over,
});

const opened = (): ChatState =>
  chatReducer(chatReducer(initialChatState("explore"), { type: "OPEN" }), {
    type: "RECEIVE", res: { reply: "Chào bạn!", phase: "warmup", turn: 1, done: false, profile: profile() },
  });

describe("chatReducer — luồng cơ bản", () => {
  it("OPEN đặt trạng thái pending, chưa có message user", () => {
    const s = chatReducer(initialChatState("explore"), { type: "OPEN" });
    expect(s.pending).toBe(true);
    expect(s.messages).toHaveLength(0);
  });

  it("RECEIVE thêm reply AI, lưu profile, tắt pending", () => {
    const s = opened();
    expect(s.pending).toBe(false);
    expect(s.messages).toEqual([{ role: "ai", text: "Chào bạn!" }]);
    expect(s.profile?.completeness).toBe(0.1);
    expect(s.phase).toBe("warmup");
  });

  it("SEND thêm message user và bật pending", () => {
    const s = chatReducer(opened(), { type: "SEND", text: "em thích vẽ" });
    expect(s.pending).toBe(true);
    expect(s.messages.at(-1)).toEqual({ role: "user", text: "em thích vẽ" });
  });

  it("done=true khóa gửi tiếp và bật CTA", () => {
    const s = chatReducer(opened(), {
      type: "RECEIVE", res: { reply: "Xong rồi!", phase: "wrapup", turn: 7, done: true, profile: profile() },
    });
    expect(s.done).toBe(true);
    expect(canSend(s, "câu nữa")).toBe(false);
  });
});

describe("canSend — one message at a time (F1-02)", () => {
  it("chặn khi đang pending", () => {
    const s = chatReducer(opened(), { type: "SEND", text: "a" });
    expect(canSend(s, "b")).toBe(false);
  });
  it("chặn text rỗng/toàn khoảng trắng", () => {
    expect(canSend(opened(), "   ")).toBe(false);
    expect(canSend(opened(), "")).toBe(false);
  });
  it("cho gửi khi idle và có text", () => {
    expect(canSend(opened(), "em thích vẽ")).toBe(true);
  });
});

describe("lỗi mạng + retry (F1-02)", () => {
  it("FAIL tắt pending, đặt error, giữ nguyên message user để retry", () => {
    let s = chatReducer(opened(), { type: "SEND", text: "em thích vẽ" });
    s = chatReducer(s, { type: "FAIL" });
    expect(s.pending).toBe(false);
    expect(s.error).toBe(true);
    expect(s.lastUserText).toBe("em thích vẽ");
    expect(s.messages.at(-1)).toEqual({ role: "user", text: "em thích vẽ" });
  });

  it("RETRY bật lại pending, xóa error, KHÔNG nhân đôi message user", () => {
    let s = chatReducer(opened(), { type: "SEND", text: "em thích vẽ" });
    s = chatReducer(s, { type: "FAIL" });
    const before = s.messages.length;
    s = chatReducer(s, { type: "RETRY" });
    expect(s.pending).toBe(true);
    expect(s.error).toBe(false);
    expect(s.messages).toHaveLength(before);
  });

  it("RECEIVE sau retry xóa lastUserText", () => {
    let s = chatReducer(opened(), { type: "SEND", text: "x" });
    s = chatReducer(s, { type: "FAIL" });
    s = chatReducer(s, { type: "RETRY" });
    s = chatReducer(s, { type: "RECEIVE", res: { reply: "ok", phase: "interests", turn: 2, done: false, profile: profile() } });
    expect(s.lastUserText).toBeNull();
    expect(s.error).toBe(false);
  });
});

describe("mode semantics (F1-01)", () => {
  it("đổi mode tự do khi user CHƯA trả lời lượt nào", () => {
    expect(canChangeModeFreely(initialChatState("explore"))).toBe(true);
    expect(canChangeModeFreely(opened())).toBe(true); // mới chỉ có lời chào AI
  });

  it("sau khi user đã trả lời → đổi mode cần confirm reset", () => {
    const s = chatReducer(opened(), { type: "SEND", text: "em lớp 12" });
    expect(canChangeModeFreely(s)).toBe(false);
  });

  it("RESET_MODE xóa sạch hội thoại + profile, đổi mode, quay về pending OPEN", () => {
    let s = chatReducer(opened(), { type: "SEND", text: "em lớp 12" });
    s = chatReducer(s, { type: "RESET_MODE", mode: "launch" });
    expect(s.mode).toBe("launch");
    expect(s.messages).toHaveLength(0);
    expect(s.profile).toBeNull();
    expect(s.done).toBe(false);
    expect(s.pending).toBe(false); // page sẽ dispatch OPEN lại
  });
});

describe("PROFILE_PATCHED (F1-04)", () => {
  it("thay profile bằng bản server trả về, không đụng hội thoại", () => {
    const s0 = opened();
    const s = chatReducer(s0, { type: "PROFILE_PATCHED", profile: profile({ interests: ["vẽ"] }) });
    expect(s.profile?.interests).toEqual(["vẽ"]);
    expect(s.messages).toEqual(s0.messages);
  });
});
