# HANDOFF — Bàn giao trong một repo, không mất context

## 1. Một handoff chỉ hoàn tất khi đủ 6 mục

Copy template này vào PR và group chat:

```md
[HANDOFF] <TASK-ID> — <người giao> → <người nhận>
- Artifact/PR: <link + path chính xác>
- Contract/version: <API contract / taxonomy hash / dataset snapshot>
- Chạy thử: <lệnh copy-paste được>
- Input → output mẫu: <path hoặc JSON ngắn>
- Known limitations: <tối đa 3 ý, không giấu lỗi>
- Người nhận đã chạy và phản hồi: ⬜
```

Link file không thay cho lệnh chạy. “Code xong rồi” không phải handoff.

## 2. Artifact registry

| Artifact | Source of truth | Producer | Consumer | Ready khi |
|---|---|---|---|---|
| API shapes | `docs/API_CONTRACT.md` + BE/FE types | M1 + owner endpoint | M4/M5/M6 | 3 nơi đồng bộ |
| Raw snapshot | `data/raw/*.jsonl` (không commit) | M2 | M2 | manifest có nguồn/ngày/count |
| Processed postings | `data/processed/postings.jsonl` | M2 | M3 | D-04 QA report pass |
| Skill taxonomy | `data/taxonomy/skills_vi.json` | M3 | pipeline + M4 | version/hash được ghi |
| Enriched postings | `data/processed/postings_enriched.jsonl` | M3 | stats builder | extraction report đi kèm |
| Market DB | `backend/market.db` hoặc release artifact | M3 | BE/M6 | meta table + spot-check pass |
| Career KB | `data/seed/careers_seed.json` | M2 + M4 | matching/FE | route check pass |
| Career embeddings | `.npy` + career IDs | M3 | M4 | cùng KB hash |
| Replay fixtures | `backend/app/data/replay/*.json` | M1 + M4 | demo | ngắt mạng vẫn E2E |
| Evaluation results | `docs/EVALUATION_RESULTS.md` | M1 | pitch/judges | ghi cả fail/caveat |
| Launch profile/result fixture | replay + contract | M4 | M5/M6/M1 | matched/missing/actions invariants pass |

## 3. Integration order

1. FE làm mock đúng contract; BE stub trả cùng shape.
2. M4 handoff chat thật cho M5; M1 thu replay ngay.
3. M3 handoff `top_k` chạy trên seed sớm; refresh embeddings sau khi KB mở rộng.
4. M3 handoff market DB/API cho M6; UI vẫn giữ fallback seed.
5. M4 thay stub recommendation bằng scoring; M6 chuyển mock → real bằng env, không xóa mock.
6. M1 chạy contract smoke test và E2E sau mỗi integration PR.
7. Launch là presenter trên shared core: không handoff service/DB riêng; chỉ profile/result fields + fixtures.

## 4. Khi artifact đổi

- Dataset/KB/taxonomy/embeddings phải có `built_at`, count và hash/version; không truyền file cùng tên nhưng nội dung không rõ phiên bản.
- Breaking API change sau H+8 cần M1 + bên giao + bên nhận xác nhận, cập nhật 3 source-of-truth trong cùng PR.
- Consumer không tự đoán field còn thiếu; trả handoff về producer.

## 5. Trước khi ngủ hoặc đổi người

Commit/push branch, ghi task đang ở đâu, lệnh chạy cuối cùng, lỗi cuối cùng và bước tiếp theo nhỏ nhất. Buddy phải thả ✅. Không handoff secret qua repo hoặc screenshot.
