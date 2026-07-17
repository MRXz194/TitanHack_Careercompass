# 🚀 DEPLOY — checklist cho M1 (task L-03)

> FE = Vercel, BE = Render. Toàn bộ đã verify chạy local end-to-end (mock + live) trước khi viết file này.

## 0. Trạng thái sẵn sàng (M5 bàn giao)

- FE: `npm run test` (61 unit), `npm run typecheck`, `npm run build` — đều xanh.
- BE: `python -m compileall app scripts` + `pytest -q tests` (15 test) — xanh; `/api/health` trả `{"status":"ok",...}`.
- Live FE↔BE đã verify local: chat 2 chiều explore/launch, profile PATCH, error envelope `{"error":{code,message}}` đúng contract §5, timeout 45s có retry UI.
- FE parse lỗi BE qua `lib/api-core.ts`; mock mode vẫn nguyên vẹn (lưới an toàn demo).

## 1. Deploy BE lên Render (~5 phút)

1. Render dashboard → **New + → Blueprint** → chọn repo → Render tự đọc [render.yaml](../render.yaml).
2. Điền env vars khi được hỏi:
   - `CORS_ORIGINS` = `https://<domain-vercel>.vercel.app,http://localhost:3000` (điền lại sau khi có domain FE thật — bước 3)
   - `CHAT_*`/`EMBED_*`: bỏ trống được ở giai đoạn stub; điền khi PR-03 merge (key lấy trong group chat riêng).
3. Chờ deploy xong → mở `https://<app>.onrender.com/api/health` → phải thấy `"status":"ok"`.

⚠️ Free tier Render ngủ sau 15' không có traffic — lần gọi đầu chậm ~30s. Trước demo: mở health URL để đánh thức, hoặc để M1 setup ping 10'/lần.

## 2. Deploy FE lên Vercel (~5 phút)

1. Vercel → **Add New → Project** → import repo → **Root Directory = `frontend`** (quan trọng).
2. Environment Variables:
   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_BASE` | `https://<app>.onrender.com` |
   | `NEXT_PUBLIC_USE_MOCK` | `0` (đổi thành `1` = demo bằng mock khi BE có sự cố) |
3. Deploy → lấy domain → quay lại Render sửa `CORS_ORIGINS` thêm domain này → redeploy BE (Render tự restart khi đổi env).

## 3. Smoke test sau deploy (bắt buộc, 3 phút)

- [ ] `GET /api/health` trên Render: `status: ok`
- [ ] Mở FE → `/explore` → lượt chào xuất hiện (không phải lỗi mạng) → trả lời 2 lượt → profile nhích %
- [ ] `/explore?mode=launch` → câu mở đầu launch khác explore
- [ ] Xóa 1 skill trong profile card → không có banner lỗi đỏ
- [ ] DevTools Console: không có lỗi CORS
- [ ] Đổi `NEXT_PUBLIC_USE_MOCK=1` trên Vercel → redeploy → FE chạy độc lập không cần BE (drill lưới an toàn — làm 1 lần cho biết đường lui)

## 4. Chạy local (nhắc lại nhanh cho thành viên mới)

```bash
# BE (từ backend/, cần .env — copy từ .env.example)
python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# FE (từ frontend/, .env.local: NEXT_PUBLIC_USE_MOCK=0|1)
npm install && npm run dev
```

Lỗi build Next `EXDEV cross-device link` trên Windows/OneDrive → thêm `NEXT_TELEMETRY_DISABLED=1` vào `.env.local`.
