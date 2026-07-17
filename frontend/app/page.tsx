// Landing page — task F2-06 hoàn thiện. Skeleton này để cả team thấy app chạy từ giờ đầu.
import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-6 px-6 text-center">
      <span className="text-5xl">🧭</span>
      <h1 className="text-4xl font-bold tracking-tight">CareerCompass</h1>
      <p className="text-lg text-[var(--cc-muted)]">
        Chọn nghề bằng dữ liệu thật, không phải cảm tính. Trò chuyện vài phút để khám phá
        các hướng đi phù hợp với <b>chính em</b> — kèm số liệu thị trường lao động Việt Nam.
      </p>
      <div className="flex gap-4">
        <Link
          href="/explore"
          className="rounded-xl bg-[var(--cc-primary)] px-6 py-3 font-semibold text-white shadow hover:opacity-90"
        >
          Bắt đầu khám phá
        </Link>
        <Link
          href="/market"
          className="rounded-xl border border-slate-300 px-6 py-3 font-semibold hover:bg-white"
        >
          Xem thị trường việc làm
        </Link>
      </div>
      <p className="text-sm text-[var(--cc-muted)]">
        Gợi ý chỉ mang tính tham khảo — quyết định luôn là của em. ·{" "}
        <Link href="/how-it-works" className="underline">
          Cách hệ thống hoạt động
        </Link>
      </p>
    </main>
  );
}
