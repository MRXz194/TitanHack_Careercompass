# DEPLOY — L-03 deploy skeleton + L-02 GitHub guardrails checklist

> Production target hiện tại: Vercel + Railway. Runbook copy-paste và env matrix mới nằm tại `docs/DEPLOY_VERCEL_RAILWAY.md`. Phần Render bên dưới được giữ làm fallback.

> M1 sở hữu file này. Checklist dưới đây là thao tác bấm tay trong GitHub/Vercel/Render UI —
> không tự động hoá được từ CLI trong môi trường build hiện tại vì cần credentials cá nhân
> của leader. Điền URL/kết quả thật vào cuối file sau khi xong, và tick lại `docs/PREFLIGHT.md`.

## A. GitHub guardrails (L-02)

Artefact đã có sẵn trong repo: `.github/CODEOWNERS`, `.github/ISSUE_TEMPLATE/`, `.github/labels.yml`
(danh sách tham chiếu — GitHub không tự import label từ YAML trên free plan, tạo tay theo bảng đó).

1. **Branch protection**: repo → Settings → Branches → Add rule → branch name pattern `main`.
   - [ ] Require a pull request before merging (require 1 approval).
   - [ ] Require status checks to pass before merging → chọn `backend` và `frontend` (từ `ci.yml`) — cần mở ít nhất 1 PR trước để 2 check này xuất hiện trong danh sách.
   - [ ] Do not allow bypassing the above settings (bỏ qua nếu free plan không có, dùng convention "chỉ M1 merge" thay thế — xem fallback trong `M1_LEAD_INTEGRATION.md` L-02).
   - [ ] Block force pushes / Block deletions.
2. **Labels**: Settings → Labels → tạo từng label theo `.github/labels.yml` (name/color/description).
3. **Verify**: mở 1 PR nhỏ (VD: PR này) → xác nhận không push thẳng được lên `main`, CI trigger, PR template hiển thị đúng, issue template hiển thị khi bấm "New issue".

## B. Deploy skeleton (L-03)

### Backend → Render (Blueprint, dùng `render.yaml` ở root repo)
1. [ ] Render dashboard → New → Blueprint → connect repo `MRXz194/TitanHack_Careercompass` → Render đọc `render.yaml`.
2. [ ] Điền các env var chat đánh dấu `sync: false` (`CHAT_API_BASE`, `CHAT_API_KEY`, `CHAT_MODEL`) — copy giá trị thật từ `.env` local, KHÔNG paste vào chat/issue/log. Release không cần embedding key.
3. [ ] Build phải xác nhận file `backend/market.db` tồn tại; đây là aggregate-only release artifact, không chứa mô tả tuyển dụng. Thiếu file thì Render fail build thay vì âm thầm dùng seed.
4. [ ] Deploy xong → mở `https://<service>.onrender.com/api/health` → phải có `status=ok`, `market_db_loaded=true`, `postings_count=298`.
5. **Known limitation cần ghi vào pitch/runbook**: Render free plan spin-down khi idle (cold start ~30-50s). `market.db` được phục hồi từ Git ở mỗi deploy; `sessions.db` là ephemeral nên session có thể mất khi restart. Nếu ảnh hưởng demo, dùng `DEMO_MODE=replay` làm lưới an toàn.

### Frontend → Vercel
1. [ ] Vercel dashboard → Add New → Project → import repo, **Root Directory = `frontend`**.
2. [ ] Env vars: `NEXT_PUBLIC_API_BASE` = URL backend Render ở trên; `NEXT_PUBLIC_USE_MOCK` = `0` cho bản live (giữ `1` cho preview an toàn nếu BE chưa sẵn sàng).
3. [ ] Deploy → verify trang chào mở được ở URL Vercel công khai, thử trên trình duyệt ẩn danh + 1 thiết bị mobile.

### Sau khi có cả hai URL
1. [ ] Quay lại Render → env var `CORS_ORIGINS` → set đúng bằng URL Vercel thật (không dùng `*`, xem `backend/app/main.py` CORS middleware đọc `settings.cors_origins`).
2. [ ] Redeploy backend, verify FE gọi API thật không bị chặn CORS (Network tab, không có lỗi CORS trong console).
3. [ ] Ghi rollback version: Render/Vercel đều giữ deployment history — biết cách bấm "Redeploy" bản trước nếu bản mới lỗi.

## Env matrix (dev vs demo)

| Var | Dev (local) | Demo (Render/Vercel) |
|---|---|---|
| `NEXT_PUBLIC_API_BASE` | `http://localhost:8000` | URL Render thật |
| `NEXT_PUBLIC_USE_MOCK` | `1` khi FE chưa cần BE thật | `0` cho live path, có nút/flag chuyển `1` làm fallback |
| `CORS_ORIGINS` | `http://localhost:3000` | URL Vercel thật (exact origin) |
| `DEMO_MODE` | `off` | `off` cho live demo; `replay` là fallback bấm tay nếu mạng/LLM chết (L-08) |
| `AGENT_MODE` | `langgraph` (release path) | `langgraph`; đổi `deterministic` là kill switch nếu graph lỗi |

## Smoke test sau deploy (bắt buộc, ~3 phút — chạy lại sau MỌI redeploy)

- [ ] `GET /api/health` trên Render: `status: ok`, `market_db_loaded: true`, `postings_count: 298`
- [ ] Mở FE → `/explore` → lượt chào xuất hiện (không phải lỗi mạng) → trả lời 2 lượt → profile nhích %
- [ ] `/explore?mode=launch` → câu mở đầu launch khác explore
- [ ] Xóa 1 skill trong profile card → không có banner lỗi đỏ (verify optimistic-patch rollback không kích hoạt sai)
- [ ] DevTools Console: không có lỗi CORS
- [ ] Đổi `NEXT_PUBLIC_USE_MOCK=1` trên Vercel → redeploy → FE chạy độc lập không cần BE (drill lưới an toàn — làm 1 lần cho biết đường lui, rồi đổi lại `0`)

## Kết quả thật (điền sau khi bấm)

- Backend URL: `TBD`
- Frontend URL: `TBD`
- Ngày deploy lần đầu: `TBD`
- Known limitations: `TBD`
