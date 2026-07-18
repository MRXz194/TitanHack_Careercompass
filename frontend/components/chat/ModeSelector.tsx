// F1-01: chọn hành trình explore|launch. Sau khi user đã trả lời (locked), đổi mode
// phải xác nhận reset ngay trong component — không dùng window.confirm.
"use client";

import { useState } from "react";
import type { JourneyMode } from "@/types";

const MODES: { value: JourneyMode; label: string; hint: string }[] = [
  { value: "explore", label: "Khám phá nghề", hint: "Dành cho bạn đang tìm hướng đi" },
  { value: "launch", label: "Tìm việc đầu tiên", hint: "Dành cho bạn sắp/mới tốt nghiệp" },
];

export function ModeSelector({
  mode, locked, onSelect,
}: {
  mode: JourneyMode;
  locked: boolean;
  onSelect: (mode: JourneyMode) => void;
}) {
  const [confirming, setConfirming] = useState<JourneyMode | null>(null);

  const pick = (next: JourneyMode) => {
    if (next === mode) return;
    if (!locked) return onSelect(next);
    setConfirming(next);
  };

  return (
    <div>
      <div role="group" aria-label="Chọn hành trình" className="flex gap-2">
        {MODES.map((m) => (
          <button
            key={m.value}
            aria-pressed={m.value === mode}
            onClick={() => pick(m.value)}
            title={m.hint}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
              m.value === mode
                ? "bg-[var(--cc-primary)] text-white shadow"
                : "border border-slate-300 bg-white hover:border-[var(--cc-primary)]"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {confirming && (
        <div className="mt-2 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm">
          <p>Đổi chế độ sẽ <b>bắt đầu lại</b> cuộc trò chuyện từ đầu. Bạn chắc chứ?</p>
          <div className="mt-2 flex gap-2">
            <button
              onClick={() => { const next = confirming; setConfirming(null); onSelect(next); }}
              className="rounded-lg bg-[var(--cc-primary)] px-3 py-1.5 text-xs font-semibold text-white"
            >
              Đổi và bắt đầu lại
            </button>
            <button
              onClick={() => setConfirming(null)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium"
            >
              Ở lại
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
