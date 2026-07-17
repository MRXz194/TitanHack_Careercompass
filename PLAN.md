# 📋 PLAN — CareerCompass, Hackathon 48h

> Đọc kèm: [docs/TASKS.md](docs/TASKS.md) (task từng người) · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/AI_DESIGN.md](docs/AI_DESIGN.md)

---

## 1. Bài toán cốt lõi & cách chúng ta thắng

### Đề bài yêu cầu 3 thứ (mapping trực tiếp sang module)

| # | Yêu cầu đề bài | Module của ta | Người phụ trách chính |
|---|---|---|---|
| 1 | Phân tích **nhu cầu kỹ năng thật** từ hiring data (postings, skills, lương, trend theo vùng/thời gian) | **Market Intelligence Engine** (data pipeline + market stats API + dashboard) | M2 (data) + M3 (AI extract) + M6 (FE dashboard) |
| 2 | Xây **hồ sơ năng lực–sở thích qua tương tác**, không phải 1 bài quiz | **Conversational Profiler** (chat nhiều lượt, profile build dần, hiển thị live) | M4 (AI) + M5 (FE chat) |
| 3 | Gợi ý **lộ trình học/nghề cá nhân hóa, giải thích được**, gồm cả đường nghề (vocational), không chỉ đại học | **Explainable Recommender + Pathway Builder** | M4 (AI) + M6 (FE) |
| ⚖️ | Ràng buộc đạo đức: **mở rộng lựa chọn, không đóng khung; không bias giới/vùng; gợi ý = tham khảo** | **Bias Guardrails by design** (xuyên suốt, có tài liệu riêng) | M4 chủ trì, cả team review |

### Tiêu chí chấm → chiến lược điểm

| Tiêu chí chấm | Trọng số (theo đề) | Ta đánh vào đâu |
|---|---|---|
| Chất lượng skill-signal extraction từ hiring data | Cao | Pipeline hybrid (từ điển kỹ năng VN + LLM), số liệu THẬT crawl từ TopCV/VietnamWorks/ITviec, hiển thị nguồn + số lượng posting làm bằng chứng |
| Mức độ cá nhân hóa + giải thích được | Cao | Mỗi gợi ý có **Evidence Card**: "vì sao gợi ý này" gắn với câu trả lời cụ thể của em + số liệu thị trường cụ thể |
| Anti-bias / mở rộng cơ hội | **Rất cao (high weight)** | Recommender **không nhận giới tính làm input**; luôn có ≥1 lộ trình vocational; có "Stretch suggestions" (nghề em chưa nghĩ tới); vùng miền là thông tin, không phải bộ lọc cứng; có trang "Cách hệ thống hoạt động" minh bạch |
| Hữu ích thật với học sinh & tư vấn viên | Cao | Demo bằng persona học sinh thật (lớp 12, tỉnh, phân vân); ngôn ngữ tiếng Việt tự nhiên, không thuật ngữ |

### 3 điểm đột phá (differentiators) — nói trong pitch

1. **Skill Gap Radar theo vùng**: từ dữ liệu posting thật, tính "kỹ năng nào đang khát nhân lực ở địa phương em" — chưa tool hướng nghiệp VN nào làm. Đây là "wow moment" của demo.
2. **Profile qua hội thoại + hiển thị live**: học sinh THẤY hồ sơ của mình hình thành theo từng câu trả lời (transparency = trust), và có thể sửa trực tiếp — tôn trọng autonomy đúng yêu cầu đề.
3. **Explainability 2 chiều**: mỗi gợi ý có (a) bằng chứng từ chính lời em nói, (b) bằng chứng từ thị trường (số posting, lương, trend), và (c) **counterfactual** — "nếu em thích X hơn thì gợi ý sẽ đổi thành Y" → chứng minh gợi ý là tham khảo, không phán quyết.

---

## 2. MVP — định nghĩa chính xác

### User journey demo (4 phút, phải chạy mượt 100%)

1. **Landing** (15s): vấn đề + giải pháp, nút "Bắt đầu khám phá".
2. **Chat profiling** (90s): AI hỏi ~8–10 lượt thích ứng (sở thích, môn học mạnh, hoạt động thích làm, điều kiện gia đình/vùng — hỏi mở, không trắc nghiệm). Bên phải: **Profile Card** cập nhật live từng chiều (kỹ thuật / sáng tạo / xã hội / phân tích / thực hành + kỹ năng + ràng buộc). Học sinh có thể click sửa profile.
3. **Kết quả** (90s): 4–5 hướng nghề xếp hạng, mỗi card gồm:
   - % phù hợp + **"Vì sao?"** (evidence từ câu trả lời + từ thị trường)
   - Số liệu thật: số posting 90 ngày, dải lương, trend, top vùng tuyển
   - **≥2 lộ trình**: Đại học / Cao đẳng–Trung cấp nghề / Chứng chỉ-Bootcamp, kèm bước đi cụ thể
   - 1 card **"Có thể em chưa nghĩ tới"** (stretch, mở rộng lựa chọn)
   - Dòng disclaimer: "Đây là gợi ý tham khảo — quyết định là của em."
4. **Skill Gap Radar** (45s): chọn vùng (VD: Đà Nẵng) → biểu đồ kỹ năng đang khát + nghề đang tăng trưởng, từ dữ liệu crawl thật.

### In-scope (MVP — PHẢI xong)

- ✅ Dataset ≥ 3.000 job postings thật (crawl 1 lần, tĩnh) từ ≥2 nguồn, phủ ≥3 vùng (HN, HCM, Đà Nẵng)
- ✅ Pipeline extract skills hybrid (từ điển + LLM) → bảng market stats: demand/career, salary, trend, skills theo vùng
- ✅ Chat profiling tiếng Việt ~8–10 lượt, adaptive, output profile JSON có cấu trúc
- ✅ Profile Card hiển thị live + cho phép chỉnh sửa
- ✅ Recommender: match profile ↔ career KB (embedding + rule), trả top 5 + 1 stretch
- ✅ Evidence Card giải thích được cho từng gợi ý (trích câu trả lời + số liệu thị trường)
- ✅ Lộ trình học đa dạng: mỗi nghề ≥2 route trong đó ≥1 route ngoài đại học
- ✅ Bias guardrails: không input giới tính vào recommender, stretch suggestions, disclaimer, trang "Cách hoạt động"
- ✅ Skill Gap Radar theo vùng (1 màn hình dashboard)
- ✅ Deploy được (Vercel + Render/Railway) hoặc chạy local ổn định cho demo
- ✅ Pitch deck + demo script + 2 persona demo chuẩn bị sẵn

### Out-of-scope (KHÔNG làm trong 48h — nói "future work" trong pitch)

- ❌ Đăng nhập / tài khoản / lưu lịch sử dài hạn (dùng session id trong localStorage)
- ❌ Crawl real-time / scheduler định kỳ (pitch: "kiến trúc đã sẵn sàng, xem ARCHITECTURE.md §Scalability")
- ❌ Mobile app (web responsive là đủ)
- ❌ Dashboard riêng cho tư vấn viên/giáo viên (chỉ mock 1 slide trong pitch)
- ❌ Fine-tune model / train ML riêng (dùng LLM + embedding + rules)
- ❌ Tích hợp trường học, chấm điểm học bạ, dự đoán điểm chuẩn
- ❌ Đa ngôn ngữ (chỉ tiếng Việt)
- ❌ Thanh toán, gamification, social features

### Definition of Done cho demo

- [ ] Chạy end-to-end 3 lần liên tiếp không lỗi với 2 persona khác nhau
- [ ] Mọi số liệu trên màn hình truy được về dataset thật (judge hỏi "số này ở đâu ra" → trả lời được)
- [ ] Thời gian phản hồi chat < 5s/lượt; trang kết quả < 8s
- [ ] Có fallback: nếu LLM API chết lúc demo → chế độ replay từ cached responses (M1 chuẩn bị)

---

## 3. Timeline 48h — milestones & lịch

> Quy ước: **H+n** = n giờ kể từ lúc bắt đầu. Sync toàn team 10 phút tại các mốc ⏰.

### Milestones (điều kiện pass — Team Lead check)

| Mốc | Giờ | Điều kiện pass |
|---|---|---|
| **M0 — Kickoff xong** | H+2 | Cả 6 người clone repo, chạy được FE + BE local, đọc xong PLAN + task của mình, API contract chốt v1 |
| **M1 — Móng xong** | H+8 | FE chat UI + dashboard skeleton chạy trên mock; crawler ra ≥500 postings raw; skill taxonomy v1; prompt profiling v1 test được trong notebook |
| **M2 — Dữ liệu thật + Chat thật** | H+20 | Dataset ≥3k postings processed; market stats API trả số thật; chat profiling end-to-end ra profile JSON; FE nối chat API thật |
| **M3 — End-to-end** | H+30 | Recommendation + evidence + pathway chạy full flow FE↔BE với dữ liệu thật; Skill Gap Radar có số thật |
| **M4 — Đóng băng tính năng** | H+40 | Polish UI, bias checklist pass, deploy xong, seed 2 persona demo, cached fallback sẵn sàng. **Sau mốc này: chỉ fix bug, không thêm feature** |
| **M5 — Sẵn sàng pitch** | H+46 | Pitch deck xong, demo rehearse ≥2 lần, demo script in ra, code freeze |

### Lịch chi tiết theo phase

**Phase 0 · H+0 → H+2 — Kickoff** ⏰
- Cả team: đọc PLAN + TASKS, setup môi trường, chạy quickstart, hỏi đáp.
- M1 điều phối: chốt API contract v1, phân quyền repo, tạo group chat + kênh #blockers.

**Phase 1 · H+2 → H+8 — Móng song song (không ai chờ ai)** ⏰ sync H+5, H+8
- M2: crawler nguồn #1 (TopCV) chạy ra data thật.
- M3: skill taxonomy VN v1 + thử prompt extract skills trên 50 postings mẫu.
- M4: thiết kế profile schema + prompt hội thoại, test trong script/notebook độc lập.
- M5: chat UI + Profile Card trên mock API.
- M6: dashboard kết quả + career card trên seed JSON.
- M1: CI, deploy skeleton lên Vercel/Render ngay từ giờ (deploy sớm = tránh thảm họa giờ chót), review PR.

**Phase 2 · H+8 → H+20 — Core (có ngủ ca 1: mỗi người ngủ 3–4h so le, M1 xếp ca)** ⏰ sync H+12, H+16, H+20
- M2: crawler nguồn #2, normalize, dedupe → processed dataset.
- M3: chạy extract skills toàn dataset, build market stats + skill gap index, expose qua API.
- M4: chat profiling engine hoàn chỉnh (state machine + LLM), endpoint /chat.
- M5: nối chat thật, profile editing, loading/error states.
- M6: nối market API thật, Skill Gap Radar, landing page.
- M1: integrate liên tục, giữ main luôn chạy được.

**Phase 3 · H+20 → H+30 — Recommendation & Explainability** ⏰ sync H+24, H+30
- M4: matching engine + evidence generation + counterfactual + pathway builder.
- M3: hỗ trợ M4 phần embedding careers; tinh chỉnh chất lượng stats.
- M5+M6: màn kết quả hoàn chỉnh (evidence card, pathway, stretch card).
- M2: data QA — soát số liệu sai, bổ sung nghề thiếu vào career KB.
- M1: end-to-end test liên tục, log lỗi vào #blockers.

**Phase 4 · H+30 → H+40 — Polish & Hardening (ngủ ca 2)** ⏰ sync H+34, H+40
- Bias checklist review toàn team (H+32, 30 phút, bắt buộc — xem AI_DESIGN.md §5).
- Polish UI, copy tiếng Việt, empty/error states, responsive.
- Deploy production, seed demo data, build cached-replay fallback.
- M1 + M6 bắt đầu pitch deck.

**Phase 5 · H+40 → H+48 — Pitch & Buffer** ⏰ rehearse H+42, H+45
- H+40–44: pitch deck xong, quay video backup demo (phòng wifi chết).
- H+44–46: rehearse 2 lần có bấm giờ, phản biện câu hỏi judge (list câu hỏi dự đoán trong docs/DEMO_SCRIPT.md).
- H+46–48: buffer. **Không deploy gì mới sau H+46.**

---

## 4. Phân vai 6 thành viên (chi tiết từng task → [docs/TASKS.md](docs/TASKS.md))

| ID | Vai | Sở hữu | Deliverable chính |
|---|---|---|---|
| **M1** | Team Lead / Integrator / DevOps | repo, CI/CD, deploy, contract, demo | Main luôn chạy; deploy; fallback demo; pitch |
| **M2** | Data Engineer | `data/pipeline` crawl + clean | Dataset ≥3k postings sạch, có vùng + lương + ngày |
| **M3** | AI Engineer — Market Intelligence | extract skills, market stats, embeddings | Market stats API số thật; Skill Gap Index |
| **M4** | AI Engineer — Profiling & Recommender | chat engine, matching, explainability, bias | Chat profiling; top-5 + stretch + evidence |
| **M5** | Frontend — Trải nghiệm profiling | chat UI, Profile Card | Màn chat + profile live-update mượt |
| **M6** | Frontend — Kết quả & Dashboard | career cards, radar, landing | Màn kết quả + Skill Gap Radar + landing |

**Cặp hỗ trợ khi kẹt (buddy):** M2↔M3, M4↔M3, M5↔M6, M1 hỗ trợ tất cả.

---

## 5. Rủi ro lớn nhất & phương án

| Rủi ro | Xác suất | Phương án |
|---|---|---|
| Crawler bị chặn / HTML đổi | Cao | 3 nguồn dự phòng (TopCV → VietnamWorks → ITviec/CareerViet); nếu H+10 vẫn <1k postings → chuyển dataset Kaggle VN jobs + crawl bổ sung; **quyết định do M1 chốt tại H+10, không tranh luận** |
| DeepSeek trả JSON hỏng / tiếng Việt kém | Vừa | Mọi LLM call có schema validation + retry 2 lần; fallback model cấu hình qua `.env` (đổi 1 dòng, xem backend/CLAUDE.md); test chất lượng ngay Phase 1 |
| Tích hợp FE–BE vỡ giờ chót | Vừa | API contract freeze tại H+8; FE luôn có mock mode (`NEXT_PUBLIC_USE_MOCK=1`); integrate liên tục từ H+12 chứ không dồn cuối |
| LLM API chết lúc demo | Thấp | Cached-replay mode cho 2 persona demo (M1, task L-08) |
| Thành viên kẹt task > 90 phút | Cao | Rule: kẹt 45' → hỏi buddy; 90' → báo M1 đổi hướng/đổi người. Không hero-coding trong im lặng |
| Scope creep ("thêm tí này hay lắm") | Cao | Mọi feature ngoài In-scope → ghi vào `docs/BACKLOG.md`, làm sau M4 nếu thừa giờ. M1 có quyền veto |

---

## 6. Tech stack (chốt — không đổi giữa chừng)

| Lớp | Chọn | Lý do |
|---|---|---|
| Frontend | Next.js 15 + TypeScript + Tailwind v4 + Recharts | Team quen React; AI assistants hỗ trợ tốt nhất; deploy Vercel 1 click |
| Backend | FastAPI (Python 3.11) + Pydantic v2 | Python mạnh nhất cho data/NLP; Swagger tự động = FE tự tra API |
| DB | SQLite (qua SQLAlchemy) | Zero-setup, đủ cho scale hackathon; đường lên Postgres đã thiết kế sẵn |
| Vector search | NumPy cosine in-process | ~200 careers, không cần vector DB — đừng over-engineer |
| LLM chat | DeepSeek (OpenAI-compatible) — cấu hình qua env | Rẻ; đổi model = đổi 1 biến env |
| Embeddings | OpenAI `text-embedding-3-small` | Rẻ, multilingual đủ tốt cho tiếng Việt |
| Crawl | httpx + BeautifulSoup/selectolax (+ Playwright chỉ khi bắt buộc) | Nhẹ, nhanh |
| Deploy | Vercel (FE) + Render/Railway (BE) | Free tier, nhanh |
| Charts | Recharts | Đơn giản, đẹp đủ dùng |

Chi tiết kiến trúc & scalability: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
