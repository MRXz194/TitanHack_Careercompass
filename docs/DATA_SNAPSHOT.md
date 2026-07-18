# DATA SNAPSHOT CARD — generated candidate card

> Status: `CANDIDATE_NOT_RELEASED`. Đây là hiring-demand proxy, không phải dữ liệu thời gian thực và không đo nguồn cung lao động. Snapshot này chưa thay `backend/market.db` khi accuracy còn `NOT_RUN`.

| Field | Value |
|---|---|
| Snapshot / SHA-256 | `real_jobs_snapshot_20260718` / `4ecfc1a513fea9eb451e61cbed4825b64385cf8a75d746cc2606dc5be0e83806` |
| Built at / analysis window | `2026-07-18T09:27:09.381825+00:00` / tối đa 90 ngày |
| Raw / normalized | 3914 / 3865; drop hoặc dedupe 49 (1.25%) |
| Source distribution | vietnamworks: 2963 (76.7%), itviec: 874 (22.6%), topcv: 28 (0.7%) |
| Region distribution | other: 2971 (76.9%), hcm: 498 (12.9%), hanoi: 372 (9.6%), danang: 24 (0.6%) |
| Salary evidence | 1449/3865 (37.5%) |
| Experience evidence | 854/3865 (22.1%); entry-level 87 |
| Skill extraction | `skill-extraction-v1`; 3532/3865 có skill; live LLM success 0; fallback 1481 |
| Career mapping | `career-mapping-v1-stub`; 1031/3865 (26.7%); accuracy `NOT_RUN` |

## Release decision

- Candidate có quy mô và skill coverage tốt hơn release hiện tại, nhưng chưa đủ bằng chứng để thay DB demo.
- Blocker: Career mapping accuracy is NOT_RUN; label and review at least 50 postings before replacing market.db.; Region 'other' dominates the snapshot; regional claims require better location normalization.
- Go/no-go owner phải ký sau gold-label accuracy review; script không tự publish DB.

## Source permission and release boundary

- Policy URLs nằm trong `data/processed/manifest.json`; permission status là `unverified`, không suy diễn privacy/terms page thành giấy phép tái phân phối.
- Raw/processed full text không được commit. Release chỉ chứa aggregate DB, manifest và report.
- UI/pitch phải gọi đây là nhu cầu tuyển dụng quan sát được, không claim labor shortage nếu chưa có supply data.

## Known limitations

- Posting count không bằng vacancy count; coverage lệch theo nguồn và vùng.
- Mapping coverage không phải mapping accuracy; accuracy và human usefulness có thể vẫn `NOT_RUN`.
- Salary percentile phải null khi mẫu không đủ; trend phải null khi không đủ hai cửa sổ đáng tin.
- Xem `docs/EVALUATION_RESULTS.md` và report JSON để biết denominator/fallback đầy đủ.
