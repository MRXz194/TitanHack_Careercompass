# BUSINESS CASE — CareerCompass giải quyết vấn đề gì trong thực tế?

## 1. Khách hàng và người dùng

- **Người dùng chính:** học sinh lớp 10–12, sinh viên năm đầu đang thiếu thông tin để chọn hướng học/nghề.
- **Người dùng hỗ trợ:** giáo viên chủ nhiệm, tư vấn viên hướng nghiệp, phụ huynh.
- **Khách hàng trả tiền tiềm năng:** trường THPT/ĐH, trung tâm hướng nghiệp, sở/đơn vị giáo dục và chương trình CSR phát triển nhân lực địa phương.

MVP không cố bán hàng trong 48 giờ. Nó chứng minh một workflow có thể pilot: học sinh tự khám phá 8–10 phút, nhận hồ sơ có thể sửa và gợi ý có bằng chứng; tư vấn viên dùng kết quả đó làm điểm bắt đầu cho buổi tư vấn, không dùng nó như phán quyết tự động.

## 2. Bài toán hiện tại của tổ chức giáo dục

| Hiện trạng | Hệ quả | CareerCompass xử lý trong MVP |
|---|---|---|
| Một tư vấn viên phục vụ nhiều học sinh, thời gian 1:1 ít | Tư vấn thường chung chung hoặc dựa trên bài test tĩnh | Hội thoại adaptive tạo bản nháp hồ sơ trước buổi tư vấn |
| Thông tin nghề, lương và kỹ năng nằm rời rạc | Khó nối “mình hợp gì” với “thị trường cần gì” | Evidence Card nối tín hiệu cá nhân với dữ liệu tuyển dụng |
| Đại học thường là lộ trình mặc định | Bỏ sót cao đẳng, trung cấp nghề, chứng chỉ | Mỗi nghề có ít nhất 2 route, luôn có route ngoài đại học |
| Khó giải thích vì sao hệ thống gợi ý | Thiếu niềm tin, rủi ro bias | Profile có thể sửa, evidence truy vết, counterfactual, bias audit |
| Báo cáo thị trường nhanh lỗi thời | Chương trình đào tạo phản ứng chậm | Pipeline tái chạy được; MVP dùng snapshot có ngày và nguồn rõ |

## 3. Job-to-be-done và lời hứa sản phẩm

> Khi một học sinh chưa biết nên đi hướng nào, CareerCompass giúp em biến trải nghiệm thật của mình thành một tập lựa chọn nghề có thể giải thích, đối chiếu với tín hiệu tuyển dụng gần đây và nhìn thấy nhiều lộ trình học khả thi — để em và tư vấn viên có một cuộc trao đổi tốt hơn.

CareerCompass **không** tuyển dụng, không dự đoán thành công, không thay tư vấn viên và không khẳng định một nghề là “đúng nhất”.

## 4. Chỉ số chứng minh giá trị

**North-star pilot:** tỷ lệ học sinh tạo được ít nhất 2 hướng đi mới đáng cân nhắc và giải thích lại được vì sao chúng xuất hiện.

| Nhóm | Chỉ số | Ngưỡng pass MVP |
|---|---|---|
| Hữu ích | “Giúp em hiểu lựa chọn hơn” | trung vị ≥4/5 trên ≥5 người test |
| Mở rộng lựa chọn | Có ≥1 nghề/route mới sẵn sàng tìm hiểu | ≥60% người test |
| Tin cậy | Tìm được nguồn/giải thích cho một con số | ≥80% hoàn thành task |
| Tư vấn viên | Output dùng được để mở đầu buổi tư vấn | ≥1/2 người test xác nhận, ghi caveat |
| Hoàn thành flow | Bắt đầu chat → xem recommendations | ≥80% trong test có quan sát |
| Thời gian | Persona demo / trải nghiệm thật | ≤4 phút / ≤10 phút |

Mẫu test nhỏ chỉ là **tín hiệu pilot**, không được pitch như nghiên cứu đại diện cho học sinh Việt Nam.

## 5. Lợi thế có thể bảo vệ

1. Taxonomy kỹ năng Việt–Anh và pipeline chuẩn hóa dữ liệu tuyển dụng Việt Nam.
2. Explainability hai chiều: lời người học + tín hiệu tuyển dụng, không chỉ một “điểm phù hợp”.
3. Guardrail mở rộng lựa chọn được kiểm bằng code và paired tests.
4. Workflow hỗ trợ tư vấn viên thay vì cố thay thế họ.

## 6. Pilot sau hackathon

- 1 trường, 2 tư vấn viên, 30–50 học sinh trong 2 tuần.
- Đo trước/sau: độ rõ hướng đi, số lựa chọn mới, mức tin cậy và ý định trao đổi với tư vấn viên.
- Tư vấn viên review 20 output: hợp lý, có bằng chứng, không đóng khung, route khả thi.
- Không lưu hội thoại dài hạn nếu chưa có consent và chính sách dữ liệu của trường.
