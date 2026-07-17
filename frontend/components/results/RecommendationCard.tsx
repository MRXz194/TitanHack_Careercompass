"use client";

import { useState } from "react";
import type { Recommendation } from "@/types";

const ROUTE_BADGE: Record<string, string> = {
  university: "🎓 Đại học",
  college: "🏫 Cao đẳng",
  vocational: "🔧 Học nghề",
  certificate: "📜 Chứng chỉ",
};

interface RecommendationCardProps {
  rec: Recommendation;
  rank?: number;
}

export default function RecommendationCard({ rec, rank }: RecommendationCardProps) {
  const [open, setOpen] = useState(false);
  const { market, why, routes, job_readiness, is_stretch } = rec;

  // Cấu hình xu hướng tuyển dụng
  const showTrend = market.trend_pct !== null && !market.low_confidence;
  const trendVal = market.trend_pct ?? 0;

  return (
    <div
      className={`rounded-2xl border p-6 transition-all duration-300 bg-[var(--cc-card-bg)] shadow-sm ${
        is_stretch
          ? "border-[var(--cc-accent)] ring-1 ring-[var(--cc-accent)]/30 hover:shadow-md"
          : "border-[var(--cc-border)] hover:border-[var(--cc-primary)] hover:shadow-md"
      }`}
    >
      {is_stretch && (
        <span className="mb-3.5 inline-flex items-center gap-1.5 rounded-full bg-[var(--cc-accent-soft)] border border-[var(--cc-accent)] px-3 py-1 text-xs font-semibold text-[var(--cc-accent)] font-serif shadow-sm">
          ✨ Hướng đi gợi mở (Stretch Recommendation)
        </span>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2.5 flex-wrap">
            {rank && !is_stretch && (
              <span className="text-xs font-serif font-bold text-[var(--cc-muted)] bg-[var(--cc-primary-soft)] rounded-md px-2 py-0.5 border border-[var(--cc-border)]">
                #{rank}
              </span>
            )}
            <h3 className="text-xl font-bold tracking-tight text-[var(--cc-ink)] font-serif">{rec.title}</h3>
          </div>
          <p className="text-xs text-[var(--cc-muted)]">
            Mã nghề: <code className="font-mono bg-[var(--cc-primary-soft)] px-1.5 py-0.5 rounded text-[var(--cc-primary)] border border-[var(--cc-border)]/40">{rec.career_id}</code>
          </p>
        </div>

        <div className="flex flex-col sm:items-end shrink-0">
          <span className="rounded-full bg-[var(--cc-primary-soft)] border border-[var(--cc-primary)]/10 px-4 py-1.5 text-xs sm:text-sm font-bold text-[var(--cc-primary)] shadow-sm font-serif">
            {Math.round(rec.match_score * 100)}% mức tương thích tham khảo
          </span>
        </div>
      </div>

      {/* Danh sách nhãn chỉ số thị trường (Market Badges) */}
      <div className="mt-4 flex flex-wrap gap-2.5 text-xs text-[var(--cc-muted)] border-t border-[var(--cc-border)]/60 pt-3.5">
        <span className="flex items-center gap-1 bg-[var(--cc-primary-soft)]/40 px-2.5 py-1 rounded-md border border-[var(--cc-border)]/50">
          📈 {market.demand_count_90d.toLocaleString("vi-VN")} tin tuyển dụng/90 ngày
        </span>

        {market.salary_p25_trieu !== null && market.salary_p75_trieu !== null ? (
          <span className="flex items-center gap-1 bg-[var(--cc-primary-soft)]/40 px-2.5 py-1 rounded-md border border-[var(--cc-border)]/50">
            💰 Lương phổ biến: {market.salary_p25_trieu}–{market.salary_p75_trieu} triệu/tháng
          </span>
        ) : (
          <span className="flex items-center gap-1 bg-amber-50/50 text-amber-800/80 px-2.5 py-1 rounded-md border border-amber-200/40">
            💰 Lương: Số liệu có hạn chế
          </span>
        )}

        {showTrend ? (
          <span
            className={`flex items-center gap-1 px-2.5 py-1 rounded-md border ${
              trendVal >= 0
                ? "bg-green-50/40 text-[var(--cc-success)] border-green-200/40 animate-pulse"
                : "bg-red-50/40 text-[var(--cc-danger)] border-red-200/40"
            }`}
          >
            {trendVal >= 0 ? "▲" : "▼"} {Math.abs(trendVal)}% xu hướng tuyển dụng
          </span>
        ) : (
          market.low_confidence && (
            <span className="flex items-center gap-1 bg-amber-50/50 text-amber-800/80 px-2.5 py-1 rounded-md border border-amber-200/40">
              📊 Dữ liệu xu hướng có hạn chế
            </span>
          )
        )}
      </div>

      <div className="mt-4 flex justify-between items-center flex-wrap gap-2">
        <span className="text-[10px] text-[var(--cc-muted)] italic font-serif">
          {market.source_note}
        </span>
        <button
          onClick={() => setOpen(!open)}
          className="inline-flex items-center gap-1 text-xs font-semibold text-[var(--cc-primary)] hover:underline bg-[var(--cc-primary-soft)] hover:bg-[var(--cc-primary-soft)]/80 border border-[var(--cc-primary)]/10 px-3.5 py-1.5 rounded-full transition-all cursor-pointer shadow-sm"
        >
          {open ? "Thu gọn thông tin ▲" : "Vì sao gợi ý này? & Lộ trình ▼"}
        </button>
      </div>

      {open && (
        <div className="mt-5 space-y-5 border-t border-[var(--cc-border)] pt-5 text-sm">
          {/* Section: Giải thích từ người dùng & thị trường */}
          <div className="space-y-2.5">
            <h4 className="font-bold font-serif text-[var(--cc-ink)] text-base">🔍 Bằng chứng Sự phù hợp (Explainability)</h4>
            <div className="bg-[var(--cc-primary-soft)]/40 rounded-xl p-4 border border-[var(--cc-border)]/60 space-y-2 shadow-inner">
              <p className="text-[10px] font-bold text-[var(--cc-muted)] tracking-wider uppercase font-serif">Từ chính chia sẻ của em:</p>
              {why.from_you.length > 0 ? (
                why.from_you.map((w, i) => (
                  <p key={i} className="text-sm leading-relaxed text-[var(--cc-ink)]">
                    💬 <span className="italic font-serif">“{w.quote}”</span> — <span className="text-[var(--cc-muted)]">{w.reason}</span>
                  </p>
                ))
              ) : (
                <p className="text-xs text-[var(--cc-muted)] italic font-serif">Chưa ghi nhận trích dẫn trực tiếp.</p>
              )}
            </div>

            {why.from_market.length > 0 && (
              <div className="bg-[var(--cc-primary-soft)]/20 rounded-xl p-4 border border-[var(--cc-border)]/40 space-y-2 shadow-inner">
                <p className="text-[10px] font-bold text-[var(--cc-muted)] tracking-wider uppercase font-serif">Ghi nhận thực tế từ thị trường:</p>
                <div className="grid sm:grid-cols-2 gap-2.5">
                  {why.from_market.map((w, i) => (
                    <p key={i} className="text-xs text-[var(--cc-ink)] flex items-start gap-1">
                      <span>📊</span> <span>{w.stat}</span>
                    </p>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Section: Lộ trình đào tạo đề xuất */}
          <div className="space-y-2.5">
            <h4 className="font-bold font-serif text-[var(--cc-ink)] text-base">🛤️ Lộ trình Đào tạo Đề xuất</h4>
            <div className="grid gap-3.5 md:grid-cols-2">
              {routes.length > 0 ? (
                routes.map((r, i) => (
                  <div key={i} className="rounded-xl border border-[var(--cc-border)] bg-[var(--cc-card-bg)] p-4 shadow-sm hover:border-[var(--cc-primary)] transition-all flex flex-col justify-between">
                    <div>
                      <span className="inline-block text-[10px] font-bold tracking-wider uppercase text-[var(--cc-primary)] bg-[var(--cc-primary-soft)] px-2 py-0.5 rounded border border-[var(--cc-primary)]/10 mb-1">
                        {ROUTE_BADGE[r.type] || r.type}
                      </span>
                      <p className="font-bold text-sm text-[var(--cc-ink)] font-serif mt-1">{r.label}</p>
                      <p className="text-xs text-[var(--cc-muted)] mt-1.5 leading-relaxed">{r.detail}</p>
                    </div>
                    {r.first_steps.length > 0 && (
                      <div className="mt-3 pt-2.5 border-t border-[var(--cc-border)]/40">
                        <p className="text-[9px] font-bold text-[var(--cc-muted)] uppercase tracking-wider mb-1.5">Gợi ý hành động đầu tiên:</p>
                        <ul className="list-inside list-disc text-xs text-[var(--cc-muted)] space-y-1">
                          {r.first_steps.map((s, j) => (
                            <li key={j} className="leading-relaxed">{s}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <p className="text-xs text-[var(--cc-muted)] italic font-serif">Chưa có thông tin lộ trình cụ thể.</p>
              )}
            </div>
          </div>

          {/* Section: Đánh giá Readiness (Chỉ hiện khi có Launch mode data) */}
          {job_readiness && (
            <div className="space-y-2.5 border-t border-[var(--cc-border)]/50 pt-4">
              <h4 className="font-bold font-serif text-[var(--cc-ink)] text-base">🚀 Đánh giá Mức độ Sẵn sàng (Readiness)</h4>
              <div className="bg-[var(--cc-accent-soft)] border border-[var(--cc-accent)]/40 rounded-xl p-4 space-y-3.5 shadow-sm">
                <div className="flex items-center gap-2 flex-wrap text-xs">
                  <span className="font-bold text-[var(--cc-muted)] font-serif">Trạng thái hiện tại:</span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold shadow-sm ${
                    job_readiness.band === "ready_now"
                      ? "bg-green-100 text-green-800 border border-green-200"
                      : job_readiness.band === "near_ready"
                      ? "bg-blue-100 text-blue-800 border border-blue-200"
                      : "bg-amber-100 text-amber-800 border border-amber-200"
                  }`}>
                    {job_readiness.band === "ready_now" && "Sẵn sàng ứng tuyển (Ready Now)"}
                    {job_readiness.band === "near_ready" && "Gần sẵn sàng (Near Ready)"}
                    {job_readiness.band === "build_foundation" && "Cần xây thêm nền tảng (Build Foundation)"}
                  </span>
                </div>
                <p className="text-xs text-[var(--cc-ink)] leading-relaxed font-serif italic">
                  💡 {job_readiness.band_reason}
                </p>

                {/* Match & Missing skills */}
                <div className="grid sm:grid-cols-2 gap-3 text-xs pt-1.5">
                  <div className="space-y-1.5">
                    <p className="font-bold text-[var(--cc-success)]">✓ Kỹ năng đã có bằng chứng:</p>
                    {job_readiness.matched_skills.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {job_readiness.matched_skills.map((s, idx) => (
                          <span key={idx} className="bg-green-50 text-[var(--cc-success)] border border-green-200/50 px-2 py-0.5 rounded text-[11px]" title={s.evidence}>
                            {s.skill}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="italic text-[var(--cc-muted)] font-serif">Chưa có minh chứng kỹ năng.</p>
                    )}
                  </div>
                  <div className="space-y-1.5">
                    <p className="font-bold text-[var(--cc-danger)]">⚠ Kỹ năng thị trường cần nhưng chưa có:</p>
                    {job_readiness.missing_skills.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {job_readiness.missing_skills.map((s, idx) => (
                          <span key={idx} className="bg-red-50 text-[var(--cc-danger)] border border-red-200/50 px-2 py-0.5 rounded text-[11px]">
                            {s}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="italic text-[var(--cc-muted)] font-serif">Đã đầy đủ các kỹ năng cốt lõi!</p>
                    )}
                  </div>
                </div>

                {/* Từ khóa tìm việc */}
                {job_readiness.search_queries.length > 0 && (
                  <div className="text-xs space-y-1.5 pt-1.5 border-t border-[var(--cc-border)]/40">
                    <p className="font-bold text-[var(--cc-muted)] font-serif">🔍 Các vị trí/Từ khóa gợi ý tìm kiếm:</p>
                    <div className="flex flex-wrap gap-1.5">
                      {job_readiness.search_queries.map((q, idx) => (
                        <code key={idx} className="font-mono bg-[var(--cc-primary-soft)] px-2 py-0.5 rounded text-xs text-[var(--cc-primary)] border border-[var(--cc-border)]/40">{q}</code>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Section: Counterfactual */}
          <div className="rounded-xl bg-[var(--cc-accent-soft)] border border-[var(--cc-accent)]/20 p-4 text-xs font-medium text-[var(--cc-muted)] leading-relaxed italic font-serif flex items-start gap-2 shadow-sm">
            <span className="text-sm">🔄</span>
            <div>
              <span className="font-bold text-[var(--cc-ink)]">Tư duy phản chứng: </span>
              {why.counterfactual}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
