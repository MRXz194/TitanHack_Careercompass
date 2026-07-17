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
    <div className="flex items-end gap-2 border-t border-slate-200 p-3">
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
        rows={1}
        aria-label="Tin nhắn của bạn"
        className="max-h-32 flex-1 resize-none rounded-xl border border-slate-300 px-4 py-2 outline-none focus:border-[var(--cc-primary)] disabled:bg-slate-50"
      />
      <button
        onClick={submit}
        disabled={disabled || !text.trim()}
        className="rounded-xl bg-[var(--cc-primary)] px-5 py-2 font-medium text-white transition disabled:opacity-50"
      >
        Gửi
      </button>
    </div>
  );
}
