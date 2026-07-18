# 📜 API CONTRACT — Nguồn chân lý FE ↔ BE

> **Freeze tại H+8.** Muốn đổi: theo quy trình TEAM_RULES.md §2. Đổi contract = sửa file này + `backend/app/models/schemas.py` + `frontend/types/index.ts` trong CÙNG 1 PR.
>
> Base URL: local `http://localhost:8000` · Mọi endpoint prefix `/api`. Mọi lỗi trả `{ "error": { "code": string, "message": string } }` với HTTP status phù hợp.

---

## 1. Health

`GET /api/health`

```json
{ "status": "ok", "llm_configured": true, "llm_ok": true, "data_loaded": true, "market_db_loaded": true, "postings_count": 3412 }
```

`llm_configured` chỉ xác nhận key production đã được cấu hình và không phải placeholder; nó
không gọi provider và không tuyên bố model đang reachable. `llm_ok` là alias cũ giữ tương thích,
consumer mới phải dùng `llm_configured`. Provider readiness được chứng minh bằng bounded chat
smoke riêng để không làm health check Render phát sinh chi phí hoặc phụ thuộc mạng.
`market_db_loaded`: whether `/api/market/*` is reading real pipeline output (`market.db`) vs seed fallback — check this before assuming market numbers are live during demo prep. `postings_count` reflects whichever source is active (real count when `market_db_loaded`, seed sum otherwise).

---

## 2. Chat Profiling

### `POST /api/chat`

Request:
```json
{
  "session_id": "uuid-do-FE-tu-sinh-va-giu-trong-localStorage",
  "message": "Em thích vẽ và hay sửa đồ điện trong nhà",  // null cho lượt mở đầu
  "journey_mode": "explore"                               // explore | launch; gửi từ opening turn
}
```

Response:
```json
{
  "reply": "Hay quá! Khi sửa đồ điện, em thấy thích nhất phần nào — tìm ra chỗ hỏng, hay lúc làm nó chạy lại được?",
  "phase": "interests",          // warmup | interests | abilities | constraints | wrapup
  "turn": 3,
  "done": false,                 // true = đủ dữ kiện, FE hiện CTA "Xem hướng đi"
  "profile": { ...Profile }      // profile ĐẦY ĐỦ sau khi merge (không phải delta)
}
```

### `GET /api/profile/{session_id}` → `{ "profile": Profile }`

### `DELETE /api/profile/{session_id}` → `{ "ok": true }`

Xóa phiên server-side (privacy). 404 nếu session không tồn tại. FE nên xóa luôn `localStorage` key `cc_session_id`.

Session semantics bắt buộc:

- `message=null` hoặc chuỗi chỉ có whitespace + `session_id` mới: tạo opening turn.
- `message` tối đa 2.000 ký tự và `session_id` dài 1–128 ký tự; vượt giới hạn trả error envelope 422. FE phải áp cùng giới hạn 2.000 ký tự tại composer.
- `message=null` hoặc chuỗi chỉ có whitespace + `session_id` đã có: **resume idempotent**, không reset `turn`, `phase`, profile hay corrections.
- “Bắt đầu hồ sơ mới” phải sinh UUID mới trước khi gọi chat; xóa UUID cũ là best-effort, không được chặn UI.
- Đổi Explore ↔ Launch sau khi đã trả lời cũng tạo UUID mới; mode của session cũ luôn khóa theo opening turn.

### `PATCH /api/profile/{session_id}` — học sinh sửa tay profile (autonomy)

Request (gửi phần muốn sửa):
```json
{
  "dimensions": { "ky_thuat": 0.9 },
  "remove_skills": ["python"],
  "add_interests": ["thiết kế nội thất"],
  "remove_interests": ["vẽ tranh"],
  "education_stage": "final_year",
  "job_goal": "tìm vai trò dữ liệu entry-level",
  "add_experiences": [
    { "title": "Dashboard bán hàng", "kind": "project", "description": "…", "skills": ["Excel"], "source_quote": "em đã làm dashboard…" }
  ],
  "remove_experience_titles": []
}
```
Response: `{ "profile": Profile }`

PATCH semantics: field bị bỏ qua = giữ nguyên; gửi `education_stage`/`job_goal: null` = xóa giá trị; add/remove interest và experience được áp dụng không phân biệt hoa thường trong MVP. User edit mới nhất có quyền thêm lại interest từng xóa. Mọi removal/correction phải lưu vào session để inference lượt sau không tự phục hồi điều user đã bác bỏ.

### Schema `Profile`

```json
{
  "session_id": "…",
  "journey_mode": "explore",      // explore | launch
  "education_stage": "high_school", // high_school | vocational_student | college_student | university_student | final_year | recent_graduate | other | null
  "job_goal": null,                // mô tả mục tiêu việc làm nếu journey_mode=launch
  "dimensions": {                 // 0..1 — 5 chiều năng lực-sở thích
    "ky_thuat": 0.7,              // thực hành-kỹ thuật (làm với máy móc, công cụ)
    "phan_tich": 0.4,             // phân tích-dữ liệu-logic
    "sang_tao": 0.8,              // sáng tạo-nghệ thuật
    "xa_hoi": 0.3,                // làm việc với con người, giúp đỡ, giảng dạy
    "quan_ly": 0.2                // tổ chức, kinh doanh, lãnh đạo
  },
  "skills": [ { "name": "vẽ tay", "level": "tự đánh giá khá", "source_quote": "em thích vẽ..." } ],
  "interests": ["vẽ", "sửa chữa đồ điện"],
  "constraints": {
    "region_pref": "danang",       // null nếu chưa rõ — CHỈ là preference, không phải filter cứng
    "study_budget": "hạn chế",     // null | "hạn chế" | "trung bình" | "thoải mái"
    "study_duration_pref": "ngắn", // null | "ngắn" | "dài đều được"
    "notes": "gia đình muốn em học gần nhà"
  },
  "evidence_quotes": [ { "turn": 3, "quote": "em hay sửa đồ điện trong nhà", "mapped_to": "ky_thuat" } ],
  "experiences": [
    { "title": "Dashboard bán hàng", "kind": "project", "description": "dashboard từ dữ liệu mở", "skills": ["Excel"], "source_quote": "em đã làm dashboard…" }
  ],
  "completeness": 0.6              // 0..1 — FE dùng cho progress indicator
}
```

> ⚠️ Profile **KHÔNG có field giới tính** — cố ý (anti-bias by design). Không thêm.

---

## 3. Recommendations

### `POST /api/recommendations`

Request: `{ "session_id": "…" }`

Trả `404` nếu session không tồn tại; FE phải đưa người dùng về `/explore`, không sinh gợi ý generic rồi gắn nhãn cá nhân hóa.
Trả `409` nếu session đã mở nhưng profile chưa có personal evidence (skill/interest/experience/job goal hoặc dimension đủ mạnh); FE hiển thị retry + CTA tạo/tiếp tục hồ sơ, không trả market-only ranking dưới nhãn cá nhân hóa.

Response:
```json
{
  "generated_at": "2026-07-18T10:00:00Z",
  "disclaimer": "Đây là gợi ý tham khảo dựa trên hồ sơ của em và dữ liệu thị trường — quyết định là của em.",
  "recommendations": [ Recommendation, … ],   // 5 phần tử, xếp theo match_score giảm dần
  "stretch": Recommendation                    // 1 gợi ý "có thể em chưa nghĩ tới"
}
```

### Schema `Recommendation`

```json
{
  "career_id": "ky-thuat-vien-dien-lanh",
  "title": "Kỹ thuật viên điện lạnh",
  "match_score": 0.86,
  "is_stretch": false,
  "why": {
    "from_you": [
      { "quote": "em hay sửa đồ điện trong nhà", "reason": "cho thấy thiên hướng thực hành-kỹ thuật rõ" }
    ],
    "from_market": [
      { "stat": "412 tin tuyển trong 90 ngày tại Đà Nẵng", "stat_key": "demand_count" },
      { "stat": "Khoảng lương quan sát 9–15 triệu, trung vị 12 triệu", "stat_key": "salary" }
    ],
    "counterfactual": "Nếu em thiên về sáng tạo hơn thực hành, gợi ý đầu bảng sẽ là Thiết kế nội thất."
  },
  "market": {
    "demand_count_90d": 412,
    "entry_level_count_90d": 96,              // posting được rule-label entry/fresher; 0 nếu chưa build được
    "salary_p25_trieu": 9, "salary_p50_trieu": 12, "salary_p75_trieu": 15,
    "trend_pct": 23,                          // % thay đổi demand 45 ngày sau vs 45 ngày trước
    "salary_sample_count": 86,                // số posting có lương dùng tính percentile
    "low_confidence": false,                  // true → FE phải hiện cảnh báo/ẩn claim trend
    "top_regions": ["danang", "hcm"],
    "top_skills": ["điện lạnh dân dụng", "đọc sơ đồ mạch", "kỹ năng khách hàng"],
    "source_note": "Từ 3.412 tin tuyển dụng trong snapshot nguồn đã duyệt, 90 ngày gần nhất"
  },
  "routes": [
    {
      "type": "vocational",                    // university | college | vocational | certificate
      "label": "Trung cấp nghề Điện lạnh (18–24 tháng)",
      "detail": "Trường CĐ nghề Đà Nẵng hoặc tương đương; vừa học vừa làm từ năm 2",
      "first_steps": ["Tìm hiểu ngày tuyển sinh trường nghề gần em", "Xin phụ việc tiệm điện lạnh dịp hè"]
    },
    { "type": "college", "label": "Cao đẳng Điện — Điện lạnh (2.5–3 năm)", "detail": "…", "first_steps": ["…"] }
  ],
  "skill_roadmap": [
    { "skill": "điện cơ bản", "status": "nen-hoc-truoc" },
    { "skill": "điện lạnh dân dụng", "status": "hoc-trong-truong" }
  ],
  "job_readiness": null            // object bên dưới khi Profile.journey_mode=launch
}
```

### Schema `JobReadiness` (chỉ cho Launch mode)

```json
{
  "band": "near_ready",            // ready_now | near_ready | build_foundation; KHÔNG phải xác suất được tuyển
  "band_reason": "Bạn đã có bằng chứng Excel qua project nhưng chưa có SQL trong profile.",
  "matched_skills": [ { "skill": "Excel", "evidence": "Project Dashboard bán hàng" } ],
  "missing_skills": ["SQL"],       // tập con market.top_skills và không trùng matched_skills
  "search_queries": ["data analyst intern", "junior reporting analyst"],
  "actions_30d": [
    { "week": 1, "action": "Hoàn thiện dashboard", "deliverable": "1 link project + 3 insight", "why": "Tạo evidence cho Excel và data cleaning" }
  ]
}
```

Launch hard rules:

- `matched_skills[*].evidence` phải truy về `Profile.skills.source_quote` hoặc `Profile.experiences`.
- `missing_skills` chỉ lấy từ role/market top skills; không bịa requirement.
- Mỗi action có deliverable kiểm chứng được; không trả lời chung chung “học thêm”.
- `band` không được diễn đạt như xác suất được tuyển; không dùng GPA/trường/giới tính/vùng để hạ band.

Ràng buộc BE phải đảm bảo (FE được phép assume):
- `routes.length ≥ 2` và **luôn có ≥1 route** với `type ∈ {vocational, college, certificate}`.
- Mọi số trong `why.from_market` tồn tại trong `market.*` (không bịa).
- `stretch.is_stretch = true` và có `why.counterfactual` giải thích vì sao đáng cân nhắc.

---

### `POST /api/recommendations/what-if` — preview một kỹ năng giả định

Request: `{ "session_id": "…", "skill": "SQL" }`.

Response gồm `mutation_label`, `original_profile_unchanged=true`, danh sách `deltas`
(`career_id`, rank/score trước và sau) và một `preview: RecommendationResponse` đầy đủ.

Hard rules: đúng một kỹ năng mỗi request; chạy trên deep copy; không persist session;
giả định không được diễn đạt thành bằng chứng người dùng đã có; recommendation vẫn do
deterministic core tạo. Lỗi preview không được làm thay đổi hồ sơ gốc.
Trả `404` nếu session không tồn tại và `409` nếu profile chưa có personal evidence; không
sinh preview generic từ một hồ sơ trống.

---

## 4. Market Intelligence

### `GET /api/market/overview?region={all|hanoi|hcm|danang}`

```json
{
  "region": "danang",
  "postings_count": 1214,
  "window_days": 90,
  "updated_at": "2026-07-18",
  "source_note": "Từ 1.214 tin tuyển dụng, snapshot 18/07/2026",
  "rising_careers": [ { "career_id": "…", "title": "…", "trend_pct": 34, "demand_count": 210, "low_confidence": false } ],
  "top_paying": [ { "career_id": "…", "title": "…", "salary_p50_trieu": 25 } ]                      // top 5
}
```

### `GET /api/market/skills?region={…}` — Radar nhu cầu kỹ năng (hiring-demand proxy)

```json
{
  "region": "danang",
  "source_note": "Từ 612 tin tuyển dụng tại Đà Nẵng, snapshot 18/07/2026",
  "skills": [
    {
      "skill": "điện lạnh dân dụng",
      "gap_score": 0.82,            // 0..1 — công thức xem AI_DESIGN.md §3
      "demand_count": 412,
      "trend_pct": 23,
      "low_confidence": false,
      "related_careers": ["ky-thuat-vien-dien-lanh"]
    }
  ]                                  // top 20, sort gap_score desc
}
```

### `GET /api/market/careers/{career_id}?region={…}` → `CareerDetail`

```json
{ "career_id": "…", "title": "…", "description": "…", "market": { …MarketStats }, "routes": [ …Route ] }
```

---

## 4.1 Career Research — nguồn kiểm chứng sau recommendation

`POST /api/research/careers`

```json
{
  "session_id": "…",
  "career_ids": ["data-analyst"],
  "intent": "skills",
  "region": "hcm"
}
```

- `career_ids`: 1–2 ID và bắt buộc thuộc top-5/stretch của chính session.
- Trả `404` nếu session không tồn tại và `409` nếu profile chưa có personal evidence; research
  chỉ là bước sau recommendation, không tự tạo candidate generic cho session trống.
- `intent`: `overview | skills | routes | local_market`.
- Không gửi tên, giới tính, trường, GPA, raw transcript hoặc profile text ra search provider.
- Response gồm `status`, `generated_at`, `limitation`, `disclaimer` và từng career block có
  `local_market: MarketStats` + `sources[]` (`title`, `url`, `domain`, `snippet`,
  `source_tier`, `retrieved_at`).
- `status = live | cached | replay | unavailable`.

Search không được đổi candidate order, score, profile hoặc market snapshot. Chỉ URL
`http/https` công khai đã sanitize được trả về; lỗi/timeout chuyển thành local-only response,
không 5xx. DDGS là community adapter miễn phí/không API key, không phải API chính thức của DuckDuckGo.

---

## 5. Quy ước chung

### Format lỗi (mọi status ≠ 2xx — BE đã có exception handler chung trong `main.py`)

```json
{ "error": { "code": "404", "message": "career not found" } }
```

- `code` là **string** (mã HTTP dạng chuỗi). 422 trả message cố định "Dữ liệu gửi lên không hợp lệ"; 500 trả "Có lỗi xảy ra, vui lòng thử lại" (chi tiết chỉ ghi log server, không leak ra FE).
- FE bắt lỗi và hiện fallback tiếng Việt thân thiện — không bao giờ hiện raw stack/error tiếng Anh cho học sinh.


- Region enum: `hanoi | hcm | danang | other | all`. Route type enum: `university | college | vocational | certificate`.
- Lương đơn vị **triệu VND/tháng**, số nguyên hoặc 1 chữ số thập phân.
- `demand_count` là số posting trong snapshot, không phải số vacancy hoặc bằng chứng trực tiếp của thiếu hụt lao động. `gap_score` là hiring-demand proxy; UI không được gọi là đo cung–cầu.
- `low_confidence=true` → FE hiện “dữ liệu còn hạn chế” và không dùng trend trong headline. `salary_sample_count < 5` → ba percentile lương phải là null.
- Mọi text hiển thị cho user do BE trả về là **tiếng Việt**.
- FE tự sinh `session_id` (uuid v4) lần đầu vào `/explore`, giữ trong localStorage key `cc_session_id`.
- Trước khi persist hoặc gửi model, backend loại tên thật khai báo trực tiếp, che email/số điện thoại/API key và loại gender/GPA/school-prestige proxy khỏi turn; không commit/log raw transcript chứa các identifier này. Turn sau khi sanitize chỉ còn identifier/marker thì không tăng `turn`, phase hay completeness và được hỏi lại bằng câu an toàn.
