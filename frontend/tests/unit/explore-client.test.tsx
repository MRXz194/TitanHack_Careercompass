import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ExploreClient } from "@/app/explore/ExploreClient";
import type { ChatResponse, JourneyMode, Profile } from "@/types";

const { sendChat, resetSession, patchProfile } = vi.hoisted(() => ({
  sendChat: vi.fn(),
  resetSession: vi.fn(async () => "new-session"),
  patchProfile: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  IS_MOCK: false,
  sendChat,
  resetSession,
  patchProfile,
}));

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function profile(mode: JourneyMode): Profile {
  return {
    session_id: `session-${mode}`,
    journey_mode: mode,
    education_stage: null,
    job_goal: null,
    dimensions: { ky_thuat: 0, phan_tich: 0, sang_tao: 0, xa_hoi: 0, quan_ly: 0 },
    skills: [],
    interests: [],
    constraints: { region_pref: null, study_budget: null, study_duration_pref: null, notes: "" },
    evidence_quotes: [],
    experiences: [],
    completeness: 0,
  };
}

function opening(mode: JourneyMode, reply: string): ChatResponse {
  return { reply, phase: "warmup", turn: 1, done: false, profile: profile(mode) };
}

describe("ExploreClient request lifecycle", () => {
  beforeEach(() => {
    sendChat.mockReset();
    resetSession.mockClear();
    patchProfile.mockReset();
  });

  it("bỏ response cũ nếu user đổi journey trong lúc opening request còn chạy", async () => {
    const oldExplore = deferred<ChatResponse>();
    const newLaunch = deferred<ChatResponse>();
    sendChat
      .mockImplementationOnce(() => oldExplore.promise)
      .mockImplementationOnce(() => newLaunch.promise);

    render(<ExploreClient initialMode="explore" />);
    await waitFor(() => expect(sendChat).toHaveBeenCalledWith(null, "explore"));
    await userEvent.click(screen.getByRole("button", { name: "Tìm việc đầu tiên" }));
    await waitFor(() => expect(sendChat).toHaveBeenCalledWith(null, "launch"));

    await act(async () => {
      newLaunch.resolve(opening("launch", "LAUNCH mới nhất"));
      await newLaunch.promise;
    });
    expect(await screen.findByText("LAUNCH mới nhất")).toBeInTheDocument();

    await act(async () => {
      oldExplore.resolve(opening("explore", "EXPLORE đã lỗi thời"));
      await oldExplore.promise;
    });
    expect(screen.queryByText("EXPLORE đã lỗi thời")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Tìm việc đầu tiên" })).toHaveAttribute("aria-pressed", "true");
  });

  it("thoát trạng thái loading và cho retry nếu tạo session mới thất bại", async () => {
    resetSession.mockRejectedValueOnce(new Error("storage unavailable"));

    render(<ExploreClient initialMode="explore" freshStart />);

    expect(await screen.findByRole("button", { name: "Gửi lại" })).toBeInTheDocument();
    expect(sendChat).not.toHaveBeenCalled();
  });
});
