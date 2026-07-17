// Màn kết quả — tasks F2-01..F2-03, F2-05 (M6). Skeleton render đủ shape contract từ mock.
"use client";

import { useEffect, useState } from "react";
import { fetchRecommendations } from "@/lib/api";
import type { Recommendation, RecommendationResponse } from "@/types";

const ROUTE_BADGE: Record<string, string> = {
  university: "🎓 Đại học",
  college: "🏫 Cao đẳng",
  vocational: "🔧 Học nghề",
  certificate: "📜 Chứng chỉ",
};

function CareerCard({ rec }: { rec: Recommendation }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      className={`rounded-2xl border bg-white p-5 shadow-sm ${
        rec.is_stretch ? "border-[var(--cc-accent)] ring-1 ring-[var(--cc-accent)]" : "border-slate-200"
      }`}
    >
      {rec.is_stretch && (
        <span className="mb-2 inline-block rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
          ✨ Có thể em chưa nghĩ tới
        </span>
      )}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">{rec.title}</h3>
        <span className="rounded-full bg-[var(--cc-primary-soft)] px-3 py-1 text-sm font-bold text-[var(--cc-primary)]">
          {Math.round(rec.match_score * 100)}% phù hợp
        </span>
      </div>
      <div className="mt-2 flex flex-wrap gap-3 text-sm text-[var(--cc-muted)]">
        <span>📈 {rec.market.demand_count_90d} tin tuyển/90 ngày</span>
        {rec.market.salary_p25_trieu != null && (
          <span>💰 {rec.market.salary_p25_trieu}–{rec.market.salary_p75_trieu} triệu</span>
        )}
        {rec.market.trend_pct != null && (
          <span className={rec.market.trend_pct >= 0 ? "text-[var(--cc-success)]" : "text-[var(--cc-danger)]"}>
            {rec.market.trend_pct >= 0 ? "▲" : "▼"} {Math.abs(rec.market.trend_pct)}%
          </span>
        )}
      </div>
      <button onClick={() => setOpen(!open)} className="mt-3 text-sm font-medium text-[var(--cc-primary)]">
        {open ? "Thu gọn ▲" : "Vì sao gợi ý này? + Lộ trình ▼"}
      </button>
      {open && (
        <div className="mt-3 space-y-4 border-t border-slate-100 pt-3 text-sm">
          <div>
            <h4 className="font-semibold">Từ chính em:</h4>
            {rec.why.from_you.map((w, i) => (
              <p key={i} className="mt-1">
                💬 <i>“{w.quote}”</i> — {w.reason}
              </p>
            ))}
          </div>
          <div>
            <h4 className="font-semibold">Từ thị trường:</h4>
            {rec.why.from_market.map((w, i) => (
              <p key={i} className="mt-1">📊 {w.stat}</p>
            ))}
            <p className="mt-1 text-xs text-[var(--cc-muted)]">{rec.market.source_note}</p>
          </div>
          <div>
            <h4 className="font-semibold">Lộ trình (chọn đường phù hợp với em):</h4>
            <div className="mt-2 grid gap-2 md:grid-cols-2">
              {rec.routes.map((r, i) => (
                <div key={i} className="rounded-xl border border-slate-200 p-3">
                  <span className="text-xs font-medium">{ROUTE_BADGE[r.type]}</span>
                  <p className="font-medium">{r.label}</p>
                  {r.first_steps.length > 0 && (
                    <ul className="mt-1 list-inside list-disc text-xs text-[var(--cc-muted)]">
                      {r.first_steps.map((s, j) => <li key={j}>{s}</li>)}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>
          <p className="rounded-xl bg-slate-50 p-3 text-xs">🔄 {rec.why.counterfactual}</p>
        </div>
      )}
    </div>
  );
}

export default function ResultsPage() {
  const [data, setData] = useState<RecommendationResponse | null>(null);

  useEffect(() => {
    fetchRecommendations().then(setData);
  }, []);

  if (!data)
    return <main className="p-10 text-center text-[var(--cc-muted)]">Đang tổng hợp hướng đi cho em…</main>;

  return (
    <main className="mx-auto max-w-3xl space-y-4 p-6">
      <h1 className="text-2xl font-bold">Các hướng đi dành cho em</h1>
      <p className="text-sm text-[var(--cc-muted)]">{data.disclaimer}</p>
      {data.recommendations.map((r) => <CareerCard key={r.career_id} rec={r} />)}
      <CareerCard rec={data.stretch} />
    </main>
  );
}
