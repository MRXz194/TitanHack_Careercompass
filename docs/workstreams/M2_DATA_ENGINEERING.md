# M2 — Data Engineering, Provenance, QA

**Mission:** tạo snapshot hiring data hợp lệ, tái chạy được và đủ provenance để mọi con số truy ngược. Không tối đa count bằng mọi giá.

**Owned:** `data/pipeline/crawl*`, `normalize.py`, raw/processed schema, manifest/data card. **Buddy:** M3.

## Task cards

### D-01 — Source reconnaissance và quyền sử dụng (H+0→2)
- **Actions:** robots/terms/license; schema/HTML/API; vùng/ngày/lương; rate behavior; mark `allowed|unclear|blocked`.
- **Expected:** Notes có URLs, selector/API hypothesis, sample 5 records, source decision.
- **Verify:** không cần login/CAPTCHA/bypass; M1 approve trước bulk crawl.
- **Fallback:** nguồn unclear/blocked → dataset mở có license; không reverse-engineer access control.

### D-02 — Source #1 crawler (H+2→8)
- **Actions:** pagination, region/category queries, polite delay, retry bounded, checkpoint/resume, raw JSONL append-safe.
- **Expected:** ≥500 raw target; required raw fields; crawl summary/error count.
- **Tests:** parser fixture HTML; duplicate run không nhân bản; interrupt/resume; 403/429 stops.
- **Risk/fallback:** DOM đổi → save sample + selector adapter; source fail → next allowed source.
- **Handoff:** raw schema/sample/report → D-04 and M1 H+10.

### D-03 — Source #2 adapter (H+8→14)
- **Actions:** map source-specific fields về cùng raw schema; không fork normalize logic.
- **Expected:** target total 3k, ≥2 sources; source field/URL intact.
- **Tests:** contract fixture for both sources; missing salary/date handled; no source collision in IDs.
- **Fallback:** one allowed source + open dataset; manifest nói rõ mix/snapshot dates.

### D-04 — Normalize/dedupe (H+12→18)
- **Actions:** Unicode; salary/currency config; dates; region; experience years + entry/mid/senior/unknown label with reason; cleaning/dedupe/reject.
- **Expected:** `postings.jsonl` + report in/out/drop/dedupe/salary/date/region/experience/seniority coverage.
- **Tests:** table-driven salary/date/region/experience; fresher/không yêu cầu; idempotence; null vs zero; deterministic hash.
- **Risk:** false dedupe → conservative threshold + keep source IDs; no silent delete.

### D-05 — Dataset handoff (H+18→20)
- **Actions:** freeze snapshot ID/hash/schema; package artifact; list caveats and sample query.
- **Expected:** M3 can read with one command; no local absolute path; manifest linked.
- **Verify:** M3 runs count/schema check and replies ✅; hash matches.

### D-06 — Data QA sample (H+20→26)
- **Actions:** stratified 30/source + regions; compare raw→normalized; quantify parse errors.
- **Expected:** error categories, actual accuracy sample, fixes/re-run if severe.
- **Verify:** salary/date/region/title/source URL spot checks; each region target or caveat.
- **Fallback:** low-quality field hidden/null; never repair by invented value.

### D-07 — Career KB coverage (H+20→26)
- **Actions:** inspect unmapped titles; add P0 career families, vocational routes, `entry_role_aliases`, top skills/action templates; P0 25 before P2 40–60.
- **Expected:** ≥85% mapping coverage or documented long tail; every career ≥2 routes, ≥1 non-university.
- **Tests:** unique IDs/patterns; route script; no route names/claims without review.
- **Handoff:** KB hash → M3 embeddings and M4 pathways.

### D-08 — Aggregate traceability (H+30→36)
- **Actions:** manually recompute 10 career×region stats from posting IDs.
- **Expected:** demand/salary/trend match builder; discrepancy log.
- **Verify:** percentile sample count, date windows, duplicate exclusion, low-confidence.
- **Fallback:** fail aggregate removed from UI/claim until fixed.

### D-09 — Pitch insights (H+36→42)
- **Actions:** select 3–5 defensible insights only from measured variables.
- **Expected:** query/formula, numerator/denominator, n, source/date, limitation.
- **Verify:** M3 reproduces; M1 claim audit.
- **Forbidden:** infer schools do not teach, worker shortage or causality without supply/curriculum data.

### D-10 — Data card/provenance manifest (H+18→22)
- **Actions:** fill `DATA_SNAPSHOT.md` + machine manifest with sources, terms/license, time, count, hash, coverage, limitations.
- **Expected:** UI/report count comes from meta/manifest, not hardcode.
- **Tests:** hash artifact; counts sum; URLs present; blocked source absent.
- **Handoff:** manifest → M1/M3/M6/pitch.

## Data incident rules

- 403/429: stop source; do not rotate identities or bypass.
- Date window insufficient: trend null/low-confidence, not zero.
- Salary coverage <5 samples: percentiles null.
- Source dominates >70% or region <10%: report bias; do not claim national representativeness.
