# GRADUATE LAUNCH — scope tìm việc cho sinh viên sắp/đã tốt nghiệp

## 1. Mục tiêu

Giúp sinh viên chuyển từ câu “em học ngành X” sang ba câu trả lời thực dụng:

1. Em có thể tìm các nhóm việc entry-level nào, kể cả vai trò lân cận chưa từng nghĩ tới?
2. Kỹ năng nào em đã có bằng chứng, kỹ năng nào thị trường thường yêu cầu nhưng còn thiếu?
3. Trong 30 ngày tới em nên tạo output gì để bắt đầu ứng tuyển có căn cứ hơn?

Đây là **career launch guidance**, không phải hệ thống tuyển dụng hay bảo đảm có việc.

## 2. User journey P1

1. Landing chọn “Sắp/đã tốt nghiệp — chuẩn bị tìm việc”.
2. Chat hỏi ngành/giai đoạn học, project/thực tập/việc làm thêm, công cụ đã dùng, loại công việc muốn thử và constraint.
3. Profile live hiển thị skill có `source_quote`; project được coi là evidence, không tự suy ra level cao.
4. Results trả top role families + 1 adjacent/stretch role.
5. Mỗi role có: reason từ evidence; hiring-demand stats; matched/missing skills; readiness band; search queries; action plan 4 tuần.
6. User sửa skill/evidence rồi regenerate; region chỉ đổi market context, không loại role.

## 3. MVP in-scope

- Optional `journey_mode=launch` và `education_stage` trong Profile.
- Tối đa 3 experience highlights từ project, internship, volunteer hoặc việc làm thêm.
- Recommendation dùng cùng career KB/scoring, nhưng copy và route ưu tiên entry-level/certificate/project/portfolio.
- `job_readiness` không dùng phần trăm giả chính xác; chỉ `ready_now | near_ready | build_foundation` kèm lý do.
- Matched/missing skills chỉ lấy từ profile evidence và top skills của posting aggregate.
- 4 action items theo tuần, mỗi item có deliverable kiểm chứng được.
- 2–4 search queries/job-title aliases để user tự tìm trên nguồn tuyển dụng.
- Persona demo B là sinh viên năm cuối; có replay fixture riêng.

## 4. Out-of-scope 48h

- Crawl/match từng vacancy live, ranking công ty hoặc “job phù hợp nhất”.
- Upload/chấm CV, viết cover letter, auto-apply, theo dõi application.
- Verify bằng cấp, project hoặc skill; tích hợp LinkedIn/GitHub.
- Dự đoán khả năng được tuyển, lương cá nhân hoặc thời gian có việc.
- Dùng GPA, giới tính, quê quán hoặc trường học để giảm/xếp hạng cơ hội.

## 5. Readiness logic giải thích được

```text
coverage = weighted overlap(profile skills with evidence, role top skills)
evidence_strength = count of skills backed by project/internship quotes
band = deterministic thresholds in config
```

- `ready_now`: coverage cao và có evidence cho skill cốt lõi.
- `near_ready`: có nền tảng, thiếu 1–2 skill thường gặp hoặc evidence chưa mạnh.
- `build_foundation`: cần xây skill nền trước khi tập trung ứng tuyển role đó.

Band là hướng dẫn chuẩn bị, không phải xác suất được tuyển. Market demand không được bù cho skill fit thấp.

## 6. Action plan rules

Mỗi action theo format `tuần → hành động → deliverable → vì sao`. Ví dụ: “Tuần 1: làm dashboard Excel từ dataset mở → 1 file + 3 insight → tạo evidence cho Excel/data cleaning”. Không đưa khóa học/trường/công ty cụ thể nếu không có source được kiểm chứng.

## 7. Acceptance tests

- Hai profile giống skill/project nhưng khác giới tính → role/readiness tương đương.
- Đổi region không làm mất role, chỉ đổi market block/search context.
- Missing skills là tập con role top skills và không chứa skill user đã có.
- Mọi matched skill có `source_quote` hoặc experience evidence.
- Mỗi action có deliverable; không có câu chung chung “hãy học thêm”.
- Search query không chứa giới, tuổi, trường hoặc đặc điểm nhạy cảm.
- Launch response vẫn pass route/evidence/number-grounding hard rules chung.
