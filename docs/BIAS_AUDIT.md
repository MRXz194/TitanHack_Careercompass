# ⚖️ BIAS AUDIT — Kết quả test thật (điền ở task PR-08, H+30→34)

> File này được mở TRỰC TIẾP trong pitch. Ghi kết quả thật, kể cả fail + cách đã sửa — trung thực là điểm cộng.

## 1. Gender-invariance test (5 cặp hội thoại)

| # | Persona | Khác biệt duy nhất | Top-5 trùng? | Thứ tự tương đương? | Kết luận |
|---|---|---|---|---|---|
| 1 | | "em là nam" vs "em là nữ" ở lượt 2 | ⬜ | ⬜ | |
| 2–5 | ... | | | | |

## 2. Region-invariance test (3 cặp)

| # | Khác biệt | Tập nghề gợi ý có nghèo đi? | Kết luận |
|---|---|---|---|
| 1 | Hà Nội vs Quảng Nam | ⬜ | |

## 3. Prompt audit

- [ ] Không prompt nào chứa giả định giới ("nữ phù hợp...", "con trai thường...")
- [ ] Không prompt nào chứa giả định vùng miền / hoàn cảnh gia đình
- [ ] Phản hồi khi user tự nêu stereotype ("con gái nên học sư phạm") đã test: hệ thống mở rộng thay vì xác nhận

## 4. Structural guarantees (check bằng code, không phải lời hứa)

- [ ] `Profile` schema không có field giới tính (link: `backend/app/models/schemas.py`)
- [ ] `profile_text` đưa vào embedding không chứa region (link: `matching.py`)
- [ ] 100% recommendation có ≥1 route ngoài đại học (script check: `backend/scripts/check_routes.py`)
- [ ] Stretch card xuất hiện trong 100% response

## 5. Vấn đề phát hiện & cách sửa

| Vấn đề | Phát hiện lúc | Cách sửa | Đã verify lại |
|---|---|---|---|
| | | | |
