// F1-03/F1-04: Profile Card live — 5 chiều + highlight "vừa cập nhật", skill kèm quote gốc,
// constraints trung thực, Launch: mục tiêu việc làm + giai đoạn + experiences. Sửa/xóa được (autonomy).
"use client";

import type { ProfileDiff } from "@/lib/profile/diff";
import type { EducationStage, Profile } from "@/types";
import { ExperienceList } from "./ExperienceList";
import { RemovableChip } from "./RemovableChip";

export const DIM_LABELS: Record<string, string> = {
  ky_thuat: "Thực hành – kỹ thuật",
  phan_tich: "Phân tích – logic",
  sang_tao: "Sáng tạo – nghệ thuật",
  xa_hoi: "Con người – xã hội",
  quan_ly: "Tổ chức – kinh doanh",
};

export const STAGE_LABELS: Record<EducationStage, string> = {
  high_school: "Học sinh THPT",
  vocational_student: "Học viên trường nghề",
  college_student: "Sinh viên cao đẳng",
  university_student: "Sinh viên đại học",
  final_year: "Sinh viên năm cuối",
  recent_graduate: "Mới tốt nghiệp",
  other: "Khác",
};

const REGION_LABELS: Record<string, string> = {
  hanoi: "Hà Nội", hcm: "TP.HCM", danang: "Đà Nẵng", other: "Nơi khác",
};

export function ProfilePanel({
  profile, diff, onRemoveSkill, onRemoveInterest, onRemoveExperience,
}: {
  profile: Profile | null;
  diff: ProfileDiff | null;
  onRemoveSkill: (name: string) => void;
  /** Optional for read-only contexts; Explore wires this to the autonomy PATCH. */
  onRemoveInterest?: (name: string) => void;
  onRemoveExperience: (title: string) => void;
}) {
  if (!profile) {
    return (
      <div className="p-4">
        <h2 className="mb-2 font-semibold">Hồ sơ của bạn</h2>
        <p className="text-sm text-[var(--cc-muted)]">Trò chuyện để hồ sơ hiện dần ở đây — bạn xem được và sửa được mọi thứ.</p>
      </div>
    );
  }

  const isLaunch = profile.journey_mode === "launch";
  const c = profile.constraints;
  const hasConstraints = c.region_pref || c.study_budget || c.study_duration_pref || c.notes;

  return (
    <div className="space-y-4 p-4">
      <div>
        <div className="flex items-baseline justify-between">
          <h2 className="font-semibold">Hồ sơ của bạn</h2>
          <span className="text-xs text-[var(--cc-muted)]">{Math.round(profile.completeness * 100)}% hoàn thiện</span>
        </div>
        <div className="mt-1 h-1.5 rounded-full bg-slate-100">
          <div
            className="h-1.5 rounded-full bg-[var(--cc-success)] transition-all duration-700"
            style={{ width: `${profile.completeness * 100}%` }}
          />
        </div>
      </div>

      {/* 5 chiều năng lực-sở thích */}
      <section aria-label="Chiều năng lực và sở thích" className="space-y-2.5">
        <p className="text-[10px] text-[var(--cc-muted)]">
          Tín hiệu tương đối từ điều bạn đã kể, không phải điểm kiểm tra cố định.
        </p>
        {Object.entries(profile.dimensions).map(([key, value]) => {
          const highlighted = diff?.changedDimensions.includes(key) ?? false;
          return (
            <div
              key={key}
              data-testid={`dim-${key}`}
              data-highlight={highlighted ? "true" : "false"}
              className={`rounded-lg px-2 py-1 transition-colors duration-1000 ${highlighted ? "bg-amber-50" : ""}`}
            >
              <div className="flex justify-between text-sm">
                <span>{DIM_LABELS[key] ?? key}</span>
                <span className="text-[var(--cc-muted)]">{Math.round(value * 100)}%</span>
              </div>
              <div className="mt-1 h-2 rounded-full bg-slate-100">
                <div
                  className="h-2 rounded-full bg-[var(--cc-primary)] transition-all duration-700"
                  style={{ width: `${value * 100}%` }}
                />
              </div>
            </div>
          );
        })}
      </section>

      {/* Launch: mục tiêu + giai đoạn */}
      {isLaunch && (
        <section className="rounded-xl bg-slate-50 p-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--cc-muted)]">Mục tiêu việc làm</h3>
          <p className="mt-1 text-sm">{profile.job_goal ?? "Chưa rõ — mình sẽ cùng làm rõ nhé"}</p>
          {profile.education_stage && (
            <p className="mt-1 text-xs text-[var(--cc-muted)]">Giai đoạn: {STAGE_LABELS[profile.education_stage]}</p>
          )}
        </section>
      )}

      {/* Kỹ năng — luôn kèm quote gốc để minh bạch */}
      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--cc-muted)]">Kỹ năng</h3>
        {profile.skills.length === 0 ? (
          <p className="mt-1 text-xs text-[var(--cc-muted)]">Chưa ghi nhận kỹ năng nào.</p>
        ) : (
          <ul className="mt-1.5 space-y-1.5">
            {profile.skills.map((s) => (
              <li
                key={s.name}
                className={`rounded-lg px-2 py-1 ${diff?.addedSkills.includes(s.name) ? "bg-amber-50" : ""}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium">{s.name}</span>
                  <RemovableChip
                    label={s.name}
                    removeAriaLabel={`Xóa kỹ năng ${s.name}`}
                    confirmAriaLabel={`Xác nhận xóa ${s.name}`}
                    onConfirm={() => onRemoveSkill(s.name)}
                    iconOnly
                  />
                </div>
                {s.level && <span className="text-xs text-[var(--cc-muted)]">{s.level}</span>}
                {s.source_quote && (
                  <p className="text-xs italic text-[var(--cc-muted)]">vì bạn nói: “{s.source_quote}”</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Sở thích */}
      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--cc-muted)]">Điều bạn thích</h3>
        {profile.interests.length === 0 ? (
          <p className="mt-1 text-xs text-[var(--cc-muted)]">Chưa ghi nhận sở thích nào.</p>
        ) : (
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {profile.interests.map((it) => (
              <span
                key={it}
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs ${
                  diff?.addedInterests.includes(it) ? "bg-amber-100" : "bg-[var(--cc-primary-soft)]"
                }`}
              >
                {it}
                {onRemoveInterest && (
                  <RemovableChip
                    label={it}
                    removeAriaLabel={`Xóa sở thích ${it}`}
                    confirmAriaLabel={`Xác nhận xóa ${it}`}
                    onConfirm={() => onRemoveInterest(it)}
                    iconOnly
                  />
                )}
              </span>
            ))}
          </div>
        )}
      </section>

      {/* Launch: trải nghiệm/bằng chứng */}
      {isLaunch && (
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--cc-muted)]">Trải nghiệm của bạn</h3>
          <div className="mt-1.5">
            <ExperienceList experiences={profile.experiences} onRemove={onRemoveExperience} />
          </div>
        </section>
      )}

      {/* Điều kiện */}
      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--cc-muted)]">Điều kiện của bạn</h3>
        {!hasConstraints ? (
          <p className="mt-1 text-xs text-[var(--cc-muted)]">Chưa có thông tin — cứ chia sẻ khi bạn thấy thoải mái nhé.</p>
        ) : (
          <ul className="mt-1 space-y-0.5 text-xs text-[var(--cc-ink)]">
          {c.region_pref && <li>Ưu tiên khu vực: {REGION_LABELS[c.region_pref] ?? c.region_pref}</li>}
            {c.study_budget && <li>💰 Tài chính: {c.study_budget}</li>}
            {c.study_duration_pref && <li>⏱ Thời gian học: {c.study_duration_pref}</li>}
            {c.notes && <li>📝 {c.notes}</li>}
          </ul>
        )}
      </section>

      <p className="border-t border-slate-100 pt-2 text-xs text-[var(--cc-muted)]">
        Hồ sơ này là của bạn — sai chỗ nào bạn cứ xóa/sửa, gợi ý sẽ đổi theo.
      </p>
    </div>
  );
}
