// F1-04 (Launch): form sửa giai đoạn học + mục tiêu việc làm — patch chỉ gửi khi có thay đổi.
"use client";

import { useState } from "react";
import type { EducationStage, ProfilePatch } from "@/types";
import { STAGE_LABELS } from "./ProfilePanel";

export function ProfileEditor({
  educationStage, jobGoal, onPatch,
}: {
  educationStage: EducationStage | null;
  jobGoal: string | null;
  onPatch: (patch: ProfilePatch) => void;
}) {
  const [stage, setStage] = useState<EducationStage | "">(educationStage ?? "");
  const [goal, setGoal] = useState(jobGoal ?? "");

  const nextStage = stage === "" ? null : stage;
  const nextGoal = goal.trim() === "" ? null : goal.trim();
  const dirty = nextStage !== educationStage || nextGoal !== jobGoal;

  return (
    <div className="space-y-2 rounded-xl border border-slate-200 p-3">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--cc-muted)]">Chỉnh thông tin của bạn</h3>
      <label className="block text-xs">
        Giai đoạn hiện tại
        <select
          value={stage}
          onChange={(e) => setStage(e.target.value as EducationStage | "")}
          className="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
        >
          <option value="">— Chưa chọn —</option>
          {(Object.entries(STAGE_LABELS) as [EducationStage, string][]).map(([v, label]) => (
            <option key={v} value={v}>{label}</option>
          ))}
        </select>
      </label>
      <label className="block text-xs">
        Mục tiêu việc làm
        <input
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="VD: thực tập phân tích dữ liệu"
          className="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
        />
      </label>
      <button
        disabled={!dirty}
        onClick={() => onPatch({ education_stage: nextStage, job_goal: nextGoal })}
        className="rounded-lg bg-[var(--cc-primary)] px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-40"
      >
        Lưu
      </button>
    </div>
  );
}
