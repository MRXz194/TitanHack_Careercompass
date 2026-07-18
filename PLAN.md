# 📋 PLAN — CareerCompass, Hackathon 48h

> Đọc kèm: [docs/TASKS.md](docs/TASKS.md) · [docs/AI_FOCUS.md](docs/AI_FOCUS.md) · [docs/AGENTIC_RUNTIME.md](docs/AGENTIC_RUNTIME.md) · [docs/BUSINESS_CASE.md](docs/BUSINESS_CASE.md) · [docs/EVALUATION.md](docs/EVALUATION.md) · [docs/TESTING.md](docs/TESTING.md) · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/AI_DESIGN.md](docs/AI_DESIGN.md)
>
> Trước khi bấm giờ: cả team pass [docs/PREFLIGHT.md](docs/PREFLIGHT.md). Trạng thái repo/docs tốt không đồng nghĩa runtime đã sẵn sàng.

---

## 1. Bài toán cốt lõi & cách chúng ta thắng

### Đề bài yêu cầu 3 thứ (mapping trực tiếp sang module)

| # | Yêu cầu đề bài | Module của ta | Người phụ trách chính |
|---|---|---|---|
| 1 | Phân tích **nhu cầu kỹ năng thật** từ hiring data (postings, skills, lương, trend theo vùng/thời gian) | **Market Intelligence Engine** (data pipeline + market stats API + dashboard) | M2 (data) + M3 (AI extract) + M6 (FE dashboard) |
| 2 | Xây **hồ sơ năng lực–sở thích qua tương tác**, không phải 1 bài quiz | **Conversational Profiler** (chat nhiều lượt, profile build dần, hiển thị live) | M4 (AI) + M5 (FE chat) |
| 3 | Gợi ý **lộ trình học/nghề cá nhân hóa, giải thích được**, gồm cả đường nghề (vocational), không chỉ đại học | **Explainable Recommender + Pathway Builder** | M4 (AI) + M6 (FE) |
| ⚖️ | Ràng buộc đạo đức: **mở rộng lựa chọn, không đóng khung; không bias giới/vùng; gợi ý = tham khảo** | **Bias Guardrails by design** (xuyên suốt, có tài liệu riêng) | M4 chủ trì, cả team review |

### Hai user mode, một core

| Mode | Người dùng | Outcome | Không biến thành |
|---|---|---|---|
| **Explore** | học sinh/sinh viên chưa chốt hướng | profile → nghề + route học đa dạng | personality quiz/“nghề tốt nhất” |
| **Launch** | sinh viên năm cuối/mới tốt nghiệp | role families → matched/missing skills + search queries + action 30 ngày | job board/CV scorer/auto-apply |

Cả hai mode dùng chung taxonomy, market stats, profile evidence, matching và ethics. Chi tiết Launch: [docs/GRADUATE_LAUNCH.md](docs/GRADUATE_LAUNCH.md).

### Bài toán doanh nghiệp/tổ chức mà MVP chứng minh

Trường học và trung tâm hướng nghiệp phải phục vụ nhiều học sinh nhưng thiếu thời gian 1:1, dữ liệu thị trường rời rạc và khó giải thích tại sao một hướng nghề được đề xuất. CareerCompass tạo **bản nháp trước buổi tư vấn**: học sinh tự khám phá, sửa hồ sơ, xem nhiều route và mang một output có bằng chứng đến tư vấn viên. Hệ thống hỗ trợ chứ không thay thế quyết định của học sinh/tư vấn viên. Buyer, KPI pilot và giới hạn claim nằm trong [BUSINESS_CASE.md](docs/BUSINESS_CASE.md).

### Goal vận hành của MVP tại H+40

```text
Một học sinh/sinh viên hoàn thành hội thoại có thể sửa profile của mình,
nhận nhiều hướng đi có evidence cá nhân + market snapshot có nguồn,
và biết một bước học/việc tiếp theo. Nếu AI provider lỗi, flow vẫn chạy bằng
fallback/replay; nếu evidence hoặc bias gate fail, sản phẩm không claim kết luận đó.
```

Agent không thay mục tiêu này: agent chỉ chọn cách thu thập/xác nhận evidence trong chat. Code deterministic vẫn quyết định candidate, score, stretch, route và Launch readiness. Chi tiết: [docs/AGENTIC_RUNTIME.md](docs/AGENTIC_RUNTIME.md).

### Tiêu chí chấm → chiến lược điểm

| Tiêu chí chấm | Trọng số (theo đề) | Ta đánh vào đâu |
|---|---|---|
| Chất lượng skill-signal extraction từ hiring data | Cao | Pipeline hybrid (từ điển kỹ năng VN + LLM), số liệu THẬT crawl từ TopCV/VietnamWorks/ITviec, hiển thị nguồn + số lượng posting làm bằng chứng |
| Mức độ cá nhân hóa + giải thích được | Cao | Mỗi gợi ý có **Evidence Card**: "vì sao gợi ý này" gắn với câu trả lời cụ thể của em + số liệu thị trường cụ thể |
| Anti-bias / mở rộng cơ hội | **Rất cao (high weight)** | Recommender **không nhận giới tính làm input**; luôn có ≥1 lộ trình vocational; có "Stretch suggestions" (nghề em chưa nghĩ tới); vùng miền là thông tin, không phải bộ lọc cứng; có trang "Cách hệ thống hoạt động" minh bạch |
| Hữu ích thật với học sinh & tư vấn viên | Cao | Demo bằng persona học sinh thật (lớp 12, tỉnh, phân vân); ngôn ngữ tiếng Việt tự nhiên, không thuật ngữ |

### 3 điểm đột phá (differentiators) — nói trong pitch

> Chi tiết phần AI focus và ứng dụng đa bối cảnh: [docs/AI_FOCUS.md](docs/AI_FOCUS.md). Thiết kế agentic bounded ReAct: [docs/AGENTIC_RUNTIME.md](docs/AGENTIC_RUNTIME.md).

1. **Radar nhu cầu kỹ năng tuyển dụng theo vùng**: từ snapshot posting thật, chỉ ra kỹ năng có demand/momentum cao ở địa phương. Đây là proxy tín hiệu cầu, **không tuyên bố đo trực tiếp thiếu hụt cung–cầu** — sự minh bạch này làm sản phẩm đáng tin hơn.
2. **Profile qua hội thoại + hiển thị live**: học sinh THẤY hồ sơ của mình hình thành theo từng câu trả lời (transparency = trust), và có thể sửa trực tiếp — tôn trọng autonomy đúng yêu cầu đề.
3. **Explainability 2 chiều**: mỗi gợi ý có (a) bằng chứng từ chính lời em nói, (b) bằng chứng từ thị trường (số posting, lương, trend), và (c) **counterfactual** — "nếu em thích X hơn thì gợi ý sẽ đổi thành Y" → chứng minh gợi ý là tham khảo, không phán quyết.
4. **Continuity học → việc**: cùng một profile chuyển từ Explore sang Launch, biến project/thực tập thành evidence và chỉ ra job-title lân cận + deliverable 30 ngày.
5. **AI agent có kiểm soát, không phải chatbot trả lời theo kịch bản**: agent chọn câu hỏi/tool đọc dữ liệu phù hợp với evidence đang thiếu, nhưng tool, dữ liệu, ngân sách và đạo đức đều bị policy code khóa; vì vậy vừa linh hoạt cho từng học sinh vừa test/replay được trước judge.

---

## 2. MVP — định nghĩa chính xác

### User journey demo (4 phút, phải chạy mượt 100%)

1. **Landing** (10s): vấn đề + hai mode, chọn Explore.
2. **Chat profiling** (75s): dùng persona rút gọn/replay nhưng thể hiện câu hỏi adaptive; Profile Card live và sửa một inference.
3. **Kết quả** (75s): 4–5 hướng nghề xếp hạng, mở một card gồm:
   - % phù hợp + **"Vì sao?"** (evidence từ câu trả lời + từ thị trường)
   - Số liệu thật: số posting 90 ngày, dải lương, trend, top vùng tuyển
   - **≥2 lộ trình**: Đại học / Cao đẳng–Trung cấp nghề / Chứng chỉ-Bootcamp, kèm bước đi cụ thể
   - 1 card **"Có thể em chưa nghĩ tới"** (stretch, mở rộng lựa chọn)
   - Dòng disclaimer: "Đây là gợi ý tham khảo — quyết định là của em."
4. **Radar nhu cầu kỹ năng** (30s): đổi vùng → demand/momentum + nguồn/confidence.
5. **Launch glimpse** (30s, pre-seeded/replay): sinh viên năm cuối có project Excel → 3 role entry-level, matched/missing skills và action tuần 1 có deliverable. Không live chat persona thứ hai nếu làm vượt thời gian demo.

### In-scope (MVP — PHẢI xong)

- ✅ Dataset ≥ 3.000 job postings thật (crawl 1 lần, tĩnh) từ ≥2 nguồn, phủ ≥3 vùng (HN, HCM, Đà Nẵng)
- ✅ Pipeline extract skills hybrid (từ điển + LLM) → bảng market stats: demand/career, salary, trend, skills theo vùng
- ✅ Chat profiling tiếng Việt ~8–10 lượt, adaptive, output profile JSON có cấu trúc
- ✅ Profile Card hiển thị live + cho phép chỉnh sửa
- ✅ Recommender: match profile ↔ career KB (embedding + rule), trả top 5 + 1 stretch
- ✅ Evidence Card giải thích được cho từng gợi ý (trích câu trả lời + số liệu thị trường)
- ✅ Lộ trình học đa dạng: mỗi nghề ≥2 route trong đó ≥1 route ngoài đại học
- ✅ Bias guardrails: không input giới tính vào recommender, stretch suggestions, disclaimer, trang "Cách hoạt động"
- ✅ Radar nhu cầu kỹ năng theo vùng (API giữ tên `skill gap`, UI ghi rõ đây là proxy từ hiring demand)
- ✅ Deploy được (Vercel + Render/Railway) hoặc chạy local ổn định cho demo
- ✅ Pitch deck + demo script + 2 persona demo chuẩn bị sẵn
- ✅ Launch mode tối thiểu: stage/job goal/experience evidence trong profile; role recommendations dùng cùng engine; readiness band không phải xác suất; search queries + 4 actions có deliverable

### Out-of-scope (KHÔNG làm trong 48h — nói "future work" trong pitch)

- ❌ Đăng nhập / tài khoản / lưu lịch sử dài hạn (dùng session id trong localStorage)
- ❌ Crawl real-time / scheduler định kỳ (pitch: "kiến trúc đã sẵn sàng, xem ARCHITECTURE.md §Scalability")
- ❌ Mobile app (web responsive là đủ)
- ❌ Dashboard riêng cho tư vấn viên/giáo viên (chỉ mock 1 slide trong pitch)
- ❌ Fine-tune model / train ML riêng (dùng LLM + embedding + rules)
- ❌ Tích hợp trường học, chấm điểm học bạ, dự đoán điểm chuẩn
- ❌ Đa ngôn ngữ (chỉ tiếng Việt)
- ❌ Thanh toán, gamification, social features
- ❌ Job board/vacancy matching live, CV scoring, cover-letter/auto-apply, application tracker, dự đoán khả năng được tuyển hoặc lương cá nhân

### Definition of Done cho demo

- [ ] Chạy end-to-end 3 lần liên tiếp không lỗi với 2 persona khác nhau
- [ ] Mọi số liệu trên màn hình truy được về dataset thật (judge hỏi "số này ở đâu ra" → trả lời được)
- [ ] Thời gian phản hồi chat < 5s/lượt; trang kết quả < 8s
- [ ] Có fallback: nếu LLM API chết lúc demo → chế độ replay từ cached responses (M1 chuẩn bị)
- [ ] `docs/EVALUATION_RESULTS.md` có metric thật: extraction, mapping, recommendation rubric, bias, latency và limitations
- [ ] Mọi nguồn dữ liệu có manifest/provenance; không dùng nguồn cấm automation hoặc không rõ quyền sử dụng
- [ ] 5 học sinh + 1–2 tư vấn viên test; pitch ghi đúng cỡ mẫu, không phóng đại
- [ ] Ít nhất 2 Launch personas pass invariants: matched skill có evidence, missing skill từ role stats, readiness không dùng giới/trường/vùng, mỗi action có deliverable

### Scope ladder — cắt đúng thứ tự để chắc chắn hoàn thiện

| Mức | Phải giữ | Có thể giảm khi trễ |
|---|---|---|
| **P0 — demo sống** | Explore E2E + Launch replay result; profile editable; top 5 + stretch đúng contract; grounded evidence; routes; source; replay | Không được cắt |
| **P1 — target chấm điểm** | 3k postings, ≥2 nguồn, top 5 + stretch, 3 vùng, hybrid extraction, Launch live + readiness/actions, user test | Data được giảm theo Plan B; Launch live được hạ về replay nhưng contract/invariants phải giữ |
| **P2 — polish** | animation, mini-chart từng card, 40–60 nghề, insight phụ, counselor mock slide | Cắt đầu tiên, không ảnh hưởng core |

**Rule:** nếu một P2 đe dọa P0/P1, M1 cắt ngay. Không dùng seed number như số thật; seed UI luôn có nhãn “dữ liệu mẫu”.

---

## 3. Timeline 48h — milestones & lịch

> Quy ước: **H+n** = n giờ kể từ lúc bắt đầu. Sync toàn team 10 phút tại các mốc ⏰.

### Milestones (điều kiện pass — Team Lead check)

| Mốc | Giờ | Điều kiện pass |
|---|---|---|
| **M0 — Kickoff xong** | H+2 | Cả 6 người clone repo, chạy được FE + BE local, đọc xong PLAN + task của mình, API contract chốt v1 |
| **M1 — Móng xong** | H+8 | FE chat UI + dashboard skeleton chạy trên mock; crawler ra ≥500 postings raw; skill taxonomy v1; prompt profiling v1 test được trong notebook |
| **M2 — Dữ liệu thật + Chat thật** | H+20 | Dataset target ≥3k (hoặc Plan B đã ghi rõ); data report + provenance; chat profiling E2E ra profile JSON; FE nối chat API thật |
| **M3a — E2E skeleton** | H+30 | Full flow chạy bằng core/stub đúng contract; chat live; market source rõ; không còn blocker tích hợp |
| **M3b — E2E dữ liệu thật** | H+34 | Recommendation + grounded evidence + pathway + Radar nhu cầu kỹ năng chạy với artifact thật |
| **M4 — Đóng băng tính năng** | H+40 | P0 pass; evaluation/bias checklist có kết quả; deploy + replay sẵn; security/privacy checklist pass. **Sau mốc này chỉ fix bug** |
| **M5 — Sẵn sàng pitch** | H+46 | Pitch deck xong, demo rehearse ≥2 lần, demo script in ra, code freeze |

### Lịch chi tiết theo phase

**Phase 0 · H+0 → H+2 — Kickoff** ⏰
- Cả team: đọc PLAN + TASKS, setup môi trường, chạy quickstart, hỏi đáp.
- M1 điều phối: chốt API contract v1, phân quyền repo, tạo group chat + kênh #blockers.

**Phase 1 · H+2 → H+8 — Móng song song (không ai chờ ai)** ⏰ sync H+5, H+8
- M2: crawler nguồn #1 (TopCV) chạy ra data thật.
- M3: skill taxonomy VN v1 + thử prompt extract skills trên 50 postings mẫu.
- M4: thiết kế profile schema + prompt hội thoại, test trong script/notebook độc lập.
- M5: chat UI + Profile Card Explore/Launch trên mock API.
- M6: dashboard kết quả + career/readiness card trên seed JSON.
- M1: CI, deploy skeleton lên Vercel/Render ngay từ giờ (deploy sớm = tránh thảm họa giờ chót), review PR.

**Phase 2 · H+8 → H+20 — Core (có ngủ ca 1: mỗi người ngủ 3–4h so le, M1 xếp ca)** ⏰ sync H+12, H+16, H+20
- M2: crawler nguồn #2, normalize, dedupe → processed dataset.
- M3: chạy extract skills toàn dataset, build market stats + skill gap index, expose qua API.
- M4: chat profiling engine hai mode (state machine + LLM), endpoint /chat.
- M5: nối chat thật, profile editing, loading/error states.
- M6: nối market API thật, Radar nhu cầu kỹ năng, landing page.
- M1: integrate liên tục, giữ main luôn chạy được.

**Phase 3 · H+20 → H+30 — Recommendation & Explainability** ⏰ sync H+24, H+30
- M4: matching + evidence + counterfactual + pathway builder + Launch readiness/action plan.
- M3: hỗ trợ M4 phần embedding careers; tinh chỉnh chất lượng stats.
- M5+M6: màn kết quả hoàn chỉnh (evidence card, pathway, stretch card).
- M2: data QA — soát số liệu sai, bổ sung nghề thiếu vào career KB.
- M1: end-to-end test liên tục, log lỗi vào #blockers.

**Phase 4 · H+30 → H+40 — Polish & Hardening (ngủ ca 2)** ⏰ sync H+34, H+40
- Bias checklist review toàn team (H+35, 30 phút, bắt buộc — xem AI_DESIGN.md §5).
- Polish UI, copy tiếng Việt, empty/error states, responsive.
- Deploy production, seed demo data, build cached-replay fallback.
- M1 + M6 bắt đầu pitch deck.

**Phase 5 · H+40 → H+48 — Pitch & Buffer** ⏰ rehearse H+42, H+45
- H+40–44: pitch deck xong, quay video backup demo (phòng wifi chết).
- H+44–46: rehearse 2 lần có bấm giờ, phản biện câu hỏi judge (list câu hỏi dự đoán trong docs/DEMO_SCRIPT.md).
- H+46–48: buffer. **Không deploy gì mới sau H+46.**

---

## 4. Phân vai 6 thành viên (chi tiết từng task → [docs/TASKS.md](docs/TASKS.md))

Master schedule/dependency nằm ở `docs/TASKS.md`; mỗi member dùng task card riêng trong `docs/workstreams/`. Task card là acceptance source cho AI agent, không chỉ là mô tả tham khảo.

| ID | Vai | Sở hữu | Deliverable chính |
|---|---|---|---|
| **M1** | Team Lead / Integrator / DevOps | repo, CI/CD, deploy, contract, demo | Main luôn chạy; deploy; fallback demo; pitch |
| **M2** | Data Engineer | `data/pipeline` crawl + clean | Dataset ≥3k postings sạch, có vùng + lương + ngày |
| **M3** | AI Engineer — Market Intelligence | extract skills, market stats, embeddings | Market stats API số thật; Skill Gap Index |
| **M4** | AI Engineer — Profiling & Recommender | two-mode profiler, matching, explainability, readiness, bias | Explore/Launch profile; top-5 + stretch + evidence/readiness |
| **M5** | Frontend — Trải nghiệm profiling | mode/chat/Profile Card | Chat + profile/experience live-update mượt |
| **M6** | Frontend — Kết quả & Dashboard | career/readiness cards, radar, landing | Explore/Launch results + Radar + landing |

**Task cards:** [M1](docs/workstreams/M1_LEAD_INTEGRATION.md) · [M2](docs/workstreams/M2_DATA_ENGINEERING.md) · [M3](docs/workstreams/M3_MARKET_AI.md) · [M4](docs/workstreams/M4_PROFILE_RECOMMENDER.md) · [M5](docs/workstreams/M5_FRONTEND_EXPLORE.md) · [M6](docs/workstreams/M6_FRONTEND_RESULTS_MARKET.md).

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
| Nguồn cấm/không rõ quyền crawl | Vừa | Check terms/robots trước; không bypass access control; chuyển dataset mở/seed có license; lưu source manifest và attribution |
| Judge bắt bẻ “skill gap” không có dữ liệu supply | Cao | UI/pitch gọi đúng là hiring-demand proxy; nêu limitation; future kết hợp graduate/curriculum/supply data |
| Core AI đẹp nhưng không chứng minh chất lượng | Cao | Quality gates trong EVALUATION.md; golden set/personas; report cả fail và limitations |

---

## 6. Tech stack (chốt — không đổi giữa chừng)

| Lớp | Chọn | Lý do |
|---|---|---|
| Frontend | Next.js 15 + TypeScript + Tailwind v4 + Recharts | Team quen React; AI assistants hỗ trợ tốt nhất; deploy Vercel 1 click |
| Backend | FastAPI (Python 3.11) + Pydantic v2 | Python mạnh nhất cho data/NLP; Swagger tự động = FE tự tra API |
| DB | SQLite (qua SQLAlchemy) | Zero-setup, đủ cho scale hackathon; đường lên Postgres đã thiết kế sẵn |
| Matching retrieval | Cosine 5 chiều cùng-space in-process | 25 careers, dễ giải thích/test; chưa cần vector DB |
| AI model/tool layer | LangChain Core + `langchain-openai`, chỉ qua `services/llm.py` | Một gateway cho provider adapters, typed tools, structured output; fake/test được |
| LLM chat | DeepSeek `deepseek-v4-flash` qua LangChain `ChatOpenAI` + OpenAI-compatible env | Nhanh/rẻ; JSON mode; đổi provider qua gateway |
| Agent runtime | LangGraph `StateGraph` custom tối giản; chỉ `/api/chat` | Release dùng `AGENT_MODE=langgraph`; deterministic là kill switch |
| Embeddings | Post-MVP experiment, không nằm trên release request path | Chỉ bật khi profile/career cùng encoder và thắng evaluation baseline |
| Crawl | httpx + BeautifulSoup/selectolax (+ Playwright chỉ khi bắt buộc) | Nhẹ, nhanh |
| Deploy | Vercel (FE) + Render/Railway (BE) | Free tier, nhanh |
| Charts | Recharts | Đơn giản, đẹp đủ dùng |

Chi tiết kiến trúc & scalability: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

Stack đã chốt: **LangChain cho model/tool/structured output; LangGraph cho custom StateGraph orchestration**. Boundary, version pins và spike gate: [docs/ADR_AGENT_ORCHESTRATION.md](docs/ADR_AGENT_ORCHESTRATION.md). Không thêm `create_agent`, prebuilt ReAct, LangSmith service, checkpointer hoặc graph cho recommendation trong 48h.

---

## 7. Execution system — cách biến plan thành sản phẩm

1. **Preflight:** không bấm giờ cho tới khi `docs/PREFLIGHT.md` có owner/runtime/CI/contract/source/key readiness.
2. **Task source:** `TASKS.md` quyết định lịch/dependency; `docs/workstreams/M*.md` quyết định cách làm và acceptance.
3. **AI context:** mỗi member mở root/package CLAUDE + task card + đúng source docs; dùng task packet trong `AGENT_WORKFLOW.md`.
4. **Build:** mock/fixture trước để unblock; vertical slice nhỏ; không hai builder cùng file.
5. **Verify:** static → unit → contract → integration → acceptance theo [docs/TESTING.md](docs/TESTING.md); ghi command/evidence trong PR. Chưa chạy = `NOT_VERIFIED`.
6. **Review:** buddy review + chạy ít nhất một lệnh; M1 gate contract/security/deploy/claims.
7. **Handoff:** artifact/version/hash/command/sample/limitation; consumer chạy và thả ✅.
8. **Integrate:** M1 merge critical path, smoke Explore/Launch, cập nhật blocker/kill switch.
9. **Freeze:** H+40 chỉ bug; feature mới chỉ theo `FEATURE_ROADMAP.md` khi P0/P1 gates pass.
10. **Evidence:** H+42 evaluation/data/bias results có số thật; pitch không dùng placeholder hoặc seed như actual.

### Definition of Done chung cho bất kỳ task nào

- Expected artifact tồn tại đúng path và consumer đọc/chạy được.
- Test trong task card đã chạy; failure/fallback được ghi, không che.
- Contract/types/mocks/docs đồng bộ nếu shape thay đổi.
- Không vi phạm hard ethics/data/privacy/claim rules.
- Không phá mock/live/replay hoặc critical-path consumer.
- PR nhỏ/review được; handoff acknowledged.
