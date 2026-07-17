import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CareerCompass — La bàn hướng nghiệp từ dữ liệu thật",
  description:
    "Khám phá hướng đi phù hợp với em — dựa trên năng lực, sở thích và dữ liệu thị trường lao động Việt Nam.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
