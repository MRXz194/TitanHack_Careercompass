# Data Snapshot Audit — 2026-07-18

Status: **acquisition + deterministic candidate build complete; runtime aggregate not approved**. Snapshot này đã qua normalize/extract/map candidate nhưng chưa được copy sang `backend/market.db` vì mapping accuracy còn `NOT_RUN` và region `other` chiếm 76,9%.

## 0. Candidate build result

| Stage | Result |
|---|---|
| Raw → normalized | 3.914 → 3.865; dedupe 49; chạy lặp 2 lần cùng SHA-256 `4ecfc1a513fea9eb451e61cbed4825b64385cf8a75d746cc2606dc5be0e83806` |
| Skill extraction | 3.532/3.865 có skill; 333 zero-skill; trung bình 4,714 skill/post; dictionary-only, 0 LLM call |
| Career mapping | 1.031/3.865 (26,68%) vào 25 career families; accuracy `NOT_RUN`; 1 ambiguous |
| Release decision | `CANDIDATE_NOT_RELEASED`; giữ nguyên `backend/market.db` đã kiểm chứng |

Manifest và card canonical: `data/processed/manifest.json`, `docs/DATA_SNAPSHOT.md`. Full-text artifacts vẫn gitignored.

## 1. Acquisition result

| Source | Requested cap | Public inventory discovered | Attempted in final run | Resumed | Usable unique | Parse errors | Blocked | Stop reason |
|---|---:|---:|---:|---:|---:|---:|---|---|
| VietnamWorks | 3.000 | 10.441 | 3.841 | 400 | 3.000 | 1.241 | no | requested limit reached |
| ITviec | 3.000 | 886 | 786 | 100 | 886 | 0 | no | public inventory exhausted |
| TopCV | 1.000 | not retained in retry report | 0 in retry | 28 | 28 | 0 in retry | **yes** | HTTP 403 |
| **Total** | — | — | — | — | **3.914** | — | — | — |

Interpretation:

- VietnamWorks đạt đúng cap 3.000 usable; không có HTTP error/block trong final run.
- ITviec chỉ có 886 public job-detail URLs ở snapshot, nên 886 là toàn inventory công khai quan sát được, không tạo duplicate để đạt 3.000.
- TopCV lấy được 28 record ở run đầu rồi source trả 403. Sau cooldown, retry bị 403 ngay ở sitemap và crawler dừng; không proxy/CAPTCHA/cookie bypass. Nguồn này là **partial**, không đại diện và không được dùng riêng để suy trend.
- TopCV retry report ghi run hiện tại (`discovered=0`, `attempted=0`, `resumed=28`) và đã ghi đè report đầu. N2-00 phải bổ sung run history/cumulative metrics trước lần crawl tiếp theo.

## 2. Integrity và hashes

| Source | Rows | Unique IDs | Unique URLs | Canonical snapshot hash trong crawler report | Raw file SHA-256 |
|---|---:|---:|---:|---|---|
| VietnamWorks | 3.000 | 3.000 | 3.000 | `387352e26196c6d1b929d82584ace854139e4f5d5c964e0a1c74ed9e9ea9f494` | `4c1cf9fc5c3fbb7f6dd5d6f791eb03a6fc424d571b524f913c1f139c4e1c9779` |
| ITviec | 886 | 886 | 886 | `edc472a8904927d3e41292eb7aac08d0d51f500332b03051fb5890326eb21729` | `7f9c7d070913adaffdcc2cc170a972cc934d4a51be2a7ab332f97657962fb9f3` |
| TopCV | 28 | 28 | 28 | `e1bb69174ea743c6595ce2b3b64fc7b85c39eb064d7803ce4d354856debef9af` | `231652d19b8a078a2fb23c8b58f39f3af38b216b28dc874b29402c618de4e5ba` |
| **Total** | **3.914** | **3.914** | **3.914** | — | — |

Canonical hash là SHA-256 của records đã sort theo stable ID và serialize canonical; raw file hash là SHA-256 byte-for-byte của JSONL. Hai hash có mục đích khác nhau nên không kỳ vọng giống nhau.

ID/URL uniqueness pass, nhưng exact normalized `title + company` vẫn có 8 group lặp, tổng 17 rows. Đây có thể là cùng vacancy đăng nhiều nguồn hoặc title chung; N2-01 phải dedupe/spot-check trước aggregate, không coi unique URL là unique labor-demand event.

## 3. Raw-field diagnostics

Các chỉ số dưới đây chỉ kiểm tra raw field có cấu trúc sơ bộ; **không phải coverage đã normalize**.

| Source | Description ≥100 | Skills non-empty | Salary raw chứa số | Region raw có chữ | Posted date ISO-like | Distinct posted dates |
|---|---:|---:|---:|---:|---:|---:|
| VietnamWorks | 3.000/3.000 (100%) | 2.974/3.000 (99,1%) | 1.203/3.000 (40,1%) | 0/3.000 (0%) | 3.000/3.000 (100%) | 14 |
| ITviec | 886/886 (100%) | 886/886 (100%) | 230/886 (26,0%) | 886/886 (100%) | 886/886 (100%) | 44 |
| TopCV | 28/28 (100%) | 18/28 (64,3%) | 25/28 (89,3%) | 28/28 (100%) | 28/28 (100%) | 1 |

### Blockers phải đóng trước publish

1. **VietnamWorks region:** `region_raw` là location ID số, không phải tên vùng. Current `map_region()` sẽ đưa toàn bộ về `other`. Cần versioned ID lookup + fixture/spot-check; nếu chưa có thì suppress region của nguồn này.
2. **ITviec salary:** 656/886 salary raw không có số; phần lớn là marketing/benefit copy hoặc undisclosed salary. Parser mới ở commit `cf32f56` đã từ chối non-numeric JSON-LD salary, nhưng snapshot đã crawl phải được normalization đưa về null/“thỏa thuận”.
3. **TopCV partial/date:** 28 records có cùng một posted date và source bị 403. Không dùng nguồn này để tính trend hoặc claim representation.
4. **Cross-source duplicates:** 8 exact normalized title-company groups/17 rows cần review và dedupe event-level.
5. **Normalizer safety/performance — CLOSED:** fuzzy dedupe dùng blocking key, output atomic, input/tie-break deterministic; manifest có safe `--help`/`--dry-run` và test no-side-effect.
6. **Source-mix bias:** ITviec chuyên IT, VietnamWorks rộng hơn và TopCV partial. Aggregate phải kèm source counts/diversity; không diễn giải source coverage như demand difference.

## 4. Claim decision tại thời điểm audit

| Claim/signal | Decision | Lý do |
|---|---|---|
| Tổng public postings quan sát được | allowed với snapshot date/source/count | integrity/hash pass |
| Skill frequency | pending extraction + held-out QA | raw explicit skills không đồng nhất giữa nguồn |
| Salary percentile | blocked đến khi normalize/sample gate pass | coverage thấp và IT metadata polluted |
| Region comparison | blocked | VietnamWorks location IDs chưa map |
| Trend | blocked đến khi date/source window QA pass | TopCV partial; retention/snapshot bias cần limitation |
| “Skill shortage” | prohibited | job postings chỉ là observed demand, không có supply-side evidence |
| Recommendation score | không bị web/raw crawl thay đổi trực tiếp | chỉ dùng versioned aggregate sau N3 gate |

## 5. Security, storage và compliance

- Crawler chỉ dùng public sitemap/detail pages; không cookie, auth token, login, proxy hoặc CAPTCHA bypass.
- Tracked secret scan không thấy `auth_token`, `cf_clearance`, hard-coded cookie hoặc key pattern.
- `data/raw/*` được `.gitignore`; Git chỉ track `data/raw/.gitkeep`.
- Không commit raw descriptions/company-level dataset. Team khác nhận aggregate/manifest/report; M2 là owner duy nhất cần raw local để rebuild.
- Source 401/403/429/CAPTCHA phải dừng và ghi limitation; không retry liên tục trong cùng session.

## 6. Verification evidence

| Check | Result |
|---|---|
| Crawler parser/resume unit | `7 passed` |
| Backend full suite | `347 passed` |
| Frontend typecheck | PASS |
| Frontend Vitest | `64 passed` |
| Frontend production build | PASS; route table lists 6 app routes |
| Task ID consistency | 23 task IDs, all references valid, no duplicate ID |
| Markdown local links / diff whitespace | PASS |
| Tracked secret scan / raw ignore | PASS |

## 7. Handoff và next commands

Owner M2/M3 nhận quality follow-up:

1. Tạo gold labels độc lập cho ít nhất 50 postings và đo mapping accuracy; coverage không thay thế accuracy.
2. Bổ sung versioned VietnamWorks location-ID mapping hoặc tiếp tục suppress regional claim cho nguồn này.
3. Chạy salary/route spot-check và aggregate trace; chỉ sau reviewer sign-off mới rebuild/publish `backend/market.db`.
4. Không commit enriched raw descriptions; chỉ commit manifest/report/aggregate được phê duyệt.

Owner M1 phải giữ `WEB_RESEARCH_MODE=off` ở baseline. Career Research/DuckDuckGo chỉ là P1 sau H+17 và không phụ thuộc snapshot raw trong request path.
