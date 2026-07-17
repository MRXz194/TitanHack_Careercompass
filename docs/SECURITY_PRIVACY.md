# SECURITY & PRIVACY — mức tối thiểu cho sản phẩm dùng với học sinh

## 1. Nguyên tắc

- Không thu tên thật, email, số điện thoại, trường cụ thể, địa chỉ chi tiết, giới tính hoặc học bạ trong MVP.
- Dùng session ID ngẫu nhiên; UI nói rõ đây là bản demo và không nhập thông tin nhận dạng.
- Hội thoại chỉ phục vụ profile phiên hiện tại, không dùng để train/fine-tune.
- Tư vấn nghề là hỗ trợ quyết định, không phải quyết định tự động có hậu quả học vụ.

## 2. Retention demo

- Nút “Xóa phiên” xóa localStorage và session server.
- Session server có TTL mục tiêu 24 giờ; xóa `sessions.db` sau hackathon/pilot nếu chưa có consent khác.
- Log chỉ model, token, latency, status, request ID; không log raw message/profile.
- Replay fixtures chỉ dùng persona hư cấu, không dùng transcript người test thật.

## 3. Guardrail input/LLM

- Giới hạn độ dài message và số lượt/session; rate limit endpoint chat.
- User text luôn là dữ liệu, không được phép ghi đè system instruction.
- Structured output + Pydantic validation; React không render HTML từ LLM.
- LLM lỗi/timeout → fallback, không leak stack, key hoặc provider response.
- Nếu user nêu khủng hoảng/tự hại: không dùng hướng nghiệp như giải pháp; trả safety copy và khuyến khích tìm người lớn/chuyên gia phù hợp.

## 4. Dữ liệu tuyển dụng và quyền sử dụng

- Trước khi crawl, M1/M2 kiểm tra robots.txt/điều khoản; ưu tiên API, dataset mở hoặc dữ liệu được phép dùng.
- Không vượt access control, CAPTCHA hoặc đăng nhập; không crawl dữ liệu ứng viên/cá nhân.
- Rate limit lịch sự, dừng khi 403/429.
- Lưu provenance: source, URL, crawled_at, snapshot count; UI chỉ hiện aggregate và attribution, không republish toàn bộ mô tả việc làm.
- Nếu nguồn không cho phép automation hoặc điều khoản không rõ, dùng public dataset/seed có license rõ và nói trung thực trong pitch.

## 5. Checklist release

- [ ] Không secret trong git history/diff
- [ ] Production CORS chỉ có FE origin
- [ ] Session delete/TTL hoạt động hoặc demo disclaimer nêu rõ
- [ ] Không raw PII trong log, replay, screenshot, pitch
- [ ] Source manifest + attribution + limitation có trên UI/report
- [ ] Dependency và endpoint smoke test pass
