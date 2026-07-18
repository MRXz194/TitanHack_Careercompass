"use client";

import { useState } from "react";
import type { Recommendation } from "@/types";
import Tooltip from "@/components/ui/Tooltip";
import { TOOLTIPS } from "@/lib/copy/transparency";

const ROUTE_BADGE: Record<string, string> = {
  university: "🎓 Đại học",
  college: "🏫 Cao đẳng",
  vocational: "🔧 Học nghề",
  certificate: "📜 Chứng chỉ",
};

interface StretchCardProps {
  rec: Recommendation;
}

export default function StretchCard({ rec }: StretchCardProps) {
  const [open, setOpen] = useState(false);
  const { market, why, routes, job_readiness } = rec;

  const showTrend = market.trend_pct !== null && !market.low_confidence;
  const trendVal = market.trend_pct ?? 0;

  return (
    <div className="relative rounded-2xl border-2 border-dashed border-[var(--cc-accent)] bg-[var(--cc-accent-soft)] p-6 shadow-md transition-all duration-300 hover:shadow-lg overflow-hidden">
      {/* Con dấu Vintage "Mở rộng cơ hội" góc trên cùng */}
      <div className="absolute -right-4 -top-4 w-24 h-24 rounded-full border-2 border-[var(--cc-accent)]/30 flex items-center justify-center rotate-12 select-none pointer-events-none">
        <span className="text-[9px] font-bold font-serif text-[var(--cc-accent)] uppercase tracking-wider text-center px-2 leading-tight">
          Mở rộng<br />Cơ hội
        </span>
      </div>

      <div className="space-y-3">
        <div className="inline-flex items-center gap-1.5 rounded-full bg-amber-100/60 border border-[var(--cc-accent)] px-3.5 py-1 text-xs font-bold text-amber-800 font-serif shadow-sm">
          <Tooltip content={TOOLTIPS.stretch.text}>
            ✨ Gợi ý mở rộng (Stretch Recommendation)
          </Tooltip>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-xl font-bold tracking-tight text-[var(--cc-ink)] font-serif">
              {rec.title}
            </h3>
            <p className="text-xs text-[var(--cc-muted)]">
              Mã nghề gợi mở: <code className="font-mono bg-white/70 px-1.5 py-0.5 rounded text-[var(--cc-primary)] border border-[var(--cc-border)]">{rec.career_id}</code>
            </p>
          </div>

          <div className="shrink-0">
            <span className="inline-block rounded-full bg-white/80 border border-[var(--cc-accent)]/20 px-4 py-1.5 text-xs font-bold text-amber-800 shadow-sm font-serif">
              Có thể em chưa nghĩ tới
            </span>
          </div>
        </div>

        {/* Khung giải thích tính chất "Stretch" */}
        <p className="text-xs text-[var(--cc-ink)] leading-relaxed italic font-serif bg-white/50 border border-[var(--cc-border)]/40 p-4 rounded-xl shadow-inner">
          💡 <b>Ý nghĩa gợi ý:</b> Hướng đi này nằm ngoài vùng sở thích cốt lõi hiện tại của em, nhưng dựa trên các liên kết kĩ năng hoặc sở thích phụ, hệ thống đề xuất nhằm giúp em mở rộng thêm góc nhìn, tránh việc bị giới hạn lựa chọn (Anti-bias by design).
        </p>

        {/* Tổng quan thị trường */}
        <div className="flex flex-wrap gap-2 text-xs text-[var(--cc-muted)] pt-1">
          <span className="flex items-center gap-1 bg-white/60 px-2.5 py-1 rounded-md border border-[var(--cc-border)]/50">
            📈 {market.demand_count_90d.toLocaleString("vi-VN")} tin tuyển dụng/90 ngày
          </span>

          {market.salary_p50_trieu !== null ? (
            <span className="flex items-center gap-1 bg-white/60 px-2.5 py-1 rounded-md border border-[var(--cc-border)]/50">
              💰 Lương trung vị: ~{market.salary_p50_trieu} triệu/tháng
            </span>
          ) : (
            <span className="flex items-center gap-1 bg-white/60 px-2.5 py-1 rounded-md border border-[var(--cc-border)]/50">
              💰 Lương: Số liệu có hạn chế
            </span>
          )}

          {showTrend && (
            <span className="flex items-center gap-1 bg-white/60 text-[var(--cc-success)] px-2.5 py-1 rounded-md border border-[var(--cc-border)]/50">
              <Tooltip content={TOOLTIPS.demand_proxy.text}>
                ▲ {Math.abs(trendVal)}% xu hướng
              </Tooltip>
            </span>
          )}
        </div>

        <div className="flex justify-between items-center pt-2 flex-wrap gap-2">
          <span className="text-[10px] text-[var(--cc-muted)] italic font-serif">
            <Tooltip content={TOOLTIPS.source_note.text}>
              {market.source_note}
            </Tooltip>
          </span>
          <button
            onClick={() => setOpen(!open)}
            className="inline-flex items-center gap-1 text-xs font-semibold text-amber-800 hover:underline bg-white/80 hover:bg-white border border-[var(--cc-accent)]/20 px-4 py-2 rounded-full transition-all cursor-pointer shadow-sm"
          >
            {open ? "Thu gọn thông tin ▲" : "Vì sao gợi ý? & Lộ trình chi tiết ▼"}
          </button>
        </div>
      </div>

      {open && (
        <div className="mt-5 border-t border-[var(--cc-border)]/65 pt-5 space-y-5 text-sm">
          {/* Section: Explainability */}
          <div className="space-y-2.5">
            <h4 className="font-bold font-serif text-[var(--cc-ink)] text-base">🔍 Phân tích Lý do Lựa chọn</h4>
            
            <div className="bg-white/80 rounded-xl p-4 border border-[var(--cc-border)] space-y-2 shadow-inner">
              <p className="text-[10px] font-bold text-[var(--cc-muted)] tracking-wider uppercase font-serif">Dựa trên mong muốn của em:</p>
              {why.from_you.length > 0 ? (
                why.from_you.map((w, idx) => (
                  <p key={idx} className="text-sm leading-relaxed text-[var(--cc-ink)]">
                    💬 <span className="italic font-serif">“{w.quote}”</span> — <span className="text-[var(--cc-muted)]">{w.reason}</span>
                  </p>
                ))
              ) : (
                <p className="text-xs text-[var(--cc-muted)] italic font-serif font-serif">Chưa ghi nhận trích dẫn trực tiếp.</p>
              )}
            </div>

            {why.from_market.length > 0 && (
              <div className="bg-white/50 rounded-xl p-4 border border-[var(--cc-border)] space-y-2 shadow-inner">
                <p className="text-[10px] font-bold text-[var(--cc-muted)] tracking-wider uppercase font-serif">Bằng chứng từ thị trường tuyển dụng:</p>
                <div className="grid sm:grid-cols-2 gap-2.5">
                  {why.from_market.map((w, idx) => (
                    <p key={idx} className="text-xs text-[var(--cc-ink)] flex items-start gap-1">
                      <span>📊</span> <span>{w.stat}</span>
                    </p>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Section: Routes */}
          <div className="space-y-2.5">
            <h4 className="font-bold font-serif text-[var(--cc-ink)] text-base">🛤️ Đề xuất Lộ trình Đào tạo</h4>
            <div className="grid gap-3.5 md:grid-cols-2">
              {routes.map((r, idx) => (
                <div key={idx} className="rounded-xl border border-[var(--cc-border)] bg-white p-4 shadow-sm flex flex-col justify-between hover:border-[var(--cc-accent)] transition-all">
                  <div>
                    <span className="inline-block text-[10px] font-bold tracking-wider uppercase text-[var(--cc-accent)] bg-amber-50 px-2 py-0.5 rounded border border-[var(--cc-accent)]/10 mb-1.5">
                      {ROUTE_BADGE[r.type] || r.type}
                    </span>
                    <p className="font-bold text-sm text-[var(--cc-ink)] font-serif mt-1">{r.label}</p>
                    <p className="text-xs text-[var(--cc-muted)] mt-1.5 leading-relaxed">{r.detail}</p>
                  </div>
                  {r.first_steps.length > 0 && (
                    <div className="mt-3.5 pt-2.5 border-t border-[var(--cc-border)]/40">
                      <p className="text-[9px] font-bold text-[var(--cc-muted)] uppercase tracking-wider mb-1.5">Gợi ý hành động đầu tiên:</p>
                      <ul className="list-inside list-disc text-xs text-[var(--cc-muted)] space-y-1">
                        {r.first_steps.map((s, j) => (
                          <li key={j} className="leading-relaxed">{s}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Section: Launch readiness */}
          {job_readiness && (
            <div className="space-y-3 border-t border-[var(--cc-border)]/50 pt-4">
              <h4 className="font-bold font-serif text-[var(--cc-ink)] text-base">🚀 Đánh giá Mức độ Sẵn sàng (Readiness)</h4>
              <div className="bg-white/70 border border-[var(--cc-border)] rounded-xl p-4 space-y-3 shadow-sm">
                <div className="flex items-center gap-2 flex-wrap text-xs">
                  <span className="font-bold text-[var(--cc-muted)] font-serif">Mức độ chuẩn bị:</span>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200 shadow-sm">
                    {job_readiness.band === "ready_now" && "Sẵn sàng ứng tuyển (Ready Now)"}
                    {job_readiness.band === "near_ready" && "Gần sẵn sàng (Near Ready)"}
                    {job_readiness.band === "build_foundation" && "Cần xây thêm nền tảng (Build Foundation)"}
                  </span>
                </div>
                <p className="text-xs text-[var(--cc-ink)] leading-relaxed font-serif italic">
                  💡 {job_readiness.band_reason}
                </p>

                <div className="grid sm:grid-cols-2 gap-3 text-xs pt-1.5">
                  <div className="space-y-1">
                    <p className="font-bold text-[var(--cc-success)]">✓ Kỹ năng đã có:</p>
                    {job_readiness.matched_skills.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {job_readiness.matched_skills.map((s, idx) => (
                          <span key={idx} className="bg-green-50 text-[var(--cc-success)] border border-green-200/50 px-2 py-0.5 rounded text-[11px]" title={s.evidence}>
                            {s.skill}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="italic text-[var(--cc-muted)] font-serif font-medium">Chưa có minh chứng kỹ năng.</p>
                    )}
                  </div>
                  <div className="space-y-1">
                    <p className="font-bold text-[var(--cc-danger)]">⚠ Kỹ năng thị trường cần nhưng thiếu:</p>
                    {job_readiness.missing_skills.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {job_readiness.missing_skills.map((s, idx) => (
                          <span key={idx} className="bg-red-50 text-[var(--cc-danger)] border border-red-200/50 px-2 py-0.5 rounded text-[11px]">
                            {s}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="italic text-[var(--cc-muted)] font-serif font-medium">Đã đầy đủ kỹ năng cốt lõi!</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section: Counterfactual */}
          <div className="rounded-xl bg-white/70 border border-[var(--cc-accent)]/25 p-4 text-xs font-medium text-[var(--cc-muted)] leading-relaxed italic font-serif flex items-start gap-2 shadow-sm">
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
