# M3 — Market Intelligence AI, Taxonomy, Stats, Embeddings

**Mission:** biến snapshot thành skill/role signals đo được, có confidence và interface ổn định cho M4/M6.

**Owned:** taxonomy, extraction, career mapping, stats DB, embeddings, `services/market.py`. **Buddy:** M2; consumer M4/M6.

## Card contract

Mỗi task phải làm rõ artifact đầu ra, input hash/version, tests/metrics, risk/fallback và consumer
handoff. Với task không lặp dòng `Problem`, mission + task title là problem boundary; mọi metric
phải có denominator, command và limitation theo `TESTING.md`/`EVALUATION.md`.

## Task cards

### MI-01 — Vietnamese skill taxonomy v1 (H+0→5)
- **Actions:** canonical skill + aliases VI/EN; categories technical/tool/domain/soft; normalize case/Unicode; exclude vague requirements.
- **Expected:** ~300 skills target, version field/hash, unique canonical/aliases.
- **Tests:** JSON/schema; alias collision; empty/duplicate; 30 common posting phrases.
- **Risk/fallback:** P0 120–150 high-frequency skills before long tail; quality > count.
- **Handoff:** taxonomy version → MI-02/M4.

### MI-02 — Hybrid extraction + gold evaluation (H+2→10)
- **Actions:** dictionary baseline; LLM only low-signal records; create 100-posting stratified gold; batch/cache/hash.
- **Expected:** enriched sample, precision/recall/F1, cost/1k, failure categories.
- **Tests:** deterministic dictionary tests; gold metrics; malformed JSON retry/fallback; no skill outside taxonomy unless `new_skills`.
- **Fallback:** precision below target → dictionary-only for UI + log candidates; do not display noisy LLM skills.

### MI-03 — Full extraction/career mapping (H+20→25)
- **Actions:** consume D-05 hash; resume batches; map title patterns then bounded LLM fallback; record unmapped/new skill.
- **Expected:** every posting has `skills[]`, `career_id|unmapped`, extraction version.
- **Tests:** resume without duplicate/cost; 50-sample mapping accuracy; coverage by source/region; input hash guard.
- **Fallback:** mapping <85% → family-level career IDs; unmapped excluded from career stats but counted in manifest.

### MI-04 — Market stats database/API (H+25→29)
- **Actions:** aggregate demand + entry-level count, salary n/p25/p50/p75, two-window trend, top skills, source meta; implement SQLAlchemy reads.
- **Expected:** `market.db` + meta; live API response contract; seed fallback explicit.
- **Tests:** fixture aggregate; entry label QA; D-08 trace; empty region; <5 salary null; low-confidence trend; no raw JSON scan per request.
- **Fallback:** trend invalid → demand-only; DB build fail → validated aggregate JSON adapter, same API.

### MI-05 — Hiring-demand proxy (H+29→32)
- **Actions:** normalize demand/trend within region; confidence-aware formula; related roles; write skill stats.
- **Expected:** top 20 per region + formula/source/low-confidence.
- **Tests:** score 0..1; monotonic demand fixture; missing trend; tiny n; UI copy contract.
- **Forbidden:** call proxy labor shortage or supply gap.
- **Fallback:** demand-only ranking with limitation.

### MI-06 — Career embeddings in two handoffs (H+6→12, H+26→28)
- **Actions:** build text serializer, embed seed, cosine top-k loader; persist `.npy` + IDs + model/KB hash; refresh after D-07.
- **Expected:** stable `top_k_careers(profile_text, k)` interface from H+12.
- **Tests:** shape/order/hash; cosine known vectors; missing artifact; 3 Explore + 2 Launch profiles sanity.
- **Fallback:** embedding API unavailable → cached seed vectors or skill-overlap baseline; interface unchanged.

### MI-07 — M4/M6 handoff (H+12/H+28)
- **Actions:** handoff interface/sample/error semantics, market query API, artifact versions.
- **Expected:** consumer integrates without reading pipeline internals.
- **Verify:** M4 runs sample; M6 sees live/seed source note; consumer ✅.

### MI-08 — Statistical guardrails (H+30→36)
- **Actions:** outlier/cap sanity, salary coverage, trend confidence, duplicate/source dominance, null behavior.
- **Expected:** no absurd headline; limitations in evaluation/data card.
- **Tests:** negative/outlier/extreme trend fixtures; source-only comparison.
- **Fallback:** hide field, not clamp silently; if clamp, preserve raw and document rule.

### MI-09 — Grounded market evidence support (H+32→38)
- **Actions:** define allowed stat keys/value formatting; provide structured stats to M4, not prose scraped from UI.
- **Expected:** evidence formatter map; number-grounding test fixtures; Launch missing skills from top skills.
- **Tests:** every displayed digit maps to stats; null salary copy; low-confidence copy; Vietnamese number format.
- **Handoff:** evidence fixture → M4/M6/M1.

## Interface invariants

- Artifact carries input/model/taxonomy/KB hash; mismatch fails loudly.
- Region changes context, never removes career candidate.
- Profile embedding excludes name, gender, school prestige and region.
- Market weight cannot rescue a role with very low human fit.
