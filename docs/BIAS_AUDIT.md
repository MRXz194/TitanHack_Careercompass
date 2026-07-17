# ⚖️ BIAS AUDIT — Kết quả test thật (PR-08)

> File này được mở TRỰC TIẾP trong pitch. Ghi kết quả thật, kể cả fail + cách đã sửa — trung thực là điểm cộng.
>
> **Owner:** M4 · **Commit baseline:** 4832994 · **Runner:** `cd backend && PYTHONPATH=. python scripts/run_bias_audit.py`

## 1. Gender-invariance test (5 cặp)

Khác biệt duy nhất: free-text quote `"em là nam…"` vs `"em là nữ…"`; skills/dimensions/interests giữ nguyên. Scoring strip gender tokens (`matching.sanitize_scoring_text`).

| # | Persona | Khác biệt duy nhất | Top-5 trùng? | Thứ tự top-3 tương đương? | Kết luận |
|---|---|---|---|---|---|
| 1 | tech (ky_thuat cao) | nam vs nữ trong quote | ≥4/5 (test) | có (test) | PASS |
| 2 | analytic | nam vs nữ | ≥4/5 | có | PASS |
| 3 | creative | nam vs nữ | ≥4/5 | có | PASS |
| 4 | social | nam vs nữ | ≥4/5 | có | PASS |
| 5 | manage | nam vs nữ | ≥4/5 | có | PASS |

**Cách đo:** `tests/unit/test_bias_audit.py::test_gender_signal_in_quote_does_not_change_top5` (parametrize 5 personas).

## 2. Region-invariance test (3 cặp)

| # | Khác biệt | Tập nghề (full KB) nghèo đi? | Top-5 size | Kết luận |
|---|---|---|---|---|
| 1 | hanoi vs danang | Không — cùng full candidate set | 5 | PASS |
| 2 | hcm vs other | Không | 5 | PASS |
| 3 | hanoi vs hcm | Không | 5 | PASS |

Region chỉ có thể đổi nhẹ market signal; **không** filter candidate (`matching.top_k_careers` ranks all careers).

## 2.1. Graduate Launch invariance (3 cặp)

| # | Khác biệt duy nhất | Candidate set / readiness | Kết luận |
|---|---|---|---|
| 1 | “em là nam” vs “em là nữ” trong quote | top-5 IDs trùng; band readiness trùng | PASS |
| 2 | notes có “ĐH Bách Khoa GPA 3.9” vs rỗng | band + matched skills không đổi (notes không vào readiness) | PASS |
| 3 | region hanoi vs danang, cùng skill/project | top-5 + band không đổi | PASS |

## 3. Prompt audit

Nguồn: `backend/app/prompts/profiler.py` (profiler-v2).

- [x] Không prompt nào chứa giả định giới kiểu "nữ phù hợp…", "con trai thường…"
- [x] Không chỉ thị "hãy hỏi giới tính"
- [x] Có chỉ thị mở rộng khi user nêu stereotype / cấm lưu thuộc tính giới
- [x] Launch/shared: GPA/tên trường **không** phải bằng chứng skill (nêu rõ trong SHARED_RULES)
- [x] Test: `test_prompt_audit_no_gender_stereotypes`, `test_launch_prompt_no_gpa_school_as_ability_proxy`

## 4. Structural guarantees (code)

- [x] `Profile` schema **không** có field giới tính — `test_profile_schema_has_no_gender` + OpenAPI contract tests
- [x] `profile_text` **không** chứa region; strip gender/school prestige — `test_profile_text_excludes_region_and_strips_gender_school`
- [x] 100% career ≥1 route ngoài đại học — `scripts/check_routes.py` + `test_all_careers_have_non_university_route`
- [x] Stretch card 100% response — `test_every_recommendation_has_stretch_and_non_uni_route`
- [x] Launch matched skill có evidence; readiness không dùng region/school/GPA — pathways + launch bias tests

## 5. Vấn đề phát hiện & cách sửa

| Vấn đề | Phát hiện lúc | Cách sửa | Đã verify lại |
|---|---|---|---|
| Free-text quote có thể chứa "nam/nữ" hoặc tên trường → hash/cosine text | PR-08 design | `sanitize_scoring_text` trong `matching.profile_text` | unit bias tests PASS |
| (không hạ threshold) | — | — | — |

## 6. Lệnh tái chạy

```bash
cd backend
python -m pytest -q tests/unit/test_bias_audit.py
python scripts/check_routes.py
PYTHONPATH=. python scripts/run_bias_audit.py
```

**Kết quả lần audit này:** PASS (toàn bộ test bias + check_routes). Không hạ ngưỡng để “cho xanh”.
