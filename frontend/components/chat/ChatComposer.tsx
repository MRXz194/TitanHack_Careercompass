// F1-02: ô nhập chat — Enter gửi, Shift+Enter xuống dòng, chặn rỗng và double-send.
"use client";

import { useState } from "react";

export function ChatComposer({
  disabled, onSend, placeholder = "Nhắn gì đó cho mình nhé…",
}: {
  disabled: boolean;
  onSend: (text: string) => void;
  placeholder?: string;
}) {
  const [text, setText] = useState("");

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    setText(""); // clear TRƯỚC khi gọi onSend → double-click không gửi lần 2
    onSend(trimmed);
  };

  return (
    <div className="flex min-w-0 items-end gap-2 border-t border-slate-200 p-3">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
        disabled={disabled}
        placeholder={placeholder}
        maxLength={2000}
        rows={1}
        aria-label="Tin nhắn của bạn"
        title="Tối đa 2.000 ký tự"
        className="max-h-32 min-w-0 flex-1 resize-none rounded-[2px] border border-[var(--cc-border)] bg-[var(--cc-paper)] px-4 py-2 outline-none focus:border-[var(--cc-primary)] disabled:bg-[var(--cc-fog)]"
      />
      <button
        onClick={submit}
        disabled={disabled || !text.trim()}
        className="shrink-0 rounded-[2px] bg-[var(--cc-primary)] px-4 py-2 font-mono text-xs font-medium uppercase text-white transition disabled:opacity-50"
      >
        Gửi
      </button>
    </div>
  );
}
