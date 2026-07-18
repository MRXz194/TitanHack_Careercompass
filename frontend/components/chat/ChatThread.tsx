// F1-02/F1-10: luồng hội thoại — bubbles, typing indicator, lỗi + retry tiếng Việt,
// status line theo phase (copy cố định, không lộ reasoning), auto-scroll.
"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage } from "@/lib/chat/machine";

export function ChatThread({
  messages, pending, error, statusText, progress, onRetry,
}: {
  messages: ChatMessage[];
  pending: boolean;
  error: boolean;
  statusText: string | null;
  progress: number | null; // 0..1
  onRetry: () => void;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [messages.length, pending]);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {statusText && (
        <div className="border-b border-slate-100 px-4 py-2">
          <p className="text-xs text-[var(--cc-muted)]">{statusText}</p>
          {progress != null && (
            <div className="mt-1 h-1 bg-[var(--cc-fog)]">
              <div
                className="h-1 bg-[var(--cc-primary)] transition-all duration-500"
                style={{ width: `${Math.round(progress * 100)}%` }}
              />
            </div>
          )}
        </div>
      )}

      <div className="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[88%] whitespace-pre-wrap rounded-[2px] border px-4 py-2.5 text-[15px] leading-relaxed ${
              m.role === "ai"
                ? "border-[var(--cc-primary)]/20 bg-[var(--cc-primary-soft)]"
                : "ml-auto border-[var(--cc-border)] bg-[var(--cc-fog)]"
            }`}
          >
            {m.text}
          </div>
        ))}

        {pending && (
          <div className="flex w-fit items-center gap-1.5 rounded-[2px] border border-[var(--cc-primary)]/20 bg-[var(--cc-primary-soft)] px-4 py-3" aria-label="Đang trả lời">
            {[0, 150, 300].map((delay) => (
              <span
                key={delay}
                className="h-2 w-2 animate-bounce rounded-full bg-[var(--cc-primary)]/60"
                style={{ animationDelay: `${delay}ms` }}
              />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-[2px] border border-red-200 bg-red-50 p-3 text-sm">
            <p>Mạng chập chờn một chút, tin nhắn của bạn chưa gửi được.</p>
            <button
              onClick={onRetry}
              className="mt-2 rounded-[2px] bg-[var(--cc-primary)] px-3 py-1.5 font-mono text-xs font-medium uppercase text-white"
            >
              Gửi lại
            </button>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
