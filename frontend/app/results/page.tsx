"use client";

import { useEffect, useState } from "react";
import { fetchRecommendations } from "@/lib/api";
import type { RecommendationResponse, JourneyMode } from "@/types";
import ResultsHeader from "@/components/results/ResultsHeader";
import RecommendationCard from "@/components/results/RecommendationCard";
import StretchCard from "@/components/results/StretchCard";

export default function ResultsPage() {
  const [data, setData] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [journeyMode, setJourneyMode] = useState<JourneyMode>("explore");

  useEffect(() => {
    // Đọc chế độ hành trình từ LocalStorage
    const savedMode = typeof window !== "undefined" ? localStorage.getItem("cc_journey_mode") as JourneyMode : null;
    const mode = savedMode === "launch" ? "launch" : "explore";
    setJourneyMode(mode);

    setLoading(true);
    fetchRecommendations(mode)
      .then((res) => {
        setData(res);
        // Nếu đề xuất đầu tiên có trường job_readiness (không null), chắc chắn là Launch mode
        if (res.recommendations?.[0]?.job_readiness) {
          setJourneyMode("launch");
        }
      })
      .catch((err) => {
        console.error(err);
        setError("Không thể tải kết quả định hướng của em. Vui lòng kiểm tra lại kết nối mạng hoặc thử lại từ màn hình khảo sát.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const isMock = process.env.NEXT_PUBLIC_USE_MOCK === "1";

  if (loading) {
    return (
      <main className="mx-auto max-w-3xl min-h-screen p-6 flex flex-col justify-center items-center space-y-4">
        <div className="relative flex items-center justify-center">
          {/* Vòng xoay spinner mang phong cách tối giản, vintage */}
          <div className="w-12 h-12 rounded-full border-4 border-[var(--cc-border)] border-t-[var(--cc-primary)] animate-spin" />
          <span className="absolute text-lg">🧭</span>
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
        <span className="text-4xl">📯</span>
        <h2 className="text-xl font-bold font-serif text-[var(--cc-ink)]">Đã xảy ra sự cố nhỏ</h2>
        <p className="text-sm text-[var(--cc-muted)] max-w-md leading-relaxed">
          {error || "Không tìm thấy dữ liệu phiên khảo sát. Hãy đảm bảo em đã hoàn thành cuộc hội thoại trước."}
        </p>
        <div className="flex gap-4 pt-2">
          <a
            href="/"
            className="rounded-xl border border-[var(--cc-border)] bg-white px-5 py-2.5 text-xs font-semibold text-[var(--cc-ink)] hover:bg-slate-50 shadow-sm font-serif"
          >
            Quay về Trang chủ
          </a>
          <a
            href="/explore"
            className="rounded-xl bg-[var(--cc-primary)] px-5 py-2.5 text-xs font-semibold text-white hover:opacity-90 shadow-sm"
          >
            Bắt đầu khảo sát lại
          </a>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl min-h-screen p-6 space-y-6">
      {/* Menu đầu trang phong cách vintage cuốn nhật ký */}
      <div className="flex justify-between items-center text-xs font-serif text-[var(--cc-muted)] border-b border-[var(--cc-border)]/40 pb-2.5">
        <a href="/" className="hover:text-[var(--cc-primary)] transition-all font-bold tracking-widest uppercase">
          🧭 CareerCompass
        </a>
        <div className="flex gap-3">
          <a href="/market" className="hover:underline">Thị trường việc làm</a>
          <span>·</span>
          <a href="/how-it-works" className="hover:underline">Cách hoạt động</a>
        </div>
      </div>

      {/* Header trang kết quả */}
      <ResultsHeader journeyMode={journeyMode} generatedAt={data.generated_at} isMock={isMock} />

      {/* Danh sách các đề xuất nghề nghiệp chính */}
      <div className="space-y-6">
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
        <div className="space-y-3.5 pt-4 border-t border-[var(--cc-border)]/60">
          <h2 className="text-lg font-bold font-serif text-[var(--cc-ink)]">Vùng mở rộng cơ hội (Stretch Suggestion):</h2>
          <StretchCard rec={data.stretch} />
        </div>
      )}

      {/* Khung Footer ghi chú miễn trừ trách nhiệm */}
      <div className="rounded-xl bg-[var(--cc-primary-soft)]/40 border border-[var(--cc-border)]/50 p-5 text-center text-xs text-[var(--cc-muted)] leading-relaxed font-serif shadow-sm">
        <p className="font-bold text-[var(--cc-ink)] mb-1">✍ Ghi chú Định hướng Quan trọng</p>
        <p>{data.disclaimer}</p>
        <div className="flex justify-center gap-4 pt-3.5 text-[10px] uppercase font-bold tracking-wider text-[var(--cc-primary)]">
          <a href="/explore" className="hover:underline">↩ Làm lại khảo sát</a>
          <span>·</span>
          <a href="/how-it-works" className="hover:underline">ℹ Tìm hiểu thuật toán</a>
        </div>
      </div>
    </main>
  );
}
