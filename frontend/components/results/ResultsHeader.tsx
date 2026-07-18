import type { JourneyMode } from "@/types";

interface ResultsHeaderProps {
  journeyMode: JourneyMode;
  generatedAt?: string;
  isMock?: boolean;
}

export default function ResultsHeader({ journeyMode, generatedAt, isMock = true }: ResultsHeaderProps) {
  const formattedDate = generatedAt
    ? new Date(generatedAt).toLocaleDateString("vi-VN", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";

  return (
    <div className="space-y-3 pb-5 border-b border-[var(--cc-border)]">
      {isMock && (
        <div className="inline-flex items-center gap-2 rounded-lg bg-[var(--cc-accent-soft)] border border-[var(--cc-accent)] px-3.5 py-2 text-xs text-[var(--cc-ink)] font-medium shadow-sm">
          <span className="flex h-2 w-2 rounded-full bg-[var(--cc-accent)] animate-pulse" />
          <span><b>Chế độ Demo:</b> Hiện đang hiển thị dữ liệu mô phỏng. API thật sẽ kết nối sau khi pipeline hoàn tất.</span>
        </div>
      )}
      <div className="flex flex-col md:flex-row md:items-baseline justify-between gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-[var(--cc-ink)] font-serif">
          {journeyMode === "launch" ? "Hành trình Khởi đầu Sự nghiệp" : "Bản đồ Định hướng Nghề nghiệp"}
        </h1>
        {formattedDate && (
          <span className="text-xs text-[var(--cc-muted)] italic font-serif">
            Khởi tạo: {formattedDate}
          </span>
        )}
      </div>
      <p className="text-sm text-[var(--cc-muted)] leading-relaxed">
        {journeyMode === "launch"
          ? "Phân tích mức độ sẵn sàng cho các vị trí khởi điểm (entry-level) dựa trên năng lực, dự án thực tế của bạn và tín hiệu nhu cầu từ thị trường tuyển dụng."
          : "Khám phá nhiều lựa chọn nghề đáng cân nhắc từ sở thích, năng lực có bằng chứng và tín hiệu tuyển dụng; đây không phải kết luận đóng khung em."}
      </p>
    </div>
  );
}
