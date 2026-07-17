# Backend tests

Canonical rules: [`docs/TESTING.md`](../../docs/TESTING.md).

- `unit/`: pure domain, gateway fake, policy/scoring/parser tests.
- `contract/`: Pydantic/OpenAPI/API-fixture parity.
- `integration/`: FastAPI + service + local seed/temp storage.
- `e2e/`: full Explore/Launch/replay journeys.
- `fixtures/`: fictional, sanitized, versioned inputs/outputs.

Run from `backend/`; normal tests never require API keys or network.

