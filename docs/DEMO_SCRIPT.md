# 🎤 DEMO SCRIPT & Pitch — hoàn thiện ở Phase 5 (H+40→46)

## Cấu trúc pitch (mục tiêu ≤ 10 slide, demo live là trung tâm)

1. **Problem (30s):** 1 con số thật về mismatch cung-cầu lao động VN + 1 câu chuyện học sinh chọn nghề theo "trend/gia đình".
2. **Demo live (4 phút)** — theo user journey trong PLAN.md §2. Persona: *Minh, lớp 12, Quảng Nam, thích vẽ + hay sửa đồ điện, nhà không dư dả* → hệ thống gợi ý cả nghề kỹ thuật (route trung cấp nghề) lẫn hướng sáng tạo, kèm dữ liệu Đà Nẵng thật.
3. **Differentiators (60s):** Radar nhu cầu kỹ năng theo vùng (hiring-demand proxy, không overclaim supply gap) · Evidence 2 chiều + counterfactual · Anti-bias by design.
4. **Data & kiến trúc (45s):** N postings thật, pipeline chạy lại được mỗi đêm → real-time là thêm scheduler, không viết lại (slide từ ARCHITECTURE.md §5).
5. **Future (30s):** counselor view, tích hợp trường học, mở rộng nguồn data.

## Persona demo (seed sẵn, có cached-replay — L-08)

| | Persona A — "Minh" | Persona B — "Lan" |
|---|---|---|
| Bối cảnh | Lớp 12, Quảng Nam, thích vẽ + sửa đồ điện, tài chính hạn chế | Lớp 11, Hà Nội, giỏi toán, thích nói chuyện với người, gia đình ép học Y |
| Điểm demo | Route vocational nổi bật, Skill Gap Đà Nẵng | Stretch card + counterfactual + autonomy (sửa profile) |

## Câu hỏi judge dự đoán — chuẩn bị trả lời (phân công tại H+44)

1. "Số liệu này lấy đâu ra? Tin được không?" → nguồn crawl, N postings, ngày crawl, mở file report normalize.
2. "Khác gì trắc nghiệm MBTI/Holland online?" → hội thoại adaptive + dữ liệu thị trường thật + explainable + sửa được profile.
3. "Chứng minh không bias giới?" → schema không có field giới tính (mở code) + kết quả bias test (mở BIAS_AUDIT.md).
4. "Học sinh nông thôn ít nghề ở địa phương thì sao?" → region không lọc nghề, chỉ bổ sung thông tin; gợi ý vẫn đủ rộng + route học từ xa/nghề.
5. "Sao chỉ 3 thành phố?" → giới hạn 48h; pipeline thêm vùng = thêm query crawl.
6. "LLM bịa thì sao?" → evidence chỉ được diễn đạt số từ stats, có regex check + fallback template (mở AI_DESIGN.md §4).
7. "Business model?" → freemium học sinh, B2B trường học/trung tâm hướng nghiệp, báo cáo thị trường cho trường nghề.
8. "Scale thế nào?" → ARCHITECTURE.md §5, mỗi thành phần có đường thăng cấp.
9. "Posting nhiều có nghĩa thị trường thiếu người không?" → Không. Đây là observed hiring demand; UI có sample/confidence. Đo skill shortage thật cần thêm dữ liệu supply/time-to-fill — đó là phase pilot.
10. "Doanh nghiệp/trường học được lợi gì?" → học sinh có bản nháp có bằng chứng trước buổi tư vấn; tư vấn viên dùng thời gian 1:1 cho thảo luận sâu, không làm lại bước khám phá cơ bản.

## Checklist trước giờ demo

- [ ] Video backup demo đã quay (phòng wifi chết)
- [ ] `DEMO_MODE=replay` test hoạt động
- [ ] Máy demo: tắt notification, zoom browser 125%, bookmark sẵn các trang
- [ ] Demo script in giấy, phân vai ai nói – ai điều khiển máy
