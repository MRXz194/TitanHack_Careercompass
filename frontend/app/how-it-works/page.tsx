// Trang "Cách hệ thống hoạt động" — minh bạch = trust (task PR-09 viết nội dung, F2-06 render).
export default function HowItWorksPage() {
  return (
    <main className="mx-auto max-w-2xl space-y-4 p-6">
      <h1 className="text-2xl font-bold">Cách CareerCompass hoạt động</h1>
      <p className="text-[var(--cc-muted)]">
        (Nội dung thật do task PR-09 viết — dưới đây là khung)
      </p>
      <ul className="list-inside list-disc space-y-2 text-sm">
        <li><b>Dữ liệu:</b> tin tuyển dụng thật từ các trang việc làm Việt Nam, 90 ngày gần nhất.</li>
        <li><b>Hồ sơ của em:</b> hình thành từ chính câu trả lời của em — em xem được và sửa được.</li>
        <li><b>Gợi ý:</b> kết hợp mức phù hợp với em (quan trọng nhất) và tín hiệu thị trường.</li>
        <li><b>Không hỏi giới tính:</b> hệ thống không dùng giới tính hay quê quán để loại bất kỳ nghề nào.</li>
        <li><b>Giới hạn:</b> gợi ý là tài liệu tham khảo, không phải phán quyết — quyết định là của em.</li>
      </ul>
    </main>
  );
}
