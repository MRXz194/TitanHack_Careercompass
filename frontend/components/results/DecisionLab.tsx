"use client";

import { useMemo, useState } from "react";
import { fetchCareerResearch, previewWhatIfSkill } from "@/lib/api";
import type {
  CareerResearchResponse,
  Recommendation,
  Region,
  ResearchIntent,
  WhatIfResponse,
} from "@/types";

const INTENTS: { value: ResearchIntent; label: string }[] = [
  { value: "overview", label: "Tổng quan" },
  { value: "skills", label: "Kỹ năng" },
  { value: "routes", label: "Lộ trình học" },
  { value: "local_market", label: "Thị trường địa phương" },
];

const STATUS_LABEL: Record<CareerResearchResponse["status"], string> = {
  live: "LIVE",
  cached: "CACHE",
  replay: "REPLAY",
  unavailable: "LOCAL ONLY",
};

function formatSalary(value: number | null): string {
  return value === null ? "Chưa đủ mẫu" : `${value} triệu/tháng`;
}

export default function DecisionLab({ options }: { options: Recommendation[] }) {
  const [selected, setSelected] = useState<string[]>(options.slice(0, 2).map((item) => item.career_id));
  const [intent, setIntent] = useState<ResearchIntent>("overview");
  const [region] = useState<Region>("all");
  const [research, setResearch] = useState<CareerResearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [whatIfSkill, setWhatIfSkill] = useState("");
  const [whatIf, setWhatIf] = useState<WhatIfResponse | null>(null);
  const [whatIfLoading, setWhatIfLoading] = useState(false);

  const compared = useMemo(
    () => selected.flatMap((id) => options.find((item) => item.career_id === id) ?? []),
    [options, selected],
  );

  const toggle = (careerId: string) => {
    setResearch(null);
    setSelected((current) => {
      if (current.includes(careerId)) return current.filter((id) => id !== careerId);
      return current.length >= 2 ? [current[1], careerId] : [...current, careerId];
    });
  };

  const runResearch = async () => {
    if (selected.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      setResearch(await fetchCareerResearch(selected, intent, region));
    } catch {
      setError("Chưa tải được nguồn kiểm chứng. Các gợi ý và số liệu nội bộ không bị ảnh hưởng.");
    } finally {
      setLoading(false);
    }
  };

  const runWhatIf = async () => {
    const skill = whatIfSkill.trim();
    if (!skill) return;
    setWhatIfLoading(true);
    setError(null);
    try {
      setWhatIf(await previewWhatIfSkill(skill));
    } catch {
      setError("Chưa mô phỏng được thay đổi này. Hồ sơ gốc vẫn giữ nguyên.");
    } finally {
      setWhatIfLoading(false);
    }
  };

  return (
    <section className="cc-lab" aria-labelledby="decision-lab-title">
      <div className="cc-section-heading">
        <p className="cc-kicker">DECISION LAB / COMPARE + VERIFY</p>
        <h2 id="decision-lab-title">Đặt các lựa chọn cạnh nhau, rồi tự kiểm chứng.</h2>
        <p>Chọn tối đa hai hướng. Không có “người thắng” — chỉ có trade-off, mức độ chắc chắn và bước thử tiếp theo.</p>
      </div>

      <div className="cc-option-strip" aria-label="Chọn nghề để so sánh">
        {options.map((option) => {
          const active = selected.includes(option.career_id);
          return (
            <button
              key={option.career_id}
              type="button"
              aria-pressed={active}
              onClick={() => toggle(option.career_id)}
              className={active ? "cc-chip cc-chip-active" : "cc-chip"}
            >
              {active ? "−" : "+"} {option.title}
            </button>
          );
        })}
      </div>

      {compared.length > 0 && (
        <div className="cc-compare-grid">
          {compared.map((item) => (
            <article key={item.career_id} className="cc-compare-card">
              <div className="cc-card-index">OPTION / {item.career_id}</div>
              <h3>{item.title}</h3>
              <dl className="cc-metric-list">
                <div><dt>Phù hợp tham khảo</dt><dd>{Math.round(item.match_score * 100)}%</dd></div>
                <div><dt>Tin quan sát / 90 ngày</dt><dd>{item.market.demand_count_90d.toLocaleString("vi-VN")}</dd></div>
                <div><dt>Lương trung vị</dt><dd>{formatSalary(item.market.salary_p50_trieu)}</dd></div>
                <div><dt>Mẫu lương</dt><dd>{item.market.salary_sample_count}</dd></div>
                <div><dt>Độ tin cậy</dt><dd>{item.market.low_confidence ? "Cần kiểm chứng" : "Đủ để tham khảo"}</dd></div>
                <div><dt>Lộ trình ngoài đại học</dt><dd>{item.routes.find((route) => route.type !== "university")?.label ?? "Chưa có"}</dd></div>
              </dl>
              <div className="cc-signal-inspector">
                <p className="cc-kicker">SIGNAL INSPECTOR</p>
                <p>{item.market.source_note}</p>
                <p>Kỹ năng thường gặp: {item.market.top_skills.slice(0, 4).join(" · ") || "chưa đủ dữ liệu"}</p>
                <p>{item.why.counterfactual}</p>
              </div>
            </article>
          ))}
        </div>
      )}

      <div className="cc-research-toolbar">
        <div className="cc-segment" aria-label="Mục đích nghiên cứu">
          {INTENTS.map((item) => (
            <button
              key={item.value}
              type="button"
              aria-pressed={intent === item.value}
              onClick={() => setIntent(item.value)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <button type="button" className="cc-button-dark" disabled={loading || selected.length === 0} onClick={runResearch}>
          {loading ? "ĐANG KIỂM CHỨNG…" : "NGHIÊN CỨU THÊM"}
        </button>
        <button type="button" className="cc-button-ghost cc-print-action" onClick={() => window.print()}>
          IN TÓM TẮT TƯ VẤN
        </button>
      </div>

      {error && <p role="alert" className="cc-inline-error">{error}</p>}

      {research && (
        <div className="cc-research-results" aria-live="polite">
          <div className="cc-research-meta">
            <span className="cc-status">{STATUS_LABEL[research.status]}</span>
            <p>{research.limitation}</p>
          </div>
          {research.careers.map((career) => (
            <div key={career.career_id} className="cc-source-group">
              <h3>{career.title}</h3>
              {career.sources.length === 0 ? (
                <p className="cc-empty">Chưa có nguồn web hợp lệ. Signal nội bộ phía trên vẫn giữ nguyên và có ghi rõ giới hạn.</p>
              ) : (
                career.sources.map((source) => (
                  <a key={source.url} className="cc-source-card" href={source.url} target="_blank" rel="noreferrer">
                    <span>{source.source_tier.toUpperCase()} / {source.domain}</span>
                    <strong>{source.title}</strong>
                    <p>{source.snippet}</p>
                    <small>Truy xuất {new Date(source.retrieved_at).toLocaleString("vi-VN")} ↗</small>
                  </a>
                ))
              )}
            </div>
          ))}
          <p className="cc-research-disclaimer">{research.disclaimer}</p>
        </div>
      )}

      <div className="cc-what-if">
        <div>
          <p className="cc-kicker">WHAT-IF / WORKING COPY</p>
          <h3>Nếu em thử bổ sung một kỹ năng thì sao?</h3>
          <p>Mô phỏng chạy lại scoring thật trên bản sao; không ghi đè hồ sơ và không biến giả định thành bằng chứng.</p>
        </div>
        <div className="cc-what-if-form">
          <label htmlFor="what-if-skill">Kỹ năng muốn thử</label>
          <input
            id="what-if-skill"
            value={whatIfSkill}
            maxLength={80}
            placeholder="Ví dụ: SQL"
            onChange={(event) => setWhatIfSkill(event.target.value)}
          />
          <button className="cc-button-dark" type="button" disabled={!whatIfSkill.trim() || whatIfLoading} onClick={runWhatIf}>
            {whatIfLoading ? "ĐANG MÔ PHỎNG…" : "THỬ THAY ĐỔI"}
          </button>
          {whatIf && <button className="cc-button-ghost" type="button" onClick={() => setWhatIf(null)}>HOÀN TÁC PREVIEW</button>}
        </div>
        {whatIf && (
          <div className="cc-what-if-results" aria-live="polite">
            <div className="cc-research-meta"><span className="cc-status">PREVIEW</span><p>{whatIf.mutation_label}</p></div>
            {whatIf.deltas.length === 0 ? (
              <p className="cc-empty">Thay đổi này chưa làm thứ tự hoặc điểm số thay đổi — đây cũng là một kết quả hữu ích để kiểm chứng.</p>
            ) : (
              whatIf.deltas.slice(0, 6).map((delta) => (
                <div key={delta.career_id} className="cc-delta-row">
                  <strong>{delta.title}</strong>
                  <span>Hạng {delta.before_rank ?? "—"} → {delta.after_rank ?? "—"}</span>
                  <span>{delta.before_score === null ? "—" : `${Math.round(delta.before_score * 100)}%`} → {delta.after_score === null ? "—" : `${Math.round(delta.after_score * 100)}%`}</span>
                </div>
              ))
            )}
            <p className="cc-research-disclaimer">{whatIf.disclaimer}</p>
          </div>
        )}
      </div>
    </section>
  );
}
