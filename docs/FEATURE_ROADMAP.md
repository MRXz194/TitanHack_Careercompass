# FEATURE ROADMAP — chỉ mở sau khi P0/P1 pass

## Rule mở feature

Không làm feature mới chỉ vì “còn vẻ đẹp”. M1 chỉ mở một item khi: P0 E2E 3 lần pass, replay pass, không Sev-1/2, quality gates core có kết quả, và item có owner + timebox + rollback.

## Nếu hoàn thiện sớm trong 48h

| Priority | Feature | Giá trị | Timebox | Test/rollback |
|---|---|---|---:|---|
| E1 | Compare 2 careers/roles | Giúp autonomy, không ép top-1 | 2h | compare chỉ field contract; remove route |
| E2 | Export counselor summary HTML/print | Dùng trong tư vấn thật | 2h | không PII; browser print; bỏ nếu layout lỗi |
| E3 | Data confidence tooltip nâng cao | Tăng trust/judge defense | 1h | low sample cases |
| E4 | Save anonymous local session | User quay lại trong demo | 1h | clear session; không server account |
| E5 | Launch action check-off local-only | Tăng khả năng thực hiện bước đầu | 1h | localStorage + clear; no account/analytics |

## Sau hackathon — product

| Horizon | Feature | Dependency/gate |
|---|---|---|
| Pilot | Counselor dashboard, cohort aggregate, review notes | consent, RBAC, school DPA, ≥30-user pilot |
| Pilot | Vacancy-level search links | source permission/API, freshness SLA, dedupe |
| Pilot | CV/project evidence import | privacy threat model, user confirmation, no automated rejection |
| Scale | Daily incremental pipeline | scheduler, observability, source contracts |
| Scale | Postgres/pgvector + Redis sessions | load test proves SQLite/in-memory bottleneck |
| Scale | Curriculum/supply data | partnership/license; required before claiming true skill shortage |
| Scale | Outcome feedback loop | consent, bias monitoring, no optimize solely for salary/placement |
| Scale | School/region dashboards | minimum cohort size, privacy aggregation, fairness review |

## Explicitly deferred

Auto-apply, candidate ranking for employers, prediction of hiring probability, school/GPA prestige scoring, psychometric diagnosis, and opaque “best career” labels are not natural extensions without a separate ethics/security review.
