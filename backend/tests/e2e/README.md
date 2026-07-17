# E2E tests

Đặt full-journey tests tại đây khi PR-03/PR-13 hoàn tất. E2E phải dùng fictional
persona/replay, không dùng transcript thật; đánh marker `@pytest.mark.e2e` và không gọi
network nếu không có explicit live-test flag.

Target P0:

- Explore: opening → profile correction → recommendations → market evidence.
- Launch: opening → project evidence → readiness/actions.
- Replay: ngắt model provider vẫn hoàn thành hai journey với cùng API contract.

