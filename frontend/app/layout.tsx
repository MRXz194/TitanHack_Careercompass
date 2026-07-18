import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CareerCompass — La bàn hướng nghiệp từ dữ liệu tuyển dụng",
  description:
    "Khám phá nhiều hướng học tập và nghề nghiệp dựa trên bằng chứng cá nhân cùng tín hiệu tuyển dụng quan sát được tại Việt Nam.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
