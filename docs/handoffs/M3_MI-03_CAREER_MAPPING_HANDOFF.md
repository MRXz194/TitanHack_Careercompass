# [HANDOFF] M3 · MI-03 — Career mapping stub → MI-04 / M4

- Status: `CODE_COMPLETE_NOT_VERIFIED` — consumer chưa được phép dùng như artifact production.
- Artifact/PR: `data/pipeline/map_careers.py`; PR chưa mở.
- Contract/version: `career-mapping-v1-stub`; taxonomy `1.0.0` / `sha256:67c18ff3a8bd14f71d29e0c3de27f7035fb387e6aa797c5c39ecccd9fd961e2a`; Career KB `sha256:67df6e0f8824e190ca6878d3b5137f08fca27d54889dd258790b06ce395830f6` (25 careers).
- Chạy thử: từ `backend/`, chạy `../.venv/bin/python -m pytest -q tests/unit/test_career_mapping.py tests/integration/test_career_mapping_pipeline.py`.
- Test evidence: unit + integration fixture = `PASS` (6 passed) trên working tree sau `64171b2`, local `.venv` Python 3.14.4; canonical Python 3.11 chưa chạy. Full D-05 pipeline = `FAIL` trước extraction vì trùng posting ID `itviec_5804`.
- Input → output mẫu: `backend/tests/fixtures/market/normalized_postings_mi02.jsonl` → file tạm `postings_enriched.jsonl` → `postings_mapped.jsonl`; 10/10 có `career_id|unmapped`, coverage fixture 8/10, resume 10/10, 0 LLM calls.
- Known limitations:
  1. `data/processed/postings.jsonl` có 298 dòng nhưng chỉ 297 ID duy nhất; M2 cần sửa/rebuild D-05.
  2. SHA-256 file hiện tại là `d52975191fcc4afa2e1fc075231e515b404fda5219594781e4620d1b33b265c6`, không khớp manifest `192e492fa2984f908525ac556a893767ab19a431831e7ea144558d0f8383a430`.
  3. Mapping vẫn title-pattern-only; accuracy 50 mẫu = `NOT_RUN`, không được claim ngưỡng 85%.
- Fallback: giữ `unmapped`, loại khỏi career stats nhưng vẫn đếm trong manifest; chưa build `market.db` từ artifact lỗi.
- Người nhận đã chạy và phản hồi: ⬜
