# AI FOCUS — Vì sao đây là một sản phẩm AI đúng trọng tâm hackathon?

> Mục tiêu file này: giúp team, AI assistants và pitch thống nhất một câu trả lời sắc gọn: CareerCompass không phải app hướng nghiệp gắn chatbot cho vui. AI nằm ở các điểm tạo giá trị cốt lõi: hiểu người học qua hội thoại, đọc tín hiệu tuyển dụng, ghép hai phía bằng bằng chứng, và tự kiểm soát bias/ảo giác.

## 1. Luận điểm AI chính

CareerCompass là một hệ thống **AI decision-support** cho hướng nghiệp và chuyển tiếp việc làm. Hệ thống không quyết định thay học sinh/sinh viên; nó tạo ra một bản nháp có bằng chứng để người học và tư vấn viên thảo luận tốt hơn.

Luận điểm pitch:

> Chúng tôi dùng AI để nối ba thứ thường bị tách rời: người học thực sự đã làm gì/thích gì, thị trường đang tuyển kỹ năng gì, và lộ trình học/việc nào có thể giải thích được. Mỗi gợi ý đều có nguồn, có giới hạn, có route thay thế và có kiểm tra bias.

## 2. AI dùng ở đâu, không dùng ở đâu

| Lớp | AI làm gì | Vì sao cần AI | Guardrail bắt buộc |
|---|---|---|---|
| Conversational Profiler | Hỏi adaptive, rút skill/interest/constraint/experience từ lời người học | Không ép người dùng vào một bài quiz tĩnh; hiểu được câu trả lời tự nhiên tiếng Việt | JSON schema, phase state machine, profile editable, không lưu gender |
| Skill Extraction | Trích kỹ năng từ job postings bằng taxonomy + LLM catch-up | Job description tiếng Việt/Anh rất nhiễu, nhiều cách gọi kỹ năng khác nhau | Golden set precision/recall, cache, taxonomy version, không tự tạo số |
| Career/Role Matching | Ghép profile evidence với career KB, skill overlap và market signal | Cần kết hợp tín hiệu con người + tín hiệu tuyển dụng, không chỉ keyword | Scoring deterministic, region không hard-filter, top 5 + stretch |
| Evidence Generation | Diễn đạt “vì sao gợi ý này” từ quote người dùng + stats | Judge/người dùng cần thấy lý do bằng tiếng Việt tự nhiên | Number grounding: số trong output phải có trong stats input; fallback template |
| Graduate Launch Readiness | Tách matched/missing skills, band readiness, query tìm việc, action 30 ngày | Sinh viên sắp tốt nghiệp cần chuyển project/skill thành hướng ứng tuyển cụ thể | Readiness không phải xác suất trúng tuyển; matched skill phải có evidence |
| Anti-bias Audit | Paired tests giới/vùng/trường, prompt audit | Đây là tiêu chí trọng số cao; cần chứng minh bằng test, không chỉ tuyên bố | Ghi pass/fail thật vào `BIAS_AUDIT.md`; fail thì bỏ claim hoặc sửa |

Không dùng AI cho:

- Không dùng AI để bịa salary, demand, trend hoặc sample count.
- Không dùng AI để chấm điểm con người là “hợp/không hợp” tuyệt đối.
- Không dùng AI để dự đoán xác suất được tuyển, lương cá nhân, điểm chuẩn, hoặc trường nào “xứng đáng”.
- Không dùng AI để auto-apply, viết CV thay người dùng, hoặc quyết định thay tư vấn viên.

## 3. MVP AI phải chứng minh được gì?

MVP không cần “AI lớn nhất”, cần **AI có bằng chứng nhất**. Bốn bằng chứng bắt buộc:

| Bằng chứng | Demo/Artifact | Pass khi |
|---|---|---|
| AI hiểu người học qua tương tác | Chat + Profile Card live | Profile có source quote, sửa được, không lặp câu hỏi, có Explore và Launch |
| AI đọc được skill signal từ hiring data | Data pipeline + Radar nhu cầu kỹ năng | Có source/date/count, precision/recall trên golden set, trend low-confidence được gắn cờ |
| AI gợi ý có cá nhân hóa và giải thích | Result cards | Mỗi career/role có why, market stats, route/action, counterfactual hoặc readiness |
| AI mở rộng lựa chọn và chống bias | Stretch card + bias audit | Có route ngoài đại học, region không lọc cứng, paired tests không lệch vô lý |

Nếu chỉ có UI đẹp mà thiếu 4 bằng chứng này thì không đạt trọng tâm AI. Nếu có 4 bằng chứng này, dù dataset nhỏ và UI vừa đủ, sản phẩm vẫn bám rất sát đề.

## 4. Ứng dụng sản phẩm vào đâu?

### Trường THPT, trung tâm hướng nghiệp

Use case: học sinh lớp 10-12 làm 8-10 phút hội thoại trước buổi tư vấn. Tư vấn viên nhận profile, các hướng nghề có route học đa dạng và market signal để hỏi sâu hơn.

Giá trị:

- Giảm thời gian khám phá ban đầu trong tư vấn 1:1.
- Tránh lời khuyên chỉ dựa trên xu hướng/gia đình.
- Cho học sinh thấy cả route đại học, cao đẳng, trung cấp nghề, chứng chỉ.

### Trường đại học, phòng công tác sinh viên, career center

Use case: sinh viên năm cuối hoặc mới tốt nghiệp dùng Launch mode để chuyển project/thực tập/môn học thành nhóm vai trò entry-level, skill còn thiếu, query tìm việc và kế hoạch 30 ngày.

Giá trị:

- Giúp sinh viên không tìm việc bằng từ khóa quá hẹp theo tên ngành.
- Biến project thành evidence kỹ năng thay vì nói chung chung “em chưa có kinh nghiệm”.
- Cho career center một output có cấu trúc để review nhanh.

### Trường nghề, bootcamp, đơn vị đào tạo ngắn hạn

Use case: dùng market dashboard để xem kỹ năng nào đang có tín hiệu tuyển dụng theo vùng và nghề, từ đó thiết kế workshop/module bổ sung.

Giá trị:

- Có dữ liệu tuyển dụng gần đây thay vì cảm giác chủ quan.
- Thấy skill demand và salary coverage kèm limitation.
- Không claim “thiếu nhân lực” khi chưa có dữ liệu supply.

### Sở/đơn vị giáo dục, chương trình CSR phát triển nhân lực địa phương

Use case: pilot quy mô cohort, dùng aggregate report sau khi có consent/privacy để hiểu nhóm học sinh đang thiếu thông tin gì và thị trường địa phương đang có tín hiệu nào.

Giá trị:

- Hỗ trợ phân luồng hướng nghiệp theo dữ liệu.
- Tăng nhận thức về route nghề, không chỉ đại học.
- Có khung đo tác động nhỏ: clarity, new options, counselor usefulness.

## 5. Góc đa dạng bài toán đã đáp ứng

| Góc bài toán | Đã đáp ứng trong MVP | Giới hạn cần nói thật |
|---|---|---|
| Học sinh chọn ngành theo cảm tính/gia đình | Conversational profile + stretch + route đa dạng | Không thay thế tư vấn viên/gia đình, chỉ tạo tài liệu tham khảo |
| Dư thừa cử nhân nhưng thiếu kỹ năng thực hành | Market skill signal + route vocational/certificate | Chưa đo supply thật từ hệ thống đào tạo |
| Sinh viên ra trường thất nghiệp/chưa biết ứng tuyển gì | Launch mode role family + missing skills + action plan | Không match job cụ thể/công ty cụ thể trong MVP |
| Thị trường thay đổi theo vùng/thời gian | Demand/trend/region snapshot + confidence | MVP là snapshot crawl một lần, chưa real-time scheduler |
| Bias giới/vùng/trường | No gender schema, region info-only, paired tests | Bias audit mẫu nhỏ; cần pilot lớn hơn sau hackathon |
| Tư vấn viên thiếu thời gian | Pre-counseling artifact có evidence | Chưa có counselor dashboard thật, chỉ slide future |

## 6. AI quality gates trước khi claim “đã ổn”

Team chỉ được pitch mạnh phần AI khi có bằng chứng sau:

- `MI-02`: skill extraction có golden set và precision/recall/F1.
- `MI-04/MI-05`: market stats có source/date/sample/confidence.
- `PR-02/PR-03`: profiler trả JSON valid qua nhiều transcript Explore/Launch.
- `PR-05`: matching pass persona tests và region/gender/school-name invariants.
- `PR-06`: evidence generation không có số ngoài stats input.
- `PR-07`: Launch readiness có matched/missing/action deliverable đúng schema.
- `PR-08`: bias audit ghi kết quả thật, kể cả failure và fix.
- `L-07/L-11`: E2E + user/counselor feedback có số thật, không phóng đại.

Một task AI chưa có test thì chỉ được gọi là `CODE_COMPLETE_NOT_VERIFIED`, không gọi là DONE.

## 7. Pitch narrative 60 giây cho phần AI

1. “Chúng tôi bắt đầu từ dữ liệu tuyển dụng: postings được chuẩn hóa, trích kỹ năng bằng taxonomy Việt-Anh và LLM catch-up, sau đó aggregate theo nghề/vùng/thời gian.”
2. “Người học không làm một bài quiz; họ trò chuyện. AI rút profile từng bước, nhưng profile hiện ra live và sửa được.”
3. “Recommendation không phải một câu trả lời của LLM. Candidate được tính bằng embedding, skill overlap và market signal; LLM chỉ diễn đạt evidence, còn số liệu bị kiểm tra grounding.”
4. “Để tránh đóng khung, hệ thống luôn có nhiều route, ít nhất một route ngoài đại học, một stretch suggestion, và paired tests kiểm tra gender/region bias.”
5. “Với sinh viên sắp tốt nghiệp, cùng core đó chuyển project/skill thành role entry-level, missing skills, search queries và action 30 ngày.”

## 8. Kết luận audit hiện tại

Phần AI đang **đúng trọng tâm hackathon** nếu team triển khai theo `AI_DESIGN.md`, `EVALUATION.md` và task M3/M4. Điểm mạnh nhất là AI có cấu trúc, có kiểm chứng, có fallback và có ethics-by-design. Điểm cần bảo vệ trong pitch là không overclaim: dữ liệu tuyển dụng là proxy của demand, không phải bằng chứng đầy đủ về thiếu hụt cung-cầu; Launch readiness là mức chuẩn bị, không phải xác suất được tuyển.

Ưu tiên code tiếp theo nếu muốn AI “nặng ký” hơn trong demo: làm thật `MI-02`, `PR-05`, `PR-06`, `PR-08` trước các hiệu ứng UI phụ.
