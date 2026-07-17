# 🧭 CareerCompass — AI Career Guidance từ dữ liệu tuyển dụng thật

> **TitanHack 48h — Đề bài "Career compass" (Duy Tan University)**
> Hệ thống hướng nghiệp AI kết nối **năng lực, sở thích và project/experience của người học Việt Nam** với **tín hiệu thật từ thị trường lao động**. Hai journey: **Explore** chọn hướng học/nghề; **Graduate Launch** chuyển sang nhóm việc entry-level, skill gaps và kế hoạch 30 ngày.

## Đọc gì trước tiên?

| File | Dành cho | Nội dung |
|---|---|---|
| [PLAN.md](PLAN.md) | **Cả team — đọc đầu tiên** | MVP, in/out-scope, timeline 48h, milestones, rủi ro |
| [docs/TASKS.md](docs/TASKS.md) | Từng thành viên | Task breakdown chi tiết M1–M6, dependencies, handoff |
| [docs/HANDOFF.md](docs/HANDOFF.md) | Cả team | Template bàn giao + artifact registry + integration order |
| [docs/BUSINESS_CASE.md](docs/BUSINESS_CASE.md) | Product/Pitch | Bài toán tổ chức, buyer, KPI pilot, value proposition |
| [docs/AI_FOCUS.md](docs/AI_FOCUS.md) | Cả team/Pitch | AI dùng ở đâu, chứng minh chất lượng bằng gì, ứng dụng sản phẩm vào đâu |
| [docs/AGENTIC_RUNTIME.md](docs/AGENTIC_RUNTIME.md) | AI/Backend/FE | Bounded ReAct: tool typed, policy gate, budget, fallback và red-team evaluation |
| [docs/EVALUATION.md](docs/EVALUATION.md) | AI/Data/Lead | Quality gates định lượng và report bắt buộc |
| [docs/SECURITY_PRIVACY.md](docs/SECURITY_PRIVACY.md) | Cả team | Dữ liệu học sinh, nguồn crawl, release checklist |
| [docs/GRADUATE_LAUNCH.md](docs/GRADUATE_LAUNCH.md) | Product/AI/FE | Scope sinh viên sắp/đã tốt nghiệp tìm hướng việc làm |
| [docs/AGENT_WORKFLOW.md](docs/AGENT_WORKFLOW.md) | Cả team dùng AI | Context bootstrap, file ownership, Builder–Reviewer–Verifier, cost control |
| [docs/FEATURE_ROADMAP.md](docs/FEATURE_ROADMAP.md) | M1 | Feature được phép mở sau khi core pass |
| [docs/PREFLIGHT.md](docs/PREFLIGHT.md) | M1 + cả team | Gate bắt buộc trước khi bấm giờ 48h |
| [docs/workstreams/](docs/workstreams/) | M1–M6 | Task card chi tiết riêng từng người: output, test, risk, fallback, handoff |
| [docs/TEAM_RULES.md](docs/TEAM_RULES.md) | Cả team | Git workflow, quy tắc làm việc, quy tắc dùng AI |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Dev | Kiến trúc hệ thống, data flow, scalability |
| [docs/API_CONTRACT.md](docs/API_CONTRACT.md) | FE + BE | Contract API — **nguồn chân lý duy nhất** giữa FE/BE |
| [docs/AI_DESIGN.md](docs/AI_DESIGN.md) | AI engineers | Thiết kế profiling, recommendation, explainability, anti-bias |
| [docs/DATA_PIPELINE.md](docs/DATA_PIPELINE.md) | Data engineer | Crawl → normalize → extract skills → market stats |
| [CLAUDE.md](CLAUDE.md) | AI assistants | Context cho Claude/Cursor/Copilot của mọi thành viên |
| [scripts/dev.md](scripts/dev.md) | Dev | Runbook setup, test, mode mock/live/replay, troubleshoot |

## Quickstart (5 phút)

### Backend (FastAPI — Python 3.11+)
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy ..\.env.example .env        # rồi điền API keys
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/docs (Swagger UI, có sẵn mock data)
```

### Frontend (Next.js — Node 20+)
```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Data pipeline
```bash
cd data
pip install -r ../backend/requirements.txt
python pipeline/crawl_topcv.py        # xem docs/DATA_PIPELINE.md
```

## Cấu trúc repo

```
├── frontend/    # Next.js 15 + Tailwind — UI chat profiling, dashboard kết quả
├── backend/     # FastAPI — API chat, recommendation, market stats
├── data/        # Pipeline crawl & xử lý job postings + dataset
├── docs/        # Toàn bộ tài liệu dự án
├── PLAN.md      # Kế hoạch tổng 48h
└── CLAUDE.md    # Context chung cho AI assistants
```

## Nguyên tắc vàng (tóm tắt — chi tiết ở TEAM_RULES.md)

1. **Không push thẳng lên `main`** — luôn tạo branch + PR.
2. **API_CONTRACT.md là luật** — FE code theo contract với mock, BE implement đúng contract. Muốn đổi contract → báo Team Lead.
3. **Mock trước, integrate sau** — không ai bị block chờ người khác.
4. **Trước khi nhờ AI code**: paste nội dung CLAUDE.md + task ID của bạn vào context.
5. **Sync 10 phút mỗi 4 tiếng** — theo lịch trong PLAN.md.
6. **Không gọi demand là thiếu hụt cung–cầu** — mọi claim phải đúng với biến dữ liệu thực sự đo được.
7. **AI task chưa chạy test = chưa done** — dùng workflow Builder–Reviewer–Verifier và handoff có consumer xác nhận.
