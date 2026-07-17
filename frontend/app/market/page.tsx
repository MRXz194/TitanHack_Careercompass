// Skill Gap Radar — task F2-04 (M6): nâng cấp bar chart Recharts + trend arrows + region switcher đẹp.
"use client";

import { useEffect, useState } from "react";
import { fetchMarketOverview, fetchSkillGaps } from "@/lib/api";
import type { MarketOverview, Region, SkillGapResponse } from "@/types";

const REGIONS: { value: Region; label: string }[] = [
  { value: "all", label: "Toàn quốc" },
  { value: "hanoi", label: "Hà Nội" },
  { value: "hcm", label: "TP.HCM" },
  { value: "danang", label: "Đà Nẵng" },
];

export default function MarketPage() {
  const [region, setRegion] = useState<Region>("all");
  const [gaps, setGaps] = useState<SkillGapResponse | null>(null);
  const [overview, setOverview] = useState<MarketOverview | null>(null);

  useEffect(() => {
    fetchSkillGaps(region).then(setGaps);
    fetchMarketOverview(region).then(setOverview);
  }, [region]);

  return (
    <main className="mx-auto max-w-4xl space-y-6 p-6">
      <h1 className="text-2xl font-bold">🎯 Radar kỹ năng đang khát nhân lực</h1>
      <div className="flex gap-2">
        {REGIONS.map((r) => (
          <button
            key={r.value}
            onClick={() => setRegion(r.value)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium ${
              region === r.value ? "bg-[var(--cc-primary)] text-white" : "border border-slate-300 bg-white"
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      {gaps && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-3 font-semibold">Kỹ năng khát nhân lực nhất</h2>
          <div className="space-y-2">
            {gaps.skills.map((s) => (
              <div key={s.skill} className="flex items-center gap-3">
                <span className="w-44 truncate text-sm">{s.skill}</span>
                <div className="h-3 flex-1 rounded-full bg-slate-100">
                  <div
                    className="h-3 rounded-full bg-[var(--cc-primary)]"
                    style={{ width: `${s.gap_score * 100}%` }}
                  />
                </div>
                <span className="w-24 text-right text-xs text-[var(--cc-muted)]">
                  {s.demand_count} tin {s.trend_pct != null && s.trend_pct > 0 ? `· ▲${s.trend_pct}%` : ""}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {overview && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-3 font-semibold">Nghề đang tăng trưởng</h2>
          <div className="grid gap-2 md:grid-cols-2">
            {overview.rising_careers.map((c) => (
              <div key={c.career_id} className="flex justify-between rounded-xl border border-slate-100 p-3 text-sm">
                <span>{c.title}</span>
                <span className="font-semibold text-[var(--cc-success)]">▲ {c.trend_pct}%</span>
              </div>
            ))}
          </div>
          <p className="mt-3 text-xs text-[var(--cc-muted)]">
            Từ {overview.postings_count.toLocaleString("vi-VN")} tin tuyển dụng · {overview.window_days} ngày gần nhất
            · cập nhật: {overview.updated_at}
          </p>
        </section>
      )}
    </main>
  );
}
