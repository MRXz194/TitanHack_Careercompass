// F1-04: nút xóa 2 bước (bấm × → hiện "Xóa?" → bấm lần nữa mới xóa) — không dùng window.confirm.
"use client";

import { useState } from "react";

export function RemovableChip({
  label, removeAriaLabel, confirmAriaLabel, onConfirm, iconOnly = false,
}: {
  label: string;
  removeAriaLabel: string;
  confirmAriaLabel: string;
  onConfirm: () => void;
  iconOnly?: boolean;
}) {
  const [confirming, setConfirming] = useState(false);

  if (confirming) {
    return (
      <span className="inline-flex items-center gap-1">
        <button
          aria-label={confirmAriaLabel}
          onClick={() => { setConfirming(false); onConfirm(); }}
          className="rounded-full bg-red-600 px-2 py-0.5 text-[10px] font-semibold text-white"
        >
          Xóa?
        </button>
        <button
          aria-label="Hủy xóa"
          onClick={() => setConfirming(false)}
          className="text-xs text-[var(--cc-muted)] underline"
        >
          hủy
        </button>
      </span>
    );
  }

  return (
    <button
      aria-label={removeAriaLabel}
      onClick={() => setConfirming(true)}
      title="Em không nghĩ vậy — xóa mục này"
      className="text-[var(--cc-muted)] transition hover:text-red-600"
    >
      {iconOnly ? "✕" : `✕ ${label}`}
    </button>
  );
}
