# SECURITY & PRIVACY — mức tối thiểu cho sản phẩm dùng với học sinh

## 1. Nguyên tắc

- Không thu tên thật, email, số điện thoại, trường cụ thể, địa chỉ chi tiết, giới tính hoặc học bạ trong MVP.
- Dùng session ID ngẫu nhiên; UI nói rõ đây là bản demo và không nhập thông tin nhận dạng.
- Hội thoại chỉ phục vụ profile phiên hiện tại, không dùng để train/fine-tune.
- Tư vấn nghề là hỗ trợ quyết định, không phải quyết định tự động có hậu quả học vụ.
- Launch mode không yêu cầu tên trường/công ty, GPA, CV, email/phone hoặc link hồ sơ. Project/experience được mô tả tối thiểu và user có thể xóa.

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
- Không mở link/execute code trong project description; không để nội dung user/model tạo URL ứng tuyển tự động. Search queries là text trung tính.

## 4. Dữ liệu tuyển dụng và quyền sử dụng

- Trước khi crawl, M1/M2 kiểm tra robots.txt/điều khoản; ưu tiên API, dataset mở hoặc dữ liệu được phép dùng.
- Không vượt access control, CAPTCHA hoặc đăng nhập; không crawl dữ liệu ứng viên/cá nhân.
- Rate limit lịch sự, dừng khi 403/429.
- Lưu provenance: source, URL, crawled_at, snapshot count; UI chỉ hiện aggregate và attribution, không republish toàn bộ mô tả việc làm.
- Nếu nguồn không cho phép automation hoặc điều khoản không rõ, dùng public dataset/seed có license rõ và nói trung thực trong pitch.

## 5. Checklist release

- [x] Không secret trong git history/diff — M1 verify 2026-07-17: `git log --all -p` cho `*.env` và pattern `sk-...`/`*_API_KEY=` không có key thật, chỉ `REPLACE_ME` trong `.env.example`; `.env`/`.env.local` không nằm trong `git ls-files`.
- [ ] Production CORS chỉ có FE origin — **chưa deploy nên chưa verify được**; `CORS_ORIGINS` mặc định `http://localhost:3000`. Phải set = URL Vercel thật sau L-03, xem `docs/DEPLOY.md`§B bước cuối.
- [x] Session delete/TTL hoạt động hoặc demo disclaimer nêu rõ — M1 verify: `DELETE /api/profile/{session_id}` tồn tại và gọi `profiler.delete_session` (`backend/app/routers/chat.py:33-38`). TTL tự động chưa implement trong `session_store.py`, nhưng điều kiện "delete hoạt động" trong checklist đã đủ (OR).
- [x] Không raw PII trong log, replay, screenshot, pitch — M1 verify: mọi `log.info/warning` trong `backend/app/services/*` chỉ log model/tokens/latency/error type, không log message/profile content; 3 file trong `backend/app/data/replay/` đều có `"fictional": true`.
- [x] Source manifest + attribution + limitation có trên UI/report — M1 verify: `data/processed/manifest.json` có terms_url/license/count theo nguồn; `frontend/app/market/page.tsx` render `source_note`/`updated_at` từ API.
- [x] Dependency và endpoint smoke test pass — M1 verify 2026-07-17 (sau khi pull `main` mới nhất, commit `9a62969`): backend `pytest tests/unit tests/contract` 231 passed, `tests/integration` 26 passed, `scripts.check_routes` OK; frontend `npm run typecheck` + `npm run build` pass.
