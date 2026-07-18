"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { JourneyMode } from "@/types";

const streams = [
  "SOURCE vietnamworks\nREGION hanoi\nSKILL data-analysis\nCONFIDENCE 0.82\nSTATUS observed",
  "PROFILE evidence\nINTEREST systems\nPROJECT dashboard\nCONSTRAINT short-route\nUSER confirmed",
  "CAREER data-analyst\nDEMAND 90d\nSALARY sample-gated\nTREND insufficient\nROUTE certificate",
  "SOURCE itviec\nSKILL react\nSKILL sql\nENTRY signal\nTRACE snapshot-id",
  "POLICY no-gender\nREGION context-only\nSTRETCH required\nAUTONOMY editable\nOUTPUT reference",
  "AGENT inspect\nAGENT clarify\nTOOL market-context\nTOOL research\nFALLBACK deterministic",
];

export default function LandingPage() {
  const router = useRouter();

  const start = (mode: JourneyMode) => {
    localStorage.setItem("cc_journey_mode", mode);
    router.push("/explore");
  };

  return (
    <main>
      <div className="cc-shell">
        <nav className="cc-topbar" aria-label="Điều hướng chính">
          <Link href="/" className="cc-wordmark">CareerCompass</Link>
          <div className="cc-navlinks">
            <Link href="/market" className="cc-nav-optional">Market signals</Link>
            <Link href="/how-it-works" className="cc-nav-optional">Method</Link>
            <button className="cc-button-dark" onClick={() => start("explore")}>EXPLORE</button>
            <button className="cc-button-orange" onClick={() => start("launch")}>GRADUATE LAUNCH</button>
          </div>
        </nav>

        <section className="cc-hero-copy">
          <p className="cc-kicker">VIETNAM / EDUCATION → EMPLOYMENT / DECISION SUPPORT</p>
          <h1>Đừng chọn nghề bằng một <span className="cc-emphasis">phán đoán duy nhất.</span></h1>
          <p>
            CareerCompass đối chiếu điều em đã làm, điều em muốn thử và tín hiệu tuyển dụng quan sát được
            để mở ra nhiều hướng học tập — đại học, cao đẳng, học nghề hoặc chứng chỉ.
          </p>
          <div className="cc-hero-actions">
            <button className="cc-button-dark" onClick={() => start("explore")}>BẮT ĐẦU KHÁM PHÁ</button>
            <Link className="cc-button-ghost" href="/market">ĐỌC TÍN HIỆU THỊ TRƯỜNG</Link>
          </div>
        </section>
      </div>

      <section className="cc-data-panel" aria-label="Minh họa luồng dữ liệu CareerCompass">
        <div className="cc-streams" aria-hidden="true">
          {streams.map((stream) => <pre key={stream}>{`${stream}\n\n${stream}\n\n${stream}`}</pre>)}
        </div>
        <div className="cc-panel-label">
          <p className="cc-kicker">CAREER DECISION ENGINE</p>
          <strong>Hội thoại có cấu trúc. Dữ liệu có nguồn. Quyết định thuộc về em.</strong>
          <div className="cc-human-machine"><span>HUMAN AGENCY</span><span>MACHINE EVIDENCE</span></div>
        </div>
      </section>

      <section className="cc-shell cc-section">
        <div className="cc-section-heading">
          <p className="cc-kicker">ONE CORE / TWO JOURNEYS</p>
          <h2>Từ băn khoăn đến một thử nghiệm nghề nghiệp có thể kiểm chứng.</h2>
          <p>AI hỗ trợ đặt câu hỏi và truy xuất bằng chứng; scoring và các giới hạn đạo đức vẫn do code kiểm soát.</p>
        </div>
        <div className="cc-feature-grid">
          <article className="cc-feature"><h3>01 / Conversation</h3><p>Hồ sơ hình thành qua nhiều lượt trò chuyện và luôn có thể sửa, không phải một bài trắc nghiệm đóng.</p></article>
          <article className="cc-feature"><h3>02 / Market</h3><p>Nhu cầu, kỹ năng, lương và vùng được gắn snapshot, cỡ mẫu, confidence và giới hạn diễn giải.</p></article>
          <article className="cc-feature"><h3>03 / Options</h3><p>Top hướng cân nhắc đi cùng stretch option và lộ trình ngoài đại học để mở rộng agency.</p></article>
          <article className="cc-feature"><h3>04 / Action</h3><p>Sinh viên mới ra trường nhận skill gap có bằng chứng và deliverable 30 ngày thay vì lời khuyên chung chung.</p></article>
        </div>
      </section>

      <section className="cc-dark-band">
        <p>Không thu thập giới tính. Không dùng vùng miền để loại nghề. Không biến mức phù hợp thành bản án tương lai.</p>
      </section>

      <footer className="cc-shell cc-footer">
        <div><span className="cc-status-dot" />SYSTEM DESIGNED FOR TRANSPARENT FALLBACKS</div>
        <div>© 2026 CareerCompass · Gợi ý là tài liệu tham khảo, quyết định là của em.</div>
      </footer>
    </main>
  );
}
