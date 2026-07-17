// F1-03 (Launch): trải nghiệm/bằng chứng — mỗi item hiện nguồn quote để minh bạch suy luận.
"use client";

import type { ExperienceEvidence, ExperienceKind } from "@/types";
import { RemovableChip } from "./RemovableChip";

const KIND_LABELS: Record<ExperienceKind, string> = {
  project: "Dự án",
  internship: "Thực tập",
  work: "Đi làm",
  volunteer: "Tình nguyện",
  coursework: "Bài tập môn học",
  other: "Khác",
};

export function ExperienceList({
  experiences, onRemove,
}: {
  experiences: ExperienceEvidence[];
  onRemove: (title: string) => void;
}) {
  if (experiences.length === 0) {
    return <p className="text-xs text-[var(--cc-muted)]">Chưa có trải nghiệm nào — kể mình nghe project/việc bạn từng làm nhé.</p>;
  }
  return (
    <ul className="space-y-2">
      {experiences.map((e) => (
        <li key={e.title} className="rounded-xl border border-slate-200 p-2.5">
          <div className="flex items-start justify-between gap-2">
            <div>
              <span className="mr-2 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-[var(--cc-muted)]">
                {KIND_LABELS[e.kind]}
              </span>
              <span className="text-sm font-medium">{e.title}</span>
            </div>
            <RemovableChip
              label={e.title}
              removeAriaLabel={`Xóa trải nghiệm ${e.title}`}
              confirmAriaLabel={`Xác nhận xóa ${e.title}`}
              onConfirm={() => onRemove(e.title)}
              iconOnly
            />
          </div>
          {e.skills.length > 0 && (
            <p className="mt-1 text-xs text-[var(--cc-muted)]">Kỹ năng: {e.skills.join(", ")}</p>
          )}
          {e.source_quote && (
            <p className="mt-1 text-xs italic text-[var(--cc-muted)]">vì bạn nói: “{e.source_quote}”</p>
          )}
        </li>
      ))}
    </ul>
  );
}
