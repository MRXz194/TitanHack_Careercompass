# [HANDOFF] M3 · MI-07 — Market + embeddings → M4 / M6

- Status: `READY_FOR_CONSUMER_VERIFY`; PR vào `t4mch1nh` chưa mở.
- Artifact/branch: `feat/MI-07-market-embeddings-handoff`; market builder/service từ MI-04/05 và embedding builder/loader từ MI-06.
- Contract/version:
  - Public API: `docs/API_CONTRACT.md` §4, không đổi shape.
  - Market DB: `market-stats-v1-stub`; hiring-demand proxy `0.6*demand_norm + 0.4*positive_trend_norm`, demand-only khi low-confidence.
  - Embeddings: `career-embeddings-v1`, serializer `career-text-v1`, KB `sha256:3b392b2eeb763a63cd53c0d14719982b531883bf322879b6cb8ef1f7d6bd410c` (25 careers).
- Interface cho M4: `app.services.career_embeddings.top_k_careers(profile_text, k) -> list[tuple[career_id, score]]`; `profile_text` phải đi qua serializer của M4, không chứa tên, giới tính, trường, region.
- Interface cho M6: `GET /api/market/overview`, `GET /api/market/skills`, `GET /api/market/careers/{career_id}`; luôn render `source_note`, `low_confidence` và giữ mock/seed fallback.
- Chạy thử từ `backend/`:
  - `../.venv/bin/python -m scripts.test_mi07_handoff`
  - `../.venv/bin/python -m pytest -q tests/integration/test_mi07_consumer_handoff.py tests/integration/test_embedding_pipeline.py tests/integration/test_market_stats_api.py tests/integration/test_hiring_demand_api.py`
- Build embedding offline: `../.venv/bin/python ../data/pipeline/embed_careers.py --mode deterministic`; output `data/processed/careers.npy` + `career_ids.json` là build artifact, không commit.
- Build embedding live: chỉ chạy `--mode live` sau khi M1 duyệt budget/key; mọi provider call đi qua `app/services/llm.py`.
- Test evidence: unit/contract MI-06 = 267 PASS; MI-07 consumer smoke + embedding/market/proxy integration = 4 PASS. Môi trường local `.venv` Python 3.14.4, canonical Python 3.11 chưa chạy.
- Input → output mẫu: `backend/tests/fixtures/market/mi07_consumer_sample.json`; fixture fictional, chỉ chứa sanitized profile text và public result shape.
- Error/fallback semantics:
  1. Thiếu embedding artifact hoặc provider lỗi → lexical skill-overlap fallback, interface không đổi.
  2. Artifact tồn tại nhưng sai schema/serializer/KB/vector hash → fail rõ `EmbeddingArtifactError`, không dùng vector stale.
  3. Market DB thiếu/chưa đúng version → router trả seed fallback cùng response shape và `source_note` ghi rõ.
- Known limitations:
  1. D-05 vẫn có duplicate/hash mismatch nên chưa rebuild production `market.db` từ chuỗi MI3 hiện tại.
  2. Live OpenAI embedding chưa gọi; chưa có evidence về latency/cost thực tế.
  3. Consumer HTTP smoke chuẩn Python 3.11 và xác nhận UI live/seed vẫn cần M4/M6/M1 chạy.
- Người nhận đã chạy và phản hồi: M4 ⬜ · M6 ⬜
