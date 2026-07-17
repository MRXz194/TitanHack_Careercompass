import Link from "next/link";
import { PAGE } from "@/lib/copy/transparency";

export default function HowItWorksPage() {
  return (
    <main className="mx-auto max-w-2xl min-h-screen p-6 space-y-6">
      {/* Menu đầu trang */}
      <div className="flex justify-between items-center text-xs font-serif text-[var(--cc-muted)] border-b border-[var(--cc-border)]/40 pb-2.5">
        <Link href="/" className="hover:text-[var(--cc-primary)] transition-all font-bold tracking-widest uppercase">
          🧭 CareerCompass
        </Link>
        <div className="flex gap-3">
          <Link href="/explore" className="hover:underline">Bắt đầu khảo sát</Link>
          <span>·</span>
          <Link href="/market" className="hover:underline">Thị trường việc làm</Link>
        </div>
      </div>

      {/* Tiêu đề chính */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-[var(--cc-ink)] font-serif">
          {PAGE.title}
        </h1>
        <p className="text-sm text-[var(--cc-muted)] leading-relaxed font-serif italic">
          {PAGE.intro}
        </p>
      </div>

      {/* Danh sách các phần thuyết minh hoạt động */}
      <div className="space-y-5 pt-4 border-t border-[var(--cc-border)]/40">
        {PAGE.sections.map((section) => (
          <section key={section.id} className="space-y-1.5">
            <h2 className="text-base font-bold font-serif text-[var(--cc-primary)]">
              ✦ {section.heading}
            </h2>
            <p className="text-xs sm:text-sm text-[var(--cc-ink)] leading-relaxed bg-[var(--cc-card-bg)] border border-[var(--cc-border)] p-4 rounded-xl shadow-sm">
              {section.body}
            </p>
          </section>
        ))}
      </div>

      {/* Tuyên bố Đạo đức và Bản quyền */}
      <div className="rounded-xl bg-[var(--cc-accent-soft)] border border-[var(--cc-accent)]/30 p-5 text-center text-xs text-[var(--cc-muted)] leading-relaxed font-serif shadow-sm">
        <p className="font-bold text-[var(--cc-ink)] mb-1">✍ Tuyên bố Định hướng & Quyền riêng tư</p>
        <p>{PAGE.footer}</p>
        <p className="mt-2 text-[10px] text-[var(--cc-muted)]">
          Báo cáo này được cấu trúc theo bộ quy tắc bảo vệ học sinh của CareerCompass. Thông tin phiên trò chuyện được mã hóa theo UUID tạm thời, tự động xóa sau 24h và bạn có toàn quyền click nút "Xóa phiên" để xóa sạch dữ liệu ngay lập tức.
        </p>
      </div>
    </main>
  );
}
