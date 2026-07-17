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
          <h2 className="text-lg font-bold font-serif text-[var(--cc-ink)]">Các gợi ý phù hợp nhất:</h2>
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
            Chưa tìm thấy hướng đi tương thích. Hãy thử thực hiện lại cuộc khảo sát chi tiết hơn.
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

      {/* Panel Nguồn gốc kết quả (Provenance Panel) — Task F2-09 */}
      <div className="rounded-xl border border-[var(--cc-border)] bg-[var(--cc-card-bg)] p-5 space-y-3 shadow-sm">
        <details className="group">
          <summary className="flex justify-between items-center font-serif font-bold text-sm text-[var(--cc-ink)] cursor-pointer list-none focus-visible:outline-none focus:text-[var(--cc-primary)]">
            <span className="flex items-center gap-1.5 select-none">
              🔍 Giải mã kết quả: "Dựa trên gì?" (Result Provenance)
            </span>
            <span className="transition-transform duration-200 group-open:rotate-180 text-xs text-[var(--cc-primary)]">▼</span>
          </summary>
          <div className="mt-4 pt-4 border-t border-[var(--cc-border)]/50 space-y-4 text-xs text-[var(--cc-ink)] leading-relaxed">
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <p className="font-bold text-[var(--cc-primary)] font-serif">1. Các nhân tố tính điểm tương thích</p>
                <ul className="list-inside list-disc space-y-1 text-[var(--cc-muted)]">
                  <li><b>50% Đặc điểm con người:</b> Khớp phổ sở thích và năng lực (Cosine similarity).</li>
                  <li><b>30% Trùng khớp kỹ năng:</b> So khớp kĩ năng bạn có và thị trường cần.</li>
                  <li><b>20% Tín hiệu thị trường:</b> Trọng số nhu cầu tuyển dụng tại vùng ưu tiên.</li>
                </ul>
              </div>
              <div className="space-y-1.5">
                <p className="font-bold text-[var(--cc-primary)] font-serif">2. Nguồn dữ liệu thị trường</p>
                <p className="text-[var(--cc-muted)]">
                  Mức lương phổ biến và số lượng tin tuyển dụng được đối chiếu trực tiếp từ cơ sở dữ liệu tin tuyển dụng CareerCompass quét tại Việt Nam trong 90 ngày gần nhất.
                </p>
                <p className="text-[var(--cc-muted)] italic font-semibold">
                  ℹ {data.recommendations[0]?.market.source_note || "Dữ liệu tin tuyển dụng mẫu."}
                </p>
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-4 pt-3.5 border-t border-dashed border-[var(--cc-border)]/50">
              <div className="space-y-1.5">
                <p className="font-bold text-[var(--cc-primary)] font-serif">3. Quy tắc gợi ý mở rộng (Stretch)</p>
                <p className="text-[var(--cc-muted)]">
                  Gợi ý Stretch Card được hệ thống lựa chọn có chủ đích nằm ngoài cụm sở thích chính của bạn, nhằm kích thích tính tự học và mở rộng cơ hội định hướng thay vì bị đóng khung định kiến.
                </p>
              </div>
              <div className="space-y-1.5">
                <p className="font-bold text-[var(--cc-primary)] font-serif">4. Cam kết bảo mật & Chống bias</p>
                <p className="text-[var(--cc-muted)]">
                  Hệ thống không thu thập hay sử dụng thông tin giới tính hay tên trường để xếp hạng. Dữ liệu trò chuyện được mã hóa theo UUID phiên. Bạn có toàn quyền click "Xóa phiên" để xóa sạch dữ liệu.
                </p>
              </div>
            </div>
          </div>
        </details>
      </div>

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
