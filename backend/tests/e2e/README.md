# E2E tests

Full-journey tests ở `test_journeys.py` dùng fictional persona/replay, không dùng
transcript thật, không gọi network và được chạy bắt buộc trong CI.

Coverage P0:

- Explore + LangGraph: opening → evidence → profile correction → recommendations → market.
- Launch + replay: opening → project evidence → readiness/actions, model provider bị cấm gọi.
- Cả hai: 5 hướng + stretch, pathway đa dạng, source note và autonomy disclaimer.

