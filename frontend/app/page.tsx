// Landing page — task F2-06 hoàn thiện. Giao diện vintage, minh bạch và định hướng rõ ràng 2 hành trình.
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { JourneyMode } from "@/types";

export default function LandingPage() {
  const router = useRouter();

  const handleStart = (mode: JourneyMode) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("cc_journey_mode", mode);
    }
    router.push("/explore");
  };

  return (
    <main className="mx-auto max-w-4xl min-h-screen p-6 flex flex-col justify-between space-y-12">
      
      {/* Brand Header */}
      <header className="flex justify-between items-center text-xs font-serif text-[var(--cc-muted)] border-b border-[var(--cc-border)]/40 pb-4">
        <span className="font-bold tracking-widest uppercase text-[var(--cc-ink)] text-sm">🧭 CareerCompass</span>
        <div className="flex gap-4">
          <Link href="/market" className="hover:underline">Thị trường việc làm</Link>
          <span>·</span>
          <Link href="/how-it-works" className="hover:underline">Cách hệ thống hoạt động</Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="text-center space-y-6 max-w-2xl mx-auto py-8">
        <span className="text-5xl block animate-bounce">🧭</span>
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-[var(--cc-ink)] font-serif leading-tight">
          Lộ trình Sự nghiệp của bạn,<br />Khởi hành từ Thực tế.
        </h1>
        <p className="text-base text-[var(--cc-muted)] leading-relaxed">
          Đứng trước bối cảnh mất cân bằng giữa đào tạo và tuyển dụng tại Việt Nam, nhiều bạn trẻ chọn ngành theo xu hướng hoặc kỳ vọng của gia đình mà thiếu đi tín hiệu thị trường thực tế. 
          <b> CareerCompass</b> giúp bạn đối chiếu mong muốn cá nhân với hơn 3.000 tin tuyển dụng thật.
        </p>
      </section>

      {/* Two Journeys Cards */}
      <section className="grid gap-6 md:grid-cols-2">
        
        {/* Card 1: Explore */}
        <div className="rounded-2xl border border-[var(--cc-border)] bg-[var(--cc-card-bg)] p-6 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between space-y-6">
          <div className="space-y-3">
            <span className="text-3xl block">🌱</span>
            <h2 className="text-2xl font-bold font-serif text-[var(--cc-ink)]">Hành trình Khám phá (Explore)</h2>
            <p className="text-xs font-semibold text-[var(--cc-primary)] uppercase tracking-wider">Dành cho Học sinh & Sinh viên năm đầu</p>
            <p className="text-xs text-[var(--cc-muted)] leading-relaxed">
              Trò chuyện để phác thảo hồ sơ sở thích, năng lực và điều kiện cá nhân. Nhận đề xuất lộ trình học tập đa dạng (Đại học, Cao đẳng, Học nghề) và gợi ý mở rộng hướng đi tiềm năng.
            </p>
          </div>
          <button
            onClick={() => handleStart("explore")}
            className="w-full text-center rounded-xl bg-[var(--cc-primary)] py-3 text-xs font-bold text-white shadow hover:opacity-90 transition-all cursor-pointer"
          >
            Khám phá Hướng đi mới ➡️
          </button>
        </div>

        {/* Card 2: Launch */}
        <div className="rounded-2xl border border-[var(--cc-accent)]/60 bg-[var(--cc-accent-soft)] p-6 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between space-y-6">
          <div className="space-y-3">
            <span className="text-3xl block">🚀</span>
            <h2 className="text-2xl font-bold font-serif text-[var(--cc-ink)]">Hành trình Ra mắt (Launch)</h2>
            <p className="text-xs font-semibold text-amber-800 uppercase tracking-wider">Dành cho Sinh viên năm cuối & Tốt nghiệp</p>
            <p className="text-xs text-[var(--cc-muted)] leading-relaxed">
              Khai thác các dự án thực tế, kinh nghiệm và kỹ năng công cụ của bạn. Đối chiếu trực tiếp với các vị trí entry-level, chỉ ra kỹ năng còn thiếu và lên lộ trình tích lũy trong 30 ngày.
            </p>
          </div>
          <button
            onClick={() => handleStart("launch")}
            className="w-full text-center rounded-xl bg-amber-800 py-3 text-xs font-bold text-white shadow hover:bg-amber-900 transition-all cursor-pointer"
          >
            Bứt phá Sự nghiệp ➡️
          </button>
        </div>

      </section>

      {/* 3 Step Guide Section */}
      <section className="rounded-2xl border border-[var(--cc-border)] bg-[var(--cc-card-bg)] p-6 shadow-sm space-y-6">
        <h2 className="text-lg font-bold font-serif text-[var(--cc-ink)] text-center">Định vị hướng đi qua 3 bước đơn giản</h2>
        
        <div className="grid gap-6 md:grid-cols-3 text-center">
          <div className="space-y-2">
            <span className="text-2xl block text-[var(--cc-primary)]">1️⃣</span>
            <p className="font-bold text-sm text-[var(--cc-ink)] font-serif">Trò chuyện cởi mở</p>
            <p className="text-xs text-[var(--cc-muted)] leading-relaxed">Trò chuyện tự nhiên bằng tiếng Việt để chia sẻ về sở thích, dự án đã làm hoặc băn khoăn của bạn.</p>
          </div>

          <div className="space-y-2">
            <span className="text-2xl block text-[var(--cc-primary)]">2️⃣</span>
            <p className="font-bold text-sm text-[var(--cc-ink)] font-serif">Xem hồ sơ live</p>
            <p className="text-xs text-[var(--cc-muted)] leading-relaxed">Hồ sơ năng lực tự động hình thành theo thời gian thực. Bạn có toàn quyền xem và sửa đổi theo ý mình.</p>
          </div>

          <div className="space-y-2">
            <span className="text-2xl block text-[var(--cc-primary)]">3️⃣</span>
            <p className="font-bold text-sm text-[var(--cc-ink)] font-serif">Nhận lộ trình thực tế</p>
            <p className="text-xs text-[var(--cc-muted)] leading-relaxed">Đề xuất 5 nghề nghiệp cùng 1 gợi ý mở rộng, đi kèm bằng chứng trích dẫn, số liệu thị trường và lộ trình cụ thể.</p>
          </div>
        </div>
      </section>

      {/* Ethics & Limits Section */}
      <section className="text-center space-y-2 max-w-xl mx-auto">
        <p className="text-[10px] uppercase font-bold tracking-wider text-[var(--cc-muted)]">Cam kết Đạo đức & Chống Định kiến</p>
        <p className="text-xs text-[var(--cc-muted)] leading-relaxed">
          Chúng tôi không thu thập thông tin giới tính, không lọc cứng vùng miền và luôn đề xuất ít nhất một lộ trình phi đại học cho mỗi nghề nghiệp. Hệ thống hoạt động theo nguyên tắc tôn trọng quyền tự quyết của người dùng.
        </p>
      </section>

      {/* Footer */}
      <footer className="text-center text-xs text-[var(--cc-muted)] border-t border-[var(--cc-border)]/40 pt-4 flex flex-col sm:flex-row justify-between gap-2">
        <p>© 2026 CareerCompass. Mọi gợi ý chỉ mang tính tham khảo, quyết định cuối cùng là của bạn.</p>
        <div className="flex gap-3 justify-center">
          <Link href="/how-it-works" className="underline">Cách hệ thống hoạt động</Link>
          <span>·</span>
          <Link href="/market" className="underline">Bản đồ thị trường</Link>
        </div>
      </footer>

    </main>
  );
}
