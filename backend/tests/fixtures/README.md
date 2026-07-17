# Test fixtures

Chỉ chứa dữ liệu fictional/sanitized có `contract_version`, `prompt_version`,
`tool_policy_version`, `snapshot_hash` khi liên quan. Không commit raw student message,
PII, secret hoặc output được gắn nhãn là dữ liệu thị trường thật khi chỉ là seed.

Các fixture agent thêm sau PR-12 nằm theo nhóm `agent/allow`, `agent/deny`,
`agent/fallback`; golden data extraction nằm trong `market/`.

