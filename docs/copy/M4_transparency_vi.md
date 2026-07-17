# M4 · PR-09 — Copy minh bạch (canonical)

> Nguồn runtime: `frontend/lib/copy/transparency.ts` (`transparency-v1`).  
> File này đồng bộ ý nghĩa cho pitch / M6; **sửa copy thì sửa TS trước**, rồi cập nhật tóm tắt dưới đây.

## Trang chính (`/how-it-works`) — ≤300 từ

**Tiêu đề:** Cách CareerCompass hoạt động

CareerCompass giúp bạn khám phá hướng học/nghề (Explore) hoặc chuẩn bị tìm việc entry-level (Launch). Đây là công cụ tham khảo — quyết định cuối cùng luôn là của bạn.

1. **Dữ liệu thị trường** — Tin tuyển dụng snapshot ~90 ngày; “Radar nhu cầu kỹ năng” = tín hiệu cầu tuyển dụng, không kết luận “thiếu người” nếu chưa có dữ liệu cung.
2. **Hồ sơ từ hội thoại** — Hồ sơ hiện dần từ câu trả lời, sửa được; không ô giới tính; vùng không phải bộ lọc cứng.
3. **Cách gợi ý được xếp** — Ưu tiên khớp hồ sơ, market có trần; ≥1 lộ trình ngoài đại học; có gợi ý mở rộng lựa chọn.
4. **Explore / Launch** — Explore: nghề + lộ trình học. Launch: kỹ năng có/thiếu evidence, mức sẵn sàng (không phải xác suất trúng tuyển), việc 30 ngày có deliverable.
5. **Giới hạn** — Không chấm CV, không nộp đơn hộ, không hứa việc/lương cá nhân; bạn sửa hồ sơ và xóa phiên được.

**Footer:** Gợi ý chỉ mang tính tham khảo — quyết định là của bạn.

## Tooltips (dùng lại trên UI)

| Key | Nhãn | Nội dung ngắn |
|---|---|---|
| demand_proxy | Radar nhu cầu kỹ năng | Xếp theo tin tuyển snapshot, không đo “thiếu người”. |
| match_score | Độ phù hợp | Ưu tiên hồ sơ bạn; không phải “nghề tốt nhất”. |
| stretch | Có thể bạn chưa nghĩ tới | Mở rộng lựa chọn, vẫn là tham khảo. |
| region_pref | Vùng ưu tiên | Đổi context thị trường; không loại nghề. |
| readiness_band | Mức sẵn sàng (Launch) | Chuẩn bị hồ sơ, không phải xác suất được tuyển. |
| source_note | Nguồn số liệu | Mọi số có nguồn; dữ liệu mỏng thì nói rõ. |

## Cấm overclaim

Không dùng: AI biết hơn / chắc chắn có việc / nghề tốt nhất / phán quyết / xác suất được tuyển / thiếu người (từ posting đơn thuần).
