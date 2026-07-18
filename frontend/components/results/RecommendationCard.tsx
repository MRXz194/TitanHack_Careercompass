"use client";

import { useState } from "react";
import type { Recommendation } from "@/types";
import Tooltip from "@/components/ui/Tooltip";
import { TOOLTIPS } from "@/lib/copy/transparency";

const ROUTE_BADGE: Record<string, string> = {
  university: "Đại học",
  college: "Cao đẳng",
  vocational: "Học nghề",
  certificate: "Chứng chỉ",
};

interface RecommendationCardProps {
  rec: Recommendation;
  rank?: number;
}

type TabType = "why" | "market" | "routes" | "readiness";

export default function RecommendationCard({ rec, rank }: RecommendationCardProps) {
  const { market, why, routes, job_readiness, is_stretch } = rec;
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>("why");

  // Kiểm tra xu hướng tuyển dụng
  const showTrend = market.trend_pct !== null && !market.low_confidence;
  const trendVal = market.trend_pct ?? 0;

  // Lọc danh sách tab: Chỉ hiện tab "Readiness" nếu là Launch mode (job_readiness != null)
  const tabs: { id: TabType; label: string }[] = [
    { id: "why", label: "Vì sao gợi ý?" },
    { id: "market", label: "Thị trường" },
    { id: "routes", label: "Lộ trình học" },
  ];

  if (job_readiness) {
    tabs.push({ id: "readiness", label: "Độ sẵn sàng" });
  }

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
          Hướng đi gợi mở / Stretch
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
            <Tooltip content={TOOLTIPS.match_score.text}>
              {Math.round(rec.match_score * 100)}% mức tương thích tham khảo
            </Tooltip>
          </span>
        </div>
      </div>

      {/* Tóm tắt thị trường nhanh */}
      <div className="mt-4 flex flex-wrap gap-2 text-xs text-[var(--cc-muted)] border-t border-[var(--cc-border)]/60 pt-3.5">
        <span className="flex items-center gap-1 bg-[var(--cc-primary-soft)]/40 px-2.5 py-1 rounded-md border border-[var(--cc-border)]/50">
              {market.demand_count_90d.toLocaleString("vi-VN")} tin tuyển/90 ngày
        </span>

        {market.salary_p50_trieu !== null ? (
          <span className="flex items-center gap-1 bg-[var(--cc-primary-soft)]/40 px-2.5 py-1 rounded-md border border-[var(--cc-border)]/50">
            💰 Lương trung vị: ~{market.salary_p50_trieu} triệu/tháng
          </span>
        ) : (
          <span className="flex items-center gap-1 bg-amber-50/50 text-amber-800/80 px-2.5 py-1 rounded-md border border-amber-200/40">
            💰 Lương: Số liệu có hạn chế
          </span>
        )}

        {showTrend && (
          <span
            className={`flex items-center gap-1 px-2.5 py-1 rounded-md border ${
              trendVal >= 0
                ? "bg-green-50/40 text-[var(--cc-success)] border-green-200/40"
                : "bg-red-50/40 text-[var(--cc-danger)] border-red-200/40"
            }`}
          >
            <Tooltip content={TOOLTIPS.demand_proxy.text}>
              {trendVal >= 0 ? "▲" : "▼"} {Math.abs(trendVal)}% xu hướng
            </Tooltip>
          </span>
        )}
      </div>

      <div className="mt-4 flex justify-between items-center flex-wrap gap-2">
        <span className="text-[10px] text-[var(--cc-muted)] italic font-serif">
          <Tooltip content={TOOLTIPS.source_note.text}>
            {market.source_note}
          </Tooltip>
        </span>
        <button
          onClick={() => {
            setOpen(!open);
            // Reset về tab đầu khi đóng/mở
            if (!open) setActiveTab("why");
          }}
          className="inline-flex items-center gap-1 text-xs font-semibold text-[var(--cc-primary)] hover:underline bg-[var(--cc-primary-soft)] hover:bg-[var(--cc-primary-soft)]/80 border border-[var(--cc-primary)]/10 px-4 py-2 rounded-full transition-all cursor-pointer shadow-sm"
        >
          {open ? "Thu gọn thông tin ▲" : "Vì sao gợi ý? & Lộ trình chi tiết ▼"}
        </button>
      </div>

      {open && (
        <div className="mt-5 border-t border-[var(--cc-border)] pt-5 animate-fadeIn">
          {/* Hệ thống TAB phong cách vintage */}
          <div className="flex border-b border-[var(--cc-border)] overflow-x-auto gap-1 pb-px scrollbar-none">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2.5 text-xs font-bold font-serif border-t border-x rounded-t-xl transition-all whitespace-nowrap cursor-pointer ${
                  activeTab === tab.id
                    ? "bg-[var(--cc-card-bg)] border-[var(--cc-border)] border-b-[var(--cc-card-bg)] text-[var(--cc-primary)] relative z-10"
                    : "bg-slate-100/40 border-transparent text-[var(--cc-muted)] hover:bg-slate-100/70 hover:text-[var(--cc-ink)]"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="p-4 bg-[var(--cc-card-bg)] border-x border-b border-[var(--cc-border)] rounded-b-xl space-y-4">
            
            {/* TAB 1: WHY (Giải thích sự phù hợp) */}
            {activeTab === "why" && (
              <div className="space-y-3">
                <div className="bg-[var(--cc-primary-soft)]/40 rounded-xl p-4 border border-[var(--cc-border)]/60 space-y-2 shadow-inner">
                  <p className="text-[10px] font-bold text-[var(--cc-muted)] tracking-wider uppercase font-serif">Dựa trên mong muốn của em:</p>
                  {why.from_you.length > 0 ? (
                    why.from_you.map((w, idx) => (
                      <p key={idx} className="text-sm leading-relaxed text-[var(--cc-ink)]">
                        <span className="italic font-serif">“{w.quote}”</span> — <span className="text-[var(--cc-muted)]">{w.reason}</span>
                      </p>
                    ))
                  ) : (
                    <p className="text-xs text-[var(--cc-muted)] italic font-serif">Chưa có trích dẫn trực tiếp từ cuộc trò chuyện.</p>
                  )}
                </div>

                <div className="bg-[var(--cc-primary-soft)]/20 rounded-xl p-4 border border-[var(--cc-border)]/40 space-y-2 shadow-inner">
                  <p className="text-[10px] font-bold text-[var(--cc-muted)] tracking-wider uppercase font-serif">Tương quan nhu cầu tuyển dụng:</p>
                  {why.from_market.length > 0 ? (
                    <div className="grid sm:grid-cols-2 gap-2.5">
                      {why.from_market.map((w, idx) => (
                        <p key={idx} className="text-xs text-[var(--cc-ink)] flex items-start gap-1">
                          <span>{w.stat}</span>
                        </p>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-[var(--cc-muted)] italic font-serif">Chưa có đối chiếu số liệu thị trường.</p>
                  )}
                </div>
              </div>
            )}

            {/* TAB 2: MARKET (Thống kê chi tiết thị trường) */}
            {activeTab === "market" && (
              <div className="space-y-3.5">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="rounded-xl border border-[var(--cc-border)] bg-white p-3 shadow-inner">
                    <span className="block text-[10px] text-[var(--cc-muted)] uppercase tracking-wider">Tin tuyển dụng</span>
                    <span className="text-lg font-bold font-serif text-[var(--cc-primary)]">{market.demand_count_90d} tin</span>
                  </div>
                  
                  <div className="rounded-xl border border-[var(--cc-border)] bg-white p-3 shadow-inner">
                    <span className="block text-[10px] text-[var(--cc-muted)] uppercase tracking-wider">Mức lương (Median)</span>
                    <span className="text-lg font-bold font-serif text-[var(--cc-primary)]">
                      {market.salary_p50_trieu ? `~${market.salary_p50_trieu}tr` : "N/A"}
                    </span>
                  </div>

                  <div className="rounded-xl border border-[var(--cc-border)] bg-white p-3 shadow-inner">
                    <span className="block text-[10px] text-[var(--cc-muted)] uppercase tracking-wider">Dải lương phổ biến</span>
                    <span className="text-xs font-bold font-serif text-[var(--cc-primary)] mt-1.5 block">
                      {market.salary_p25_trieu && market.salary_p75_trieu 
                        ? `${market.salary_p25_trieu}tr – ${market.salary_p75_trieu}tr` 
                        : "Dữ liệu hạn chế"}
                    </span>
                  </div>

                  <div className="rounded-xl border border-[var(--cc-border)] bg-white p-3 shadow-inner">
                    <span className="block text-[10px] text-[var(--cc-muted)] uppercase tracking-wider">Mẫu lương khảo sát</span>
                    <span className="text-lg font-bold font-serif text-[var(--cc-primary)]">{market.salary_sample_count} tin</span>
                  </div>
                </div>

                <div className="grid sm:grid-cols-2 gap-3 pt-1">
                  {/* Top skills required */}
                  <div className="space-y-1.5">
                    <p className="text-xs font-bold text-[var(--cc-muted)] uppercase font-serif">Kỹ năng thị trường yêu cầu nhiều:</p>
                    <div className="flex flex-wrap gap-1.5">
                      {market.top_skills.map((skill, idx) => (
                        <span key={idx} className="bg-slate-100/80 border border-[var(--cc-border)]/65 px-2 py-0.5 rounded text-[11px]">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Top regions */}
                  <div className="space-y-1.5">
                    <p className="text-xs font-bold text-[var(--cc-muted)] uppercase font-serif">Vùng tuyển dụng nhiều nhất:</p>
                    <div className="flex flex-wrap gap-1.5">
                      {market.top_regions.map((region, idx) => (
                        <span key={idx} className="bg-slate-100/80 border border-[var(--cc-border)]/65 px-2 py-0.5 rounded text-[11px] capitalize">
                          {region === "hcm" ? "TP. Hồ Chí Minh" : region === "danang" ? "Đà Nẵng" : region === "hanoi" ? "Hà Nội" : region}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {market.low_confidence && (
                  <div className="rounded-lg bg-amber-50/50 border border-amber-200/50 p-3 text-xs text-amber-800 flex items-start gap-1.5">
                    <span><b>Lưu ý:</b> Dữ liệu thị trường cho nghề này tại vùng miền của em có kích thước mẫu khá nhỏ. Các con số chỉ mang tính tham khảo để định hướng.</span>
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: ROUTES (Các lộ trình học) */}
            {activeTab === "routes" && (
              <div className="grid gap-3.5 md:grid-cols-2">
                {routes.map((r, idx) => (
                  <div key={idx} className="rounded-xl border border-[var(--cc-border)] bg-white p-4 shadow-sm flex flex-col justify-between">
                    <div>
                      <span className="inline-block text-[10px] font-bold tracking-wider uppercase text-[var(--cc-primary)] bg-[var(--cc-primary-soft)] px-2 py-0.5 rounded border border-[var(--cc-primary)]/10 mb-1.5">
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
            )}

            {/* TAB 4: READINESS & 30-DAY ACTIONS (Chỉ hiển thị cho Launch mode) */}
            {activeTab === "readiness" && job_readiness && (
              <div className="space-y-4">
                <div className="bg-[var(--cc-accent-soft)] border border-[var(--cc-accent)]/40 rounded-xl p-4 space-y-3">
                  <div className="flex items-center gap-2 flex-wrap text-xs">
                    <span className="font-bold text-[var(--cc-muted)] font-serif">Mức độ chuẩn bị:</span>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold shadow-sm ${
                      job_readiness.band === "ready_now"
                        ? "bg-green-100 text-green-800 border border-green-200"
                        : job_readiness.band === "near_ready"
                        ? "bg-blue-100 text-blue-800 border border-blue-200"
                        : "bg-amber-100 text-amber-800 border border-amber-200"
                    }`}>
                      <Tooltip content={TOOLTIPS.readiness_band.text}>
                        {job_readiness.band === "ready_now" && "Sẵn sàng ứng tuyển (Ready Now)"}
                        {job_readiness.band === "near_ready" && "Gần sẵn sàng (Near Ready)"}
                        {job_readiness.band === "build_foundation" && "Cần xây thêm nền tảng (Build Foundation)"}
                      </Tooltip>
                    </span>
                  </div>
                  <p className="text-xs text-[var(--cc-ink)] leading-relaxed font-serif italic">
                    {job_readiness.band_reason}
                  </p>

                  <div className="grid sm:grid-cols-2 gap-3 text-xs pt-1">
                    <div className="space-y-1">
                      <p className="font-bold text-[var(--cc-success)]">Kỹ năng đã có minh chứng:</p>
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
                    <div className="space-y-1">
                      <p className="font-bold text-[var(--cc-danger)]">Kỹ năng thị trường cần nhưng thiếu:</p>
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

                  {job_readiness.search_queries.length > 0 && (
                    <div className="text-xs space-y-1.5 pt-2 border-t border-[var(--cc-border)]/40">
                      <p className="font-bold text-[var(--cc-muted)] font-serif">Gợi ý chức danh tìm việc (aliases):</p>
                      <div className="flex flex-wrap gap-1.5">
                        {job_readiness.search_queries.map((q, idx) => (
                          <code key={idx} className="font-mono bg-[var(--cc-primary-soft)] px-2 py-0.5 rounded text-xs text-[var(--cc-primary)] border border-[var(--cc-border)]/40">{q}</code>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Bảng Kế hoạch hành động 30 ngày (30-day Action Plan) */}
                <div className="space-y-2 pt-1">
                  <p className="text-xs font-bold text-[var(--cc-ink)] uppercase font-serif tracking-wide">Kế hoạch tích lũy năng lực trong 30 ngày tới:</p>
                  
                  <div className="relative border-l-2 border-[var(--cc-border)] ml-3 pl-4 space-y-4">
                    {job_readiness.actions_30d.map((act) => (
                      <div key={act.week} className="relative">
                        {/* Dot marker */}
                        <div className="absolute -left-[23px] top-1.5 bg-[var(--cc-primary)] border-4 border-[var(--cc-card-bg)] w-4 h-4 rounded-full" />
                        
                        <div className="bg-white rounded-xl border border-[var(--cc-border)] p-3.5 shadow-sm space-y-1.5">
                          <div className="flex items-center justify-between flex-wrap gap-1">
                            <span className="text-xs font-bold font-serif text-[var(--cc-primary)]">Tuần {act.week}</span>
                            <span className="text-[10px] font-bold text-[var(--cc-muted)] bg-slate-100 px-2 py-0.5 rounded border border-[var(--cc-border)]/30">
                              Mục tiêu kiểm chứng
                            </span>
                          </div>
                          
                          <p className="text-sm font-semibold text-[var(--cc-ink)]">{act.action}</p>
                          
                          <div className="grid sm:grid-cols-2 gap-2 text-xs pt-1.5 border-t border-dashed border-[var(--cc-border)]/55">
                            <div>
                              <p className="text-[10px] font-bold text-[var(--cc-muted)] uppercase">Sản phẩm đầu ra (Deliverable):</p>
                              <p className="text-xs text-[var(--cc-ink)] mt-0.5 font-mono bg-slate-50 px-1.5 py-0.5 rounded">{act.deliverable}</p>
                            </div>
                            <div>
                              <p className="text-[10px] font-bold text-[var(--cc-muted)] uppercase">Ý nghĩa hành động:</p>
                              <p className="text-xs text-[var(--cc-muted)] mt-0.5">{act.why}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Section: Counterfactual (Tư duy phản chứng) */}
          <div className="mt-4 rounded-xl bg-[var(--cc-accent-soft)] border border-[var(--cc-accent)]/20 p-4 text-xs font-medium text-[var(--cc-muted)] leading-relaxed italic font-serif flex items-start gap-2 shadow-sm">
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
