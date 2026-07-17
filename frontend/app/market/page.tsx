// Hiring-demand radar — task F2-04 (M6): Cải tiến giao diện vintage, hiển thị radar xu hướng vùng miền chi tiết.
"use client";

import { useEffect, useState } from "react";
import { fetchMarketOverview, fetchSkillGaps } from "@/lib/api";
import type { MarketOverview, Region, SkillGapResponse } from "@/types";

const REGIONS: { value: Region; label: string }[] = [
  { value: "all", label: "Toàn quốc" },
  { value: "hanoi", label: "Hà Nội" },
  { value: "hcm", label: "TP. Hồ Chí Minh" },
  { value: "danang", label: "Đà Nẵng" },
  { value: "other", label: "Vùng khác" },
];

export default function MarketPage() {
  const [region, setRegion] = useState<Region>("all");
  const [gaps, setGaps] = useState<SkillGapResponse | null>(null);
  const [overview, setOverview] = useState<MarketOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([fetchSkillGaps(region), fetchMarketOverview(region)])
      .then(([gapsData, overviewData]) => {
        setGaps(gapsData);
        setOverview(overviewData);
      })
      .catch((err) => {
        console.error(err);
        setError("Không thể tải thông tin thị trường tuyển dụng. Vui lòng thử lại sau.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [region]);

  const isMock = process.env.NEXT_PUBLIC_USE_MOCK === "1";

  return (
    <main className="mx-auto max-w-4xl min-h-screen p-6 space-y-6">
      {/* Menu đầu trang phong cách vintage */}
      <div className="flex justify-between items-center text-xs font-serif text-[var(--cc-muted)] border-b border-[var(--cc-border)]/40 pb-2.5">
        <a href="/" className="hover:text-[var(--cc-primary)] transition-all font-bold tracking-widest uppercase">
          🧭 CareerCompass
        </a>
        <div className="flex gap-3">
          <a href="/explore" className="hover:underline">Bắt đầu khảo sát</a>
          <span>·</span>
          <a href="/how-it-works" className="hover:underline">Cách hoạt động</a>
        </div>
      </div>

      {/* Header chính */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-[var(--cc-ink)] font-serif">
          🎯 Radar Nhu cầu Kỹ năng Tuyển dụng
        </h1>
        <p className="text-sm text-[var(--cc-muted)] leading-relaxed">
          Tín hiệu tổng hợp từ tin tuyển dụng được khảo sát trong 90 ngày gần nhất. Đây là dữ liệu thực tế đo lường <b>nhu cầu tuyển dụng quan sát được</b> (Hiring Demand Proxy), không phải kết luận tuyệt đối về sự thiếu hụt nhân lực trên thị trường.
        </p>
      </div>

      {/* Bộ lọc Vùng miền (Region Switcher) */}
      <div className="flex flex-wrap gap-2 py-2 border-y border-[var(--cc-border)]/50">
        {REGIONS.map((r) => (
          <button
            key={r.value}
            onClick={() => setRegion(r.value)}
            className={`rounded-full px-4.5 py-1.5 text-xs font-bold font-serif transition-all cursor-pointer border shadow-sm ${
              region === r.value
                ? "bg-[var(--cc-primary)] text-white border-[var(--cc-primary)]"
                : "border-[var(--cc-border)] bg-[var(--cc-card-bg)] text-[var(--cc-muted)] hover:text-[var(--cc-ink)] hover:bg-slate-50"
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      {/* Cảnh báo chế độ Demo */}
      {isMock && (
        <div className="rounded-lg bg-[var(--cc-accent-soft)] border border-[var(--cc-accent)]/45 p-3.5 text-xs text-[var(--cc-ink)] font-medium shadow-sm">
          <span><b>Chế độ Demo:</b> Đang hiển thị dữ liệu mô phỏng cho khu vực <b>{REGIONS.find((r) => r.value === region)?.label}</b>. Số liệu thật sẽ tự động nạp khi data pipeline của M3 hoàn tất.</span>
        </div>
      )}

      {loading ? (
        <div className="py-20 text-center space-y-3">
          <div className="inline-block w-8 h-8 rounded-full border-2 border-[var(--cc-border)] border-t-[var(--cc-primary)] animate-spin" />
          <p className="text-xs font-serif italic text-[var(--cc-muted)]">Đang lục tìm hồ sơ tuyển dụng tuyển chọn…</p>
        </div>
      ) : error ? (
        <div className="py-12 text-center space-y-2">
          <span className="text-3xl">📯</span>
          <p className="text-sm text-[var(--cc-danger)] font-medium">{error}</p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-[1.2fr_0.8fr]">
          
          {/* CỘT 1: Radar nhu cầu kỹ năng */}
          {gaps && (
            <section className="rounded-2xl border border-[var(--cc-border)] bg-[var(--cc-card-bg)] p-5 shadow-sm space-y-4">
              <div>
                <h2 className="text-lg font-bold font-serif text-[var(--cc-ink)]">Kỹ năng có nhu cầu tuyển dụng cao</h2>
                <p className="text-[10px] text-[var(--cc-muted)] italic mt-0.5">Xếp hạng theo điểm nhu cầu trích xuất (Gap Score)</p>
              </div>

              <div className="space-y-4">
                {gaps.skills.length > 0 ? (
                  gaps.skills.map((s, idx) => {
                    const hasTrend = s.trend_pct !== null && !s.low_confidence;
                    return (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between items-baseline text-xs">
                          <span className="font-semibold text-[var(--cc-ink)]">{s.skill}</span>
                          <span className="text-[10px] text-[var(--cc-muted)]">
                            {s.demand_count} tin tuyển dụng
                            {hasTrend && (
                              <span className={s.trend_pct! >= 0 ? " text-[var(--cc-success)] font-bold" : " text-[var(--cc-danger)] font-bold"}>
                                 · {s.trend_pct! >= 0 ? "▲" : "▼"}{Math.abs(s.trend_pct!)}%
                              </span>
                            )}
                          </span>
                        </div>
                        
                        {/* Thanh chỉ số nhu cầu */}
                        <div className="h-3 rounded-full bg-slate-100/80 border border-[var(--cc-border)]/40 overflow-hidden flex shadow-inner">
                          <div
                            className="h-full bg-[var(--cc-primary)] rounded-full transition-all duration-700"
                            style={{ width: `${s.gap_score * 100}%` }}
                          />
                        </div>

                        {s.low_confidence && (
                          <p className="text-[9px] text-amber-800/80 italic font-serif">⚠ Cỡ mẫu tin nhỏ — số liệu xu hướng có thể kém ổn định.</p>
                        )}
                      </div>
                    );
                  })
                ) : (
                  <p className="text-xs text-[var(--cc-muted)] italic font-serif text-center py-6">Chưa có dữ liệu kỹ năng cho khu vực này.</p>
                )}
              </div>

              <p className="text-[10px] text-[var(--cc-muted)] border-t border-[var(--cc-border)]/40 pt-3 italic font-serif">
                ℹ {gaps.source_note}
              </p>
            </section>
          )}

          {/* CỘT 2: Xu hướng ngành nghề */}
          <div className="space-y-6">
            {overview && (
              <>
                {/* Section: Nghề tăng trưởng */}
                <section className="rounded-2xl border border-[var(--cc-border)] bg-[var(--cc-card-bg)] p-5 shadow-sm space-y-4">
                  <div>
                    <h2 className="text-base font-bold font-serif text-[var(--cc-ink)]">Nghề đang tăng trưởng</h2>
                    <p className="text-[10px] text-[var(--cc-muted)] italic mt-0.5">Tốc độ tăng trưởng tin tuyển dụng 45 ngày qua</p>
                  </div>

                  <div className="space-y-2.5">
                    {overview.rising_careers.length > 0 ? (
                      overview.rising_careers.map((c, idx) => (
                        <div key={idx} className="flex justify-between items-center rounded-xl border border-[var(--cc-border)]/50 bg-white p-3 text-xs hover:border-[var(--cc-primary)] transition-all">
                          <span className="font-medium text-[var(--cc-ink)]">{c.title}</span>
                          <span className={`font-bold ${c.low_confidence || c.trend_pct == null ? "text-amber-800/80 italic text-[10px]" : "text-[var(--cc-success)]"}`}>
                            {c.low_confidence
                              ? "Độ tin cậy thấp"
                              : c.trend_pct == null
                                ? `${c.demand_count} tin (chưa đủ dữ liệu xu hướng)`
                                : `▲ ${c.trend_pct}%`}
                          </span>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-[var(--cc-muted)] italic font-serif text-center py-6">Không có dữ liệu xu hướng nghề nghiệp.</p>
                    )}
                  </div>
                </section>

                {/* Section: Nghề lương cao nhất */}
                <section className="rounded-2xl border border-[var(--cc-border)] bg-[var(--cc-card-bg)] p-5 shadow-sm space-y-4">
                  <div>
                    <h2 className="text-base font-bold font-serif text-[var(--cc-ink)]">Thu nhập trung vị nổi bật</h2>
                    <p className="text-[10px] text-[var(--cc-muted)] italic mt-0.5">Mức lương trung vị (Median) quan sát được</p>
                  </div>

                  <div className="space-y-2.5">
                    {overview.top_paying.length > 0 ? (
                      overview.top_paying.map((c, idx) => (
                        <div key={idx} className="flex justify-between items-center rounded-xl border border-[var(--cc-border)]/50 bg-white p-3 text-xs hover:border-[var(--cc-primary)] transition-all">
                          <span className="font-medium text-[var(--cc-ink)]">{c.title}</span>
                          <span className="font-bold text-[var(--cc-primary)] font-serif">
                            ~{c.salary_p50_trieu} triệu/tháng
                          </span>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-[var(--cc-muted)] italic font-serif text-center py-6">Chưa có thống kê mức lương.</p>
                    )}
                  </div>
                </section>
              </>
            )}
          </div>
        </div>
      )}

      {/* Footer ghi chú nguồn gốc dữ liệu */}
      {overview && (
        <div className="rounded-xl bg-[var(--cc-primary-soft)]/40 border border-[var(--cc-border)]/50 p-4 text-center text-[10px] text-[var(--cc-muted)] leading-relaxed font-serif shadow-sm">
          Tổng số postings khảo sát trong snapshot: <b>{overview.postings_count.toLocaleString("vi-VN")} tin</b> · Cửa sổ dữ liệu: <b>{overview.window_days} ngày</b> · Cập nhật gần nhất: <b>{overview.updated_at}</b>.
        </div>
      )}
    </main>
  );
}
