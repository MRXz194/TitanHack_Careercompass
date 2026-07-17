# 📜 API CONTRACT — Nguồn chân lý FE ↔ BE

> **Freeze tại H+8.** Muốn đổi: theo quy trình TEAM_RULES.md §2. Đổi contract = sửa file này + `backend/app/models/schemas.py` + `frontend/types/index.ts` trong CÙNG 1 PR.
>
> Base URL: local `http://localhost:8000` · Mọi endpoint prefix `/api`. Mọi lỗi trả `{ "error": { "code": string, "message": string } }` với HTTP status phù hợp.

---

## 1. Health

`GET /api/health`

```json
{ "status": "ok", "llm_ok": true, "data_loaded": true, "postings_count": 3412 }
```

---

## 2. Chat Profiling

### `POST /api/chat`

Request:
```json
{
  "session_id": "uuid-do-FE-tu-sinh-va-giu-trong-localStorage",
  "message": "Em thích vẽ và hay sửa đồ điện trong nhà"   // null cho lượt mở đầu
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

### `PATCH /api/profile/{session_id}` — học sinh sửa tay profile (autonomy)

Request (gửi phần muốn sửa):
```json
{
  "dimensions": { "ky_thuat": 0.9 },
  "remove_skills": ["python"],
  "add_interests": ["thiết kế nội thất"]
}
```
Response: `{ "profile": Profile }`

### Schema `Profile`

```json
{
  "session_id": "…",
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
  "completeness": 0.6              // 0..1 — FE dùng cho progress indicator
}
```

> ⚠️ Profile **KHÔNG có field giới tính** — cố ý (anti-bias by design). Không thêm.

---

## 3. Recommendations

### `POST /api/recommendations`

Request: `{ "session_id": "…" }`

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
      { "stat": "Lương phổ biến 9–15 triệu, thợ giỏi 20+ triệu", "stat_key": "salary" }
    ],
    "counterfactual": "Nếu em thiên về sáng tạo hơn thực hành, gợi ý đầu bảng sẽ là Thiết kế nội thất."
  },
  "market": {
    "demand_count_90d": 412,
    "salary_p25_trieu": 9, "salary_p50_trieu": 12, "salary_p75_trieu": 15,
    "trend_pct": 23,                          // % thay đổi demand 45 ngày sau vs 45 ngày trước
    "top_regions": ["danang", "hcm"],
    "top_skills": ["điện lạnh dân dụng", "đọc sơ đồ mạch", "kỹ năng khách hàng"],
    "source_note": "Từ 3.412 tin tuyển dụng TopCV + VietnamWorks, 90 ngày gần nhất"
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
  ]
}
```

Ràng buộc BE phải đảm bảo (FE được phép assume):
- `routes.length ≥ 2` và **luôn có ≥1 route** với `type ∈ {vocational, college, certificate}`.
- Mọi số trong `why.from_market` tồn tại trong `market.*` (không bịa).
- `stretch.is_stretch = true` và có `why.counterfactual` giải thích vì sao đáng cân nhắc.

---

## 4. Market Intelligence

### `GET /api/market/overview?region={all|hanoi|hcm|danang}`

```json
{
  "region": "danang",
  "postings_count": 1214,
  "window_days": 90,
  "updated_at": "2026-07-18",
  "rising_careers": [ { "career_id": "…", "title": "…", "trend_pct": 34, "demand_count": 210 } ],  // top 8
  "top_paying": [ { "career_id": "…", "title": "…", "salary_p50_trieu": 25 } ]                      // top 5
}
```

### `GET /api/market/skills?region={…}` — Skill Gap Radar

```json
{
  "region": "danang",
  "skills": [
    {
      "skill": "điện lạnh dân dụng",
      "gap_score": 0.82,            // 0..1 — công thức xem AI_DESIGN.md §3
      "demand_count": 412,
      "trend_pct": 23,
      "related_careers": ["ky-thuat-vien-dien-lanh"]
    }
  ]                                  // top 20, sort gap_score desc
}
```

### `GET /api/market/careers/{career_id}?region={…}` → object `market` (schema như trong Recommendation) + `title`, `description`, `routes`.

---

## 5. Quy ước chung

- Region enum: `hanoi | hcm | danang | other | all`. Route type enum: `university | college | vocational | certificate`.
- Lương đơn vị **triệu VND/tháng**, số nguyên hoặc 1 chữ số thập phân.
- Mọi text hiển thị cho user do BE trả về là **tiếng Việt**.
- FE tự sinh `session_id` (uuid v4) lần đầu vào `/explore`, giữ trong localStorage key `cc_session_id`.
