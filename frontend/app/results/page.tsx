"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchRecommendations } from "@/lib/api";
import type { RecommendationResponse, JourneyMode } from "@/types";
import ResultsHeader from "@/components/results/ResultsHeader";
import RecommendationCard from "@/components/results/RecommendationCard";
import StretchCard from "@/components/results/StretchCard";
import DecisionLab from "@/components/results/DecisionLab";

export default function ResultsPage() {
  const [data, setData] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [journeyMode, setJourneyMode] = useState<JourneyMode>("explore");

  const loadRecommendations = useCallback(async () => {
    // Đọc chế độ hành trình từ LocalStorage
    const savedMode = typeof window !== "undefined" ? localStorage.getItem("cc_journey_mode") as JourneyMode : null;
    const mode = savedMode === "launch" ? "launch" : "explore";
    setJourneyMode(mode);
    setLoading(true);
    setError(null);
    try {
      const res = await fetchRecommendations(mode);
      setData(res);
      // Nếu đề xuất đầu tiên có job_readiness, session backend đang ở Launch mode.
      if (res.recommendations?.[0]?.job_readiness) setJourneyMode("launch");
    } catch {
      setData(null);
      setError("Không thể tải kết quả định hướng. Phiên có thể đã hết hạn hoặc kết nối backend đang gián đoạn.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadRecommendations();
  }, [loadRecommendations]);

  const isMock = process.env.NEXT_PUBLIC_USE_MOCK === "1";

  if (loading) {
    return (
      <main className="mx-auto max-w-3xl min-h-screen p-6 flex flex-col justify-center items-center space-y-4">
        <div className="relative flex items-center justify-center">
          <div className="w-12 h-12 rounded-full border-4 border-[var(--cc-border)] border-t-[var(--cc-primary)] animate-spin" />
        </div>
        <p className="text-sm font-serif italic text-[var(--cc-muted)] animate-pulse">
          Đang đọc lại hồ sơ, phác thảo lộ trình cho em…
        </p>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="mx-auto max-w-3xl min-h-screen p-6 flex flex-col justify-center items-center space-y-4 text-center">
        <p className="cc-kicker">SYSTEM / RESULTS UNAVAILABLE</p>
        <h2 className="text-xl font-bold font-serif text-[var(--cc-ink)]">Đã xảy ra sự cố nhỏ</h2>
        <p className="text-sm text-[var(--cc-muted)] max-w-md leading-relaxed">
          {error || "Không tìm thấy dữ liệu phiên khảo sát. Hãy đảm bảo em đã hoàn thành cuộc hội thoại trước."}
        </p>
        <div className="flex flex-wrap justify-center gap-3 pt-2">
          <button type="button" className="cc-button-dark" onClick={() => void loadRecommendations()}>
            THỬ TẢI LẠI
          </button>
          <a
            href="/"
            className="cc-button-ghost"
          >
            VỀ TRANG CHỦ
          </a>
          <a
            href={`/explore?mode=${journeyMode}&new=1`}
            className="cc-button-orange"
          >
            TẠO HỒ SƠ MỚI
          </a>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl min-h-screen p-6 space-y-6">
      <div className="cc-journal-nav">
        <a href="/" className="hover:text-[var(--cc-primary)] transition-all font-bold tracking-widest uppercase">
          CareerCompass
        </a>
        <div className="flex gap-3">
          <a href="/market" className="hover:underline">Thị trường việc làm</a>
          <span>·</span>
          <a href="/how-it-works" className="hover:underline">Cách hoạt động</a>
        </div>
      </div>

      {/* Header trang kết quả */}
      <ResultsHeader journeyMode={journeyMode} generatedAt={data.generated_at} isMock={isMock} />

      <nav className="cc-results-jump" aria-label="Đi tới phần kết quả">
        <a href="#decision-lab">01 · SO SÁNH & KIỂM CHỨNG</a>
        <a href="#recommendation-details">02 · XEM CHI TIẾT 5 HƯỚNG</a>
        <a href="#stretch-option">03 · MỞ RỘNG LỰA CHỌN</a>
      </nav>

      {/* Đưa công cụ ra quyết định lên trước danh sách dài để người dùng không bỏ lỡ. */}
      <DecisionLab options={[...data.recommendations, data.stretch]} />

      {/* Danh sách các đề xuất nghề nghiệp chính */}
      <div id="recommendation-details" className="scroll-mt-6 space-y-6 border-t border-[var(--cc-border)] pt-10">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold font-serif text-[var(--cc-ink)]">Các hướng đáng cân nhắc:</h2>
          <span className="text-xs text-[var(--cc-muted)]">Tổng số gợi ý: {data.recommendations.length}</span>
        </div>

        {data.recommendations.length > 0 ? (
          <div className="space-y-6">
            {data.recommendations.map((r, idx) => (
              <RecommendationCard key={r.career_id} rec={r} rank={idx + 1} />
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-[var(--cc-border)] bg-[var(--cc-card-bg)] p-6 text-center text-sm text-[var(--cc-muted)] italic font-serif">
            Chưa có đủ bằng chứng để đề xuất hướng đi. Hãy tiếp tục trò chuyện hoặc bổ sung trải nghiệm, kỹ năng và điều kiện của em.
          </div>
        )}
      </div>

      {/* Gợi ý mở rộng cơ hội học tập & nghề nghiệp (Stretch card) */}
      {data.stretch && (
        <div id="stretch-option" className="scroll-mt-6 space-y-3.5 pt-4 border-t border-[var(--cc-border)]/60">
          <h2 className="text-lg font-bold font-serif text-[var(--cc-ink)]">Vùng mở rộng cơ hội (Stretch Suggestion):</h2>
          <StretchCard rec={data.stretch} />
        </div>
      )}

      {/* Khung Footer ghi chú miễn trừ trách nhiệm */}
      <div className="rounded-xl bg-[var(--cc-primary-soft)]/40 border border-[var(--cc-border)]/50 p-5 text-center text-xs text-[var(--cc-muted)] leading-relaxed font-serif shadow-sm">
        <p className="font-bold text-[var(--cc-ink)] mb-1">Ghi chú định hướng</p>
        <p>{data.disclaimer}</p>
        <div className="flex justify-center gap-4 pt-3.5 text-[10px] uppercase font-bold tracking-wider text-[var(--cc-primary)]">
          <a href={`/explore?mode=${journeyMode}&new=1`} className="hover:underline">Bắt đầu hồ sơ mới</a>
          <span>·</span>
          <a href="/how-it-works" className="hover:underline">Tìm hiểu thuật toán</a>
        </div>
      </div>
    </main>
  );
}
