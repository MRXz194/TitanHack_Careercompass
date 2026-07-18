// Orchestrator cho /explore (F1-01..06, F1-10): page điều phối, component render,
// network chỉ qua lib/api.ts. Logic trạng thái nằm trong lib/chat/machine (unit-tested).
"use client";

import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { ChatComposer } from "@/components/chat/ChatComposer";
import { ChatThread } from "@/components/chat/ChatThread";
import { ModeSelector } from "@/components/chat/ModeSelector";
import { ProfileEditor } from "@/components/profile/ProfileEditor";
import { ProfilePanel } from "@/components/profile/ProfilePanel";
import { IS_MOCK, patchProfile, resetSession, sendChat } from "@/lib/api";
import {
  canChangeModeFreely, canSend, chatReducer, initialChatState,
} from "@/lib/chat/machine";
import { PHASE_PROGRESS, phaseStatus } from "@/lib/chat/status";
import { diffProfile } from "@/lib/profile/diff";
import { applyPatchLocal } from "@/lib/profile/apply";
import type { JourneyMode, Profile, ProfilePatch } from "@/types";

const MODE_STORAGE_KEY = "cc_journey_mode";

export function ExploreClient({
  initialMode,
  freshStart = false,
}: {
  initialMode: JourneyMode;
  freshStart?: boolean;
}) {
  const [state, dispatch] = useReducer(chatReducer, initialMode, initialChatState);
  const [patchError, setPatchError] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [confirmRestart, setConfirmRestart] = useState(false);
  const prevProfileRef = useRef<Profile | null>(null);
  const journeyEpochRef = useRef(0);
  const chatRequestRef = useRef(0);

  // Diff để highlight phần vừa cập nhật (F1-03)
  const diff = useMemo(() => {
    if (!state.profile) return null;
    const d = diffProfile(prevProfileRef.current, state.profile);
    return d;
  }, [state.profile]);
  useEffect(() => {
    prevProfileRef.current = state.profile;
  }, [state.profile]);

  // Giữ mode cho /results (F1-06) — không truyền data qua query string
  useEffect(() => {
    localStorage.setItem(MODE_STORAGE_KEY, state.mode);
  }, [state.mode]);

  const open = useCallback(async (mode: JourneyMode, startClean = false) => {
    const journeyEpoch = ++journeyEpochRef.current;
    const requestId = ++chatRequestRef.current;
    dispatch({ type: "OPEN" });
    try {
      if (startClean) await resetSession();
      if (journeyEpoch !== journeyEpochRef.current) return;
      const res = await sendChat(null, mode);
      if (journeyEpoch === journeyEpochRef.current && requestId === chatRequestRef.current) {
        dispatch({ type: "RECEIVE", res });
      }
    } catch {
      if (journeyEpoch === journeyEpochRef.current && requestId === chatRequestRef.current) {
        dispatch({ type: "FAIL" });
      }
    }
  }, []);

  useEffect(() => {
    void open(initialMode, freshStart);
    if (freshStart && typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.delete("new");
      window.history.replaceState({}, "", `${url.pathname}${url.search}`);
    }
    return () => {
      journeyEpochRef.current += 1;
      chatRequestRef.current += 1;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const send = async (text: string) => {
    if (!canSend(state, text)) return;
    const journeyEpoch = journeyEpochRef.current;
    const requestId = ++chatRequestRef.current;
    dispatch({ type: "SEND", text });
    try {
      const res = await sendChat(text, state.mode);
      if (journeyEpoch === journeyEpochRef.current && requestId === chatRequestRef.current) {
        dispatch({ type: "RECEIVE", res });
      }
    } catch {
      if (journeyEpoch === journeyEpochRef.current && requestId === chatRequestRef.current) {
        dispatch({ type: "FAIL" });
      }
    }
  };

  const retry = async () => {
    const text = state.lastUserText;
    const journeyEpoch = journeyEpochRef.current;
    const requestId = ++chatRequestRef.current;
    dispatch({ type: "RETRY" });
    try {
      const res = await sendChat(text, state.mode);
      if (journeyEpoch === journeyEpochRef.current && requestId === chatRequestRef.current) {
        dispatch({ type: "RECEIVE", res });
      }
    } catch {
      if (journeyEpoch === journeyEpochRef.current && requestId === chatRequestRef.current) {
        dispatch({ type: "FAIL" });
      }
    }
  };

  const changeMode = (mode: JourneyMode) => {
    dispatch({ type: "RESET_MODE", mode });
    void open(mode, true);
  };

  const restart = () => {
    setConfirmRestart(false);
    dispatch({ type: "RESET_MODE", mode: state.mode });
    void open(state.mode, true);
  };

  // F1-04: optimistic patch + rollback khi API lỗi
  const applyPatch = async (patch: ProfilePatch) => {
    if (!state.profile) return;
    const journeyEpoch = journeyEpochRef.current;
    const prev = state.profile;
    setPatchError(false);
    dispatch({ type: "PROFILE_PATCHED", profile: applyPatchLocal(prev, patch) });
    try {
      const { profile } = await patchProfile(patch);
      if (journeyEpoch === journeyEpochRef.current) {
        dispatch({ type: "PROFILE_PATCHED", profile });
      }
    } catch {
      if (journeyEpoch === journeyEpochRef.current) {
        dispatch({ type: "PROFILE_PATCHED", profile: prev });
        setPatchError(true);
      }
    }
  };

  const statusText = state.done
    ? "Hồ sơ đã đủ để gợi ý — bạn xem lại rồi bấm nút bên dưới nhé"
    : state.phase
      ? phaseStatus(state.phase, state.mode)
      : null;
  const progress = state.done ? 1 : state.phase ? PHASE_PROGRESS[state.phase] : null;

  const profileAside = (
    <>
      <ProfilePanel
        profile={state.profile}
        diff={diff}
        onRemoveSkill={(name) => applyPatch({ remove_skills: [name] })}
        onRemoveInterest={(name) => applyPatch({ remove_interests: [name] })}
        onRemoveExperience={(title) => applyPatch({ remove_experience_titles: [title] })}
      />
      {state.mode === "launch" && state.profile && (
        <div className="px-4 pb-4">
          <ProfileEditor
            educationStage={state.profile.education_stage}
            jobGoal={state.profile.job_goal}
            onPatch={applyPatch}
          />
        </div>
      )}
      {patchError && (
        <p className="px-4 pb-3 text-xs text-red-600">
          Chưa lưu được thay đổi — hồ sơ đã khôi phục như cũ, bạn thử lại nhé.
        </p>
      )}
    </>
  );

  return (
    <main className="mx-auto flex min-h-screen w-full min-w-0 max-w-6xl flex-col overflow-x-hidden p-4 md:p-6">
      <header className="mb-4 flex flex-col gap-3 border-b border-[var(--cc-border)] pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-bold">CareerCompass</h1>
          {IS_MOCK && (
            <span className="border border-[var(--cc-accent)] px-2 py-0.5 text-[10px] font-medium text-[var(--cc-ink)]">
              DEMO MẪU · KHÔNG PHẢI AI LIVE
            </span>
          )}
        </div>
        <div className="flex w-full min-w-0 flex-col items-stretch gap-2 sm:w-auto sm:items-end">
          <ModeSelector mode={state.mode} locked={!canChangeModeFreely(state)} onSelect={changeMode} />
          <div className="flex flex-wrap justify-between gap-3 sm:justify-end">
            <button
              type="button"
              className="text-[10px] uppercase text-[var(--cc-muted)] underline underline-offset-4"
              onClick={() => setConfirmRestart(true)}
            >
              Bắt đầu hồ sơ mới
            </button>
            <button
              type="button"
              className="text-[10px] uppercase text-[var(--cc-primary)] underline underline-offset-4 md:hidden"
              onClick={() => setDrawerOpen(true)}
            >
              Hồ sơ {state.profile ? `· ${Math.round(state.profile.completeness * 100)}%` : ""}
            </button>
          </div>
        </div>
      </header>

      {confirmRestart && (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border border-[var(--cc-border)] bg-[var(--cc-fog)] p-3 text-sm" role="alertdialog" aria-label="Xác nhận bắt đầu hồ sơ mới">
          <p>Hồ sơ hiện tại sẽ được thay bằng một phiên mới. Bạn muốn tiếp tục chứ?</p>
          <div className="flex gap-2">
            <button type="button" className="cc-button-dark" onClick={restart}>BẮT ĐẦU MỚI</button>
            <button type="button" className="cc-button-ghost" onClick={() => setConfirmRestart(false)}>GIỮ HỒ SƠ</button>
          </div>
        </div>
      )}

      <div className="grid min-h-0 min-w-0 flex-1 gap-6 md:grid-cols-[minmax(0,1fr)_340px]">
        {/* Cột chat */}
        <section
          aria-label="Trò chuyện"
          className="flex min-h-[min(560px,calc(100dvh-210px))] min-w-0 flex-col rounded-[2px] border border-[var(--cc-border)] bg-[var(--cc-card-bg)]"
        >
          <ChatThread
            messages={state.messages}
            pending={state.pending}
            error={state.error}
            statusText={statusText}
            progress={progress}
            onRetry={retry}
          />
          <ChatComposer disabled={state.pending || state.done || state.error} onSend={send} />
          {state.done && (
            <a
              href="/results"
              className="m-3 mt-0 rounded-[2px] bg-[var(--cc-success)] px-4 py-3 text-center font-mono text-xs font-medium uppercase tracking-wide text-white hover:opacity-90"
            >
              Xem hướng đi của bạn
            </a>
          )}
        </section>

        {/* Profile: cột phải desktop */}
        <aside
          aria-label="Hồ sơ của bạn"
          className="hidden h-fit rounded-[2px] border border-[var(--cc-border)] bg-[var(--cc-card-bg)] md:block"
        >
          {profileAside}
        </aside>
      </div>

      {/* Mobile: drawer mở từ nút trong header, không che composer. */}
      {drawerOpen && (
        <div className="fixed inset-0 z-40 md:hidden" role="dialog" aria-label="Hồ sơ của bạn">
          <div className="absolute inset-0 bg-black/30" onClick={() => setDrawerOpen(false)} />
          <div className="absolute inset-y-0 right-0 w-[88%] max-w-sm overflow-y-auto border-l border-[var(--cc-border)] bg-[var(--cc-paper)]">
            <div className="flex justify-end p-2">
              <button
                onClick={() => setDrawerOpen(false)}
                aria-label="Đóng hồ sơ"
                className="rounded-[2px] px-3 py-1 text-lg text-[var(--cc-muted)]"
              >
                ✕
              </button>
            </div>
            {profileAside}
          </div>
        </div>
      )}
    </main>
  );
}
