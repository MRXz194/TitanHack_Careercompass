// Orchestrator cho /explore (F1-01..06, F1-10): page điều phối, component render,
// network chỉ qua lib/api.ts. Logic trạng thái nằm trong lib/chat/machine (unit-tested).
"use client";

import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { ChatComposer } from "@/components/chat/ChatComposer";
import { ChatThread } from "@/components/chat/ChatThread";
import { ModeSelector } from "@/components/chat/ModeSelector";
import { ProfileEditor } from "@/components/profile/ProfileEditor";
import { ProfilePanel } from "@/components/profile/ProfilePanel";
import { patchProfile, sendChat } from "@/lib/api";
import {
  canChangeModeFreely, canSend, chatReducer, initialChatState,
} from "@/lib/chat/machine";
import { PHASE_PROGRESS, phaseStatus } from "@/lib/chat/status";
import { diffProfile } from "@/lib/profile/diff";
import { applyPatchLocal } from "@/lib/profile/apply";
import type { JourneyMode, Profile, ProfilePatch } from "@/types";

const MODE_STORAGE_KEY = "cc_journey_mode";

export function ExploreClient({ initialMode }: { initialMode: JourneyMode }) {
  const [state, dispatch] = useReducer(chatReducer, initialMode, initialChatState);
  const [patchError, setPatchError] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const prevProfileRef = useRef<Profile | null>(null);

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

  const open = useCallback((mode: JourneyMode) => {
    dispatch({ type: "OPEN" });
    sendChat(null, mode)
      .then((res) => dispatch({ type: "RECEIVE", res }))
      .catch(() => dispatch({ type: "FAIL" }));
  }, []);

  useEffect(() => {
    open(initialMode);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const send = (text: string) => {
    if (!canSend(state, text)) return;
    dispatch({ type: "SEND", text });
    sendChat(text, state.mode)
      .then((res) => dispatch({ type: "RECEIVE", res }))
      .catch(() => dispatch({ type: "FAIL" }));
  };

  const retry = () => {
    const text = state.lastUserText;
    dispatch({ type: "RETRY" });
    sendChat(text, state.mode)
      .then((res) => dispatch({ type: "RECEIVE", res }))
      .catch(() => dispatch({ type: "FAIL" }));
  };

  const changeMode = (mode: JourneyMode) => {
    dispatch({ type: "RESET_MODE", mode });
    open(mode);
  };

  // F1-04: optimistic patch + rollback khi API lỗi
  const applyPatch = async (patch: ProfilePatch) => {
    if (!state.profile) return;
    const prev = state.profile;
    setPatchError(false);
    dispatch({ type: "PROFILE_PATCHED", profile: applyPatchLocal(prev, patch) });
    try {
      const { profile } = await patchProfile(patch);
      dispatch({ type: "PROFILE_PATCHED", profile });
    } catch {
      dispatch({ type: "PROFILE_PATCHED", profile: prev });
      setPatchError(true);
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
        // onRemoveInterest cố ý không truyền: ProfilePatch chưa có remove_interests
        // (muốn thêm → quy trình đổi contract TEAM_RULES.md §2, không tự chế field)
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
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col p-4 md:p-6">
      <header className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-lg font-bold">🧭 CareerCompass</h1>
        <ModeSelector mode={state.mode} locked={!canChangeModeFreely(state)} onSelect={changeMode} />
      </header>

      <div className="grid min-h-0 flex-1 gap-6 md:grid-cols-[1fr_340px]">
        {/* Cột chat */}
        <section
          aria-label="Trò chuyện"
          className="flex min-h-[60vh] flex-col rounded-2xl border border-slate-200 bg-white shadow-sm"
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
              className="m-3 mt-0 rounded-xl bg-[var(--cc-success)] px-4 py-3 text-center font-semibold text-white shadow hover:opacity-90"
            >
              🎯 Xem hướng đi của bạn
            </a>
          )}
        </section>

        {/* Profile: cột phải desktop */}
        <aside
          aria-label="Hồ sơ của bạn"
          className="hidden h-fit rounded-2xl border border-slate-200 bg-white shadow-sm md:block"
        >
          {profileAside}
        </aside>
      </div>

      {/* Mobile: nút mở drawer hồ sơ */}
      <button
        onClick={() => setDrawerOpen(true)}
        className="fixed bottom-4 right-4 rounded-full bg-[var(--cc-primary)] px-4 py-2.5 text-sm font-semibold text-white shadow-lg md:hidden"
      >
        Hồ sơ {state.profile ? `· ${Math.round(state.profile.completeness * 100)}%` : ""}
      </button>
      {drawerOpen && (
        <div className="fixed inset-0 z-40 md:hidden" role="dialog" aria-label="Hồ sơ của bạn">
          <div className="absolute inset-0 bg-black/30" onClick={() => setDrawerOpen(false)} />
          <div className="absolute inset-y-0 right-0 w-[85%] max-w-sm overflow-y-auto bg-white shadow-xl">
            <div className="flex justify-end p-2">
              <button
                onClick={() => setDrawerOpen(false)}
                aria-label="Đóng hồ sơ"
                className="rounded-full px-3 py-1 text-lg text-[var(--cc-muted)]"
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
