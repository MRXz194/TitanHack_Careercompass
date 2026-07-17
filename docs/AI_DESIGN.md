# 🧠 AI DESIGN — Profiling, Skill Extraction, Recommendation, Anti-bias

> Người đọc chính: M3, M4. Prompt thật đặt trong `backend/app/prompts/` — file này là thiết kế + lý do.

## 1. Conversational Profiler (M4)

### Vì sao không phải quiz?
Đề bài cấm "reduced to a single personality quiz". Thiết kế: hội thoại mở, **adaptive** (câu sau phụ thuộc câu trước), profile hình thành dần và học sinh THẤY nó hình thành + sửa được. Đó là 3 điểm ăn tiền: interaction, transparency, autonomy.

### Bounded ReAct + state safety rail

Flow profiling dùng agent ReAct bị giới hạn thay vì một prompt tuyến tính: agent chọn công cụ hợp lệ để trích evidence, kiểm profile gap hoặc hỏi một câu tiếp theo. Code vẫn kiểm soát stage, tool allowlist, schema, budget và fallback; agent không được tự quyết career/ranking. Xem thiết kế đầy đủ tại `AGENTIC_RUNTIME.md`.

### State machine 5 phase (agent tự do trong allowlist của phase, code kiểm soát chuyển phase)

| Phase | Mục tiêu | Lượt (ước) | Chuyển phase khi |
|---|---|---|---|
| `warmup` | Chào, làm quen, giảm phòng thủ (hỏi lớp mấy, đang phân vân gì) | 1–2 | Có câu trả lời đầu |
| `interests` | Sở thích thật (hoạt động cụ thể đã làm và thấy vui — không hỏi "em thích nghề gì") | 3–4 | ≥2 interests + ≥2 dimensions có tín hiệu |
| `abilities` | Năng lực: môn mạnh, việc được khen, việc làm nhanh hơn bạn bè | 2–3 | ≥2 skills có source_quote |
| `constraints` | Điều kiện: vùng, tài chính, thời gian học, mong muốn gia đình — hỏi TẾ NHỊ | 1–2 | Có ≥1 constraint hoặc user né |
| `wrapup` | Tóm tắt profile bằng lời, hỏi "em thấy đúng chưa, muốn sửa gì?" | 1 | User xác nhận → `done=true` |

Code (không phải LLM) quyết định chuyển phase dựa trên completeness của profile → hội thoại không lan man, không lặp — lỗi phổ biến nhất của chatbot thuần prompt.

### Explore vs Graduate Launch

- Shared phases/tone/schema core; `journey_mode` được khóa từ opening turn.
- **Explore:** interest/ability/constraints evidence; completeness cần ≥2 interests, ≥2 dimensions, ≥2 sourced skills, ≥1 constraint/decline.
- **Launch:** project/internship/work evidence, tools/skills, job goal/constraints; completeness cần education stage, ≥1 experience hoặc explicit “chưa có”, ≥2 sourced skills, job goal hoặc role uncertainty.
- Không coi tên ngành/trường/GPA là bằng chứng skill. Project, volunteer và việc làm thêm có thể là evidence nếu user mô tả việc đã làm.

### Kỹ thuật structured output

Mỗi lượt LLM trả JSON `{reply, profile_delta, suggested_phase_done}`. Pydantic validate; fail → gửi lại kèm lỗi, retry tối đa 2. Retry vẫn fail → trả reply dạng câu hỏi generic của phase hiện tại (hardcode sẵn 2 câu/phase) — **hội thoại không bao giờ chết trước mặt judge**.

### Nguyên tắc giọng điệu (đưa vào system prompt)
- Xưng "mình", gọi "bạn/em"; ấm, tò mò, không phán xét; mỗi lượt CHỈ 1 câu hỏi; ≤3 câu/reply.
- Không bao giờ hỏi/suy đoán giới tính. Không khen sáo rỗng. Không dùng thuật ngữ (RIASEC, profile…).
- Đào cụ thể: user nói "em thích game" → hỏi "bạn thích chơi, hay từng tò mò nó được làm ra thế nào?" (phân biệt consumer vs creator signal).

## 2. Skill Extraction từ job postings (M3)

### Hybrid 2 tầng — lý do: rẻ, nhanh, kiểm soát được

**Tầng 1 — Dictionary match (chạy trước, xử lý ~80%):**
- `data/taxonomy/skills_vi.json`: mỗi skill chuẩn có `aliases` TV/TA. Match không phân biệt hoa thường trên title + description (chuẩn hóa unicode NFC trước).
- Deterministic, 0 đồng, chạy 3k postings trong vài giây.

**Tầng 2 — LLM catch-up (chỉ những posting nghèo tín hiệu):**
- Posting có < 3 skills sau tầng 1 → gửi LLM (batch 10 postings/call): "liệt kê kỹ năng theo taxonomy sau, nếu thấy skill NGOÀI taxonomy thì trả trong `new_skills`".
- `new_skills` xuất hiện ≥5 lần → M3 duyệt tay, thêm vào taxonomy → chạy lại tầng 1 (rẻ). **Taxonomy tự giàu lên từ dữ liệu — nói điểm này trong pitch.**
- Cache theo hash(posting_id + taxonomy_version) — chạy lại không tốn tiền.

### Map posting → career
Rule-based theo title keywords trong `careers_seed.json` (`title_patterns`), fallback LLM cho title lạ. Posting không map được → `unmapped`, log lại; nếu nhóm `unmapped` nào ≥50 postings → thiếu nghề trong KB → báo D-07 thêm.

## 3. Market Stats & Hiring-demand Proxy (M3)

Mỗi (career × region) và (skill × region), cửa sổ 90 ngày:
- `demand_count` = số postings.
- `salary_p25/p50/p75` = percentile trên posting CÓ lương; luôn trả `salary_sample_count`; <5 mẫu → null — **không bịa**.
- `trend_pct` = (count 45 ngày cuối − count 45 ngày đầu) / max(count 45 ngày đầu, 5) × 100. Thiếu đủ hai cửa sổ hoặc mẫu <10 → `low_confidence: true`; FE không đưa trend vào headline.

**Hiring-demand proxy** (field API vẫn là `gap_score`, 0..1 mỗi region):
```
gap_score = 0.6·norm(demand_count) + 0.4·norm(max(trend_pct,0))
```

Nếu trend low-confidence, dùng demand-only và gắn cờ. Posting data chỉ đo **nhu cầu tuyển dụng được quan sát**, không đo supply kỹ năng; vì vậy UI/pitch gọi “Radar nhu cầu kỹ năng”, không gọi “kỹ năng khan hiếm/thiếu người” nếu chưa có dữ liệu supply. Production mới kết hợp dữ liệu tốt nghiệp, chương trình đào tạo và time-to-fill.

**Nguyên tắc: công thức đơn giản, có denominator và limitation > công thức phức tạp mà không bảo vệ được trước judge.**

## 4. Matching & Explainability (M4)

### Scoring
```
score(career) = 0.5·cosine(embed(profile_text), embed(career))
              + 0.3·skill_overlap(profile.skills ∪ interests, career.top_skills)   # Jaccard có trọng số
              + 0.2·market_signal(career, profile.constraints.region_pref)          # norm(demand)·(1+trend/200)
```
- Hệ số trong `config.py` — judge hỏi "sao 0.5" → trả lời: ưu tiên phù hợp con người trước, thị trường sau (đúng tinh thần "tham khảo, không đóng khung"), và có thể tune.
- `profile_text` KHÔNG chứa: giới tính (không tồn tại trong schema), tên, region. **Region chỉ vào `market_signal`** để xếp thứ tự thông tin thị trường — không loại nghề nào vì vùng.
- **Stretch pick:** trong top 6–15, chọn career có dimension chủ đạo KHÁC dimension mạnh nhất của user — "cửa sổ mở rộng", đúng yêu cầu "expand choices".

### Evidence generation — chống bịa số (quan trọng nhất)
LLM chỉ được **diễn đạt lại** dữ liệu đưa vào prompt: (a) evidence_quotes của user, (b) stats object. System prompt cấm sinh số mới; sau khi sinh, **code regex-check**: mọi con số trong output phải xuất hiện trong stats input, sai → retry 1 lần → fail thì render evidence dạng template tĩnh từ stats (không lời văn). Demo không bao giờ hiện số bịa.

### Counterfactual
Từ scoring thật: lấy dimension có ảnh hưởng lớn nhất, đảo thử (±0.3), tìm career mới lên đầu → "Nếu em thiên về X hơn, gợi ý đầu bảng sẽ là Y". Tính bằng code (re-run scoring), LLM chỉ diễn đạt — counterfactual là THẬT, không phải văn mẫu.

### Graduate Launch readiness

Launch không có scoring engine thứ hai. Sau khi shared matching chọn role families:

```text
matched = profile skills có source/experience ∩ role top skills
missing = role top skills - matched
coverage = weighted matched / weighted role top skills
evidence_strength = số core skills có project/internship/work evidence
band = deterministic config thresholds(coverage, evidence_strength)
```

`ready_now | near_ready | build_foundation` là mức chuẩn bị, không phải xác suất được tuyển. Search query tạo từ canonical role title + aliases; action plan dùng missing skills và phải có deliverable. LLM chỉ diễn đạt `band_reason/actions`; code validate skill set/evidence/week/deliverable và có template fallback.

## 5. Anti-bias Guardrails (M4 chủ trì — tiêu chí trọng số cao nhất)

### By design (kiến trúc, không phải lời hứa)
1. Schema không có giới tính → không thể leak vào recommender (chứng minh được bằng code).
2. User lộ giới tính trong hội thoại ("em là con gái, mẹ bảo con gái nên...") → LLM được prompt KHÔNG lưu vào profile, và phản hồi mở: "nghề nghiệp không phân biệt bạn là ai — mình chọn theo điều bạn thích và làm tốt nhé".
3. Region = thông tin (hiện demand địa phương) chứ không phải bộ lọc (không ẩn nghề vì "vùng em không có").
4. Luôn ≥1 route ngoài đại học cho mọi career; stretch card luôn hiển thị.
5. Disclaimer cố định + trang "Cách hệ thống hoạt động" (PR-09) + nút sửa profile = autonomy.
6. Launch readiness không dùng trường, GPA, giới, vùng hoặc family expectation; region chỉ hiển thị demand context.

### Bias test bắt buộc (PR-08, kết quả vào `docs/BIAS_AUDIT.md`)
- 5 cặp hội thoại giống hệt nhau, chỉ khác tín hiệu giới ("em là nam/nữ" ở lượt 2) → top-5 phải trùng ≥4/5 và thứ tự tương đương.
- 3 cặp chỉ khác vùng (HN vs tỉnh) → tập nghề gợi ý không được nghèo đi, chỉ khác phần thông tin thị trường.
- Audit tay toàn bộ prompts: không chứa giả định giới/vùng/hoàn cảnh.
- Kết quả (kể cả fail và cách sửa) ghi thật vào BIAS_AUDIT.md — **đem file này vào pitch**: "chúng tôi không nói suông, chúng tôi test".

## 6. LLM config (chốt + fallback)

| Việc | Model | Ghi chú |
|---|---|---|
| Chat profiling, evidence | DeepSeek `deepseek-v4-flash` (OpenAI-compatible, `CHAT_API_BASE` + `CHAT_MODEL`) | JSON mode; test chất lượng TV ngay Phase 1 (PR-02) |
| Embeddings | OpenAI `text-embedding-3-small` (`EMBED_*` riêng — DeepSeek không có embeddings) | 1536 dims, rẻ |
| Fallback | Đổi `CHAT_MODEL`/`CHAT_API_BASE` sang `gpt-4o-mini` (hoặc model khác) — 1 biến env | Quyết định fallback do M4 + M1 tại H+8 nếu DeepSeek vỡ JSON > 20% |

Mọi call qua `app/services/llm.py`: log model + tokens + latency, timeout 30s, retry có backoff. Không import SDK LLM ở bất kỳ file nào khác.
