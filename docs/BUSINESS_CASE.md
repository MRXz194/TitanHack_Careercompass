# BUSINESS CASE — CareerCompass giải quyết vấn đề gì trong thực tế?

## 1. Khách hàng và người dùng

- **Người dùng chính:** (a) học sinh lớp 10–12/sinh viên đầu khóa đang chọn hướng học; (b) sinh viên năm cuối hoặc mới tốt nghiệp cần chuyển từ ngành học sang nhóm việc entry-level khả thi.
- **Người dùng hỗ trợ:** giáo viên chủ nhiệm, tư vấn viên hướng nghiệp, phụ huynh.
- **Khách hàng trả tiền tiềm năng:** trường THPT/ĐH, trung tâm hướng nghiệp, sở/đơn vị giáo dục và chương trình CSR phát triển nhân lực địa phương.

MVP không cố bán hàng trong 48 giờ. Nó chứng minh hai workflow dùng chung một data/AI core:

1. **Explore:** khám phá nghề và route học cho học sinh/sinh viên chưa chốt hướng.
2. **Launch:** chuyển năng lực, project và ngành học của sinh viên sắp/đã tốt nghiệp thành nhóm việc entry-level, skill gap và kế hoạch chuẩn bị 30 ngày.

Tư vấn viên dùng output làm điểm bắt đầu cho buổi tư vấn, không dùng nó như phán quyết tự động.

## 2. Bài toán hiện tại của tổ chức giáo dục

| Hiện trạng | Hệ quả | CareerCompass xử lý trong MVP |
|---|---|---|
| Một tư vấn viên phục vụ nhiều học sinh, thời gian 1:1 ít | Tư vấn thường chung chung hoặc dựa trên bài test tĩnh | Hội thoại adaptive tạo bản nháp hồ sơ trước buổi tư vấn |
| Thông tin nghề, lương và kỹ năng nằm rời rạc | Khó nối “mình hợp gì” với “thị trường cần gì” | Evidence Card nối tín hiệu cá nhân với dữ liệu tuyển dụng |
| Đại học thường là lộ trình mặc định | Bỏ sót cao đẳng, trung cấp nghề, chứng chỉ | Mỗi nghề có ít nhất 2 route, luôn có route ngoài đại học |
| Khó giải thích vì sao hệ thống gợi ý | Thiếu niềm tin, rủi ro bias | Profile có thể sửa, evidence truy vết, counterfactual, bias audit |
| Báo cáo thị trường nhanh lỗi thời | Chương trình đào tạo phản ứng chậm | Pipeline tái chạy được; MVP dùng snapshot có ngày và nguồn rõ |
| Sinh viên biết tên ngành nhưng không biết tìm job title nào | Tìm việc bằng từ khóa hẹp, bỏ lỡ vai trò lân cận | Launch mode map project/skill → 3–5 nhóm việc entry-level + search queries |
| “Thiếu kinh nghiệm” được hiểu quá chung chung | Học lan man, CV/project không chứng minh được skill tuyển dụng | Skill evidence + missing-skill roadmap + deliverable 30 ngày |

## 3. Job-to-be-done và lời hứa sản phẩm

> Khi một người học chưa rõ nên học gì hoặc bắt đầu tìm việc từ đâu, CareerCompass giúp họ biến trải nghiệm thật thành một tập lựa chọn có thể giải thích, đối chiếu với tín hiệu tuyển dụng gần đây và nhìn thấy bước tiếp theo khả thi — để họ và tư vấn viên có một cuộc trao đổi tốt hơn.

CareerCompass **không** tuyển dụng, không dự đoán thành công, không thay tư vấn viên và không khẳng định một nghề là “đúng nhất”.

### Buyer map và quyết định mua/pilot

| Actor | Pain/goal | Điều họ cần thấy trước pilot |
|---|---|---|
| Ban giám hiệu/phòng CTSV | tăng độ phủ hướng nghiệp, hỗ trợ chuyển tiếp việc làm | privacy, counselor oversight, usefulness và chi phí/session |
| Tư vấn viên/giảng viên | giảm thời gian khám phá cơ bản, có evidence để hỏi sâu | output không phán quyết, sửa được, source/confidence rõ |
| Khoa/trường nghề | hiểu skill demand để cập nhật workshop/module | data provenance, coverage/limitations; không gọi proxy là shortage |
| Học sinh/sinh viên | rõ lựa chọn và bước tiếp theo | tiếng Việt dễ hiểu, route đa dạng, autonomy, không thu PII |

### Workflow trước và sau

```text
Trước: form/test tĩnh → tư vấn viên đọc thủ công → tra thị trường rời rạc → lời khuyên khó truy vết
Sau: 8–10 phút hội thoại → profile/evidence user sửa → market-grounded options → tư vấn viên review/thảo luận → action cụ thể
```

CareerCompass tạo **decision-support artifact**, không tự động ra quyết định. Giá trị vận hành cần đo ở pilot: thời gian chuẩn bị/buổi, tỷ lệ học sinh hoàn thành trước tư vấn, số lựa chọn mới và mức counselor chấp nhận output.

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
| Launch usefulness | Sinh viên tìm được ≥2 job-title/query mới và 1 action thực hiện được trong 7 ngày | ≥60% người test launch |

Mẫu test nhỏ chỉ là **tín hiệu pilot**, không được pitch như nghiên cứu đại diện cho học sinh Việt Nam.

## 5. Lợi thế có thể bảo vệ

1. Taxonomy kỹ năng Việt–Anh và pipeline chuẩn hóa dữ liệu tuyển dụng Việt Nam.
2. Explainability hai chiều: lời người học + tín hiệu tuyển dụng, không chỉ một “điểm phù hợp”.
3. Guardrail mở rộng lựa chọn được kiểm bằng code và paired tests.
4. Workflow hỗ trợ tư vấn viên thay vì cố thay thế họ.
5. Một profile có thể phục vụ cả quyết định học tập và chuyển tiếp sang việc làm, giảm đứt gãy giữa “học ngành gì” và “ứng tuyển vai trò nào”.

## 5.1. Mô hình triển khai/kinh doanh giả thuyết

- Học sinh/sinh viên dùng miễn phí trong pilot.
- B2B SaaS theo trường/cohort cho counselor workflow và aggregate report, chỉ sau privacy/RBAC/consent.
- Dịch vụ insight chương trình đào tạo chỉ dùng aggregate đủ mẫu; không bán dữ liệu hội thoại cá nhân.
- Hackathon **không chứng minh willingness-to-pay**; slide business model phải ghi đây là hypothesis cần validate.

### Rủi ro business cần kiểm chứng

- Counselor có tin/đưa output vào quy trình không?
- Sinh viên có hoàn thành action sau 7 ngày hay chỉ xem recommendation?
- Trường có quyền sử dụng/retention data phù hợp không?
- Coverage hiring data có đủ cho ngành phi-IT/vùng ngoài đô thị không?
- Chi phí LLM/session và vận hành data có phù hợp quy mô cohort không?

## 6. Pilot sau hackathon

- 1 trường, 2 tư vấn viên, 20–30 học sinh + 15–20 sinh viên năm cuối/mới tốt nghiệp trong 2 tuần.
- Đo trước/sau: độ rõ hướng đi, số lựa chọn mới, mức tin cậy và ý định trao đổi với tư vấn viên.
- Tư vấn viên review 20 output: hợp lý, có bằng chứng, không đóng khung, route khả thi.
- Với launch cohort: đo số job title mới, mức rõ skill gap, tỷ lệ hoàn thành action đầu tiên sau 7 ngày; không hứa tăng tỷ lệ có việc chỉ từ pilot ngắn.
- Không lưu hội thoại dài hạn nếu chưa có consent và chính sách dữ liệu của trường.
