# [HANDOFF] PR-04 — M4 → M5 / M1

Chat profiling API is ready for FE integration and replay capture.

## Artifact / paths

| Item | Path |
|---|---|
| Branch / tip | `kaguya` (includes PR-01…03) + `feat/PR-04-chat-handoff` |
| Contract | `docs/API_CONTRACT.md` §2 Chat Profiling |
| BE types | `backend/app/models/schemas.py` |
| FE types | `frontend/types/index.ts` |
| FE client | `frontend/lib/api.ts` (`sendChat`, `patchProfile`) |
| Profiler | `backend/app/services/profiler.py` |
| Sample Explore session | `backend/app/data/replay/explore_sample_session.json` |
| Sample Launch session | `backend/app/data/replay/launch_sample_session.json` |
| Capture script | `backend/scripts/capture_chat_samples.py` |
| Prompt version | `profiler-v2` |

## Run backend

```bash
cd backend
# optional: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health: `GET http://localhost:8000/api/health` → `{ "status": "ok", ... }`

FE (live API, not mock):

```bash
cd frontend
# .env.local: NEXT_PUBLIC_API_BASE=http://localhost:8000
# do NOT set NEXT_PUBLIC_USE_MOCK=1 when testing real chat
npm run dev
```

## curl samples (copy-paste)

### Explore opening + one turn

```bash
SID=demo-explore-1
curl -s http://localhost:8000/api/chat -H 'Content-Type: application/json' \
  -d "{\"session_id\":\"$SID\",\"message\":null,\"journey_mode\":\"explore\"}" | jq .

curl -s http://localhost:8000/api/chat -H 'Content-Type: application/json' \
  -d "{\"session_id\":\"$SID\",\"message\":\"Em hay sửa đồ điện trong nhà\",\"journey_mode\":\"explore\"}" | jq .
```

### Launch opening

```bash
SID=demo-launch-1
curl -s http://localhost:8000/api/chat -H 'Content-Type: application/json' \
  -d "{\"session_id\":\"$SID\",\"message\":null,\"journey_mode\":\"launch\"}" | jq .
```

### GET / PATCH profile

```bash
curl -s http://localhost:8000/api/profile/$SID | jq .
curl -s -X PATCH http://localhost:8000/api/profile/$SID \
  -H 'Content-Type: application/json' \
  -d '{"job_goal":"data entry-level","education_stage":"final_year"}' | jq .
```

### DELETE session (privacy)

```bash
curl -s -X DELETE http://localhost:8000/api/profile/$SID | jq .
# → {"ok": true}
```

### Regenerate sample fixtures (offline)

```bash
cd backend
PYTHONPATH=. python scripts/capture_chat_samples.py
```

## Response shape (always)

```json
{
  "reply": "string (Vietnamese)",
  "phase": "warmup|interests|abilities|constraints|wrapup",
  "turn": 1,
  "done": false,
  "profile": { "...Profile contract..." }
}
```

- `profile` is **full** state after merge (not a delta).
- `journey_mode` is **locked** on the first request for that `session_id` (later values ignored).
- Opening: `message: null` → first assistant question; Explore/Launch opening does **not** invent education/job_goal without user text (Launch may fill after answers).

## Latency notes (local deterministic path)

Measured via `scripts/capture_chat_samples.py` on TestClient (no LLM):

| Metric | Typical (local) |
|---|---|
| Chat turn p50 | ~5–15 ms |
| Chat turn max (sample) | &lt; 50 ms offline |
| PATCH profile | ~5–15 ms |

**With live LLM** (when `CHAT_API_KEY` set and `DEMO_MODE!=replay`): expect ~1–5 s/turn; timeout 30s in gateway; retries ≤2 then fallback question bank. Demo target remains chat &lt; 5s/turn when online.

## Error envelope

All non-2xx:

```json
{ "error": { "code": "422", "message": "Dữ liệu gửi lên không hợp lệ" } }
```

| Status | When |
|---|---|
| 422 | Missing `session_id` / invalid body |
| 404 | GET/PATCH/DELETE unknown session |
| 500 | Unhandled — FE should show friendly Vietnamese fallback |

FE: never show raw stack; use `frontend/lib/api.ts` error handling.

## Fallback behavior (demo safety)

| Condition | Behavior |
|---|---|
| No `CHAT_API_KEY` | Deterministic extractor + `get_fallback_question` (PR-02/03) |
| `DEMO_MODE=replay` | Prefer offline path (no live model); M1 may extend fixtures for full replay router |
| LLM structured-output fail after retries | Same fallback question bank; session **not** lost |
| User PATCH | Corrections stored; later chat merge will **not** re-add removed skills |

## What M5 should do

1. Keep `NEXT_PUBLIC_USE_MOCK=1` as safety net.
2. Point `NEXT_PUBLIC_API_BASE` at BE and flip mock off for chat integration (F1-05).
3. Send `journey_mode` on **opening** turn; reuse same `session_id` (localStorage `cc_session_id`).
4. Render `profile` live from each `ChatResponse`; on edit call `PATCH /api/profile/{session_id}`.
5. When `done === true`, show CTA → recommendations (F1-06).
6. Handle 404/422/500 with Vietnamese copy; do not display tool JSON or CoT.

## What M1 should do

1. Record/curate replay from `backend/app/data/replay/*_sample_session.json` for `DEMO_MODE=replay` (L-08).
2. Smoke: Explore + Launch + PATCH after every merge.
3. Optional: document `DELETE /api/profile/{session_id}` in release notes (additive endpoint).

## Test evidence

```bash
cd backend
python -m compileall app scripts tests
python -m pytest -q tests/unit tests/contract tests/integration
python -m pytest -q tests/contract/test_chat_handoff_samples.py
```

## Known limitations (max 3)

1. Without API key, profile quality is **keyword-deterministic**, not full LLM conversation quality.
2. `DEMO_MODE=replay` full short-circuit router for entire demo journey is still **M1 L-08** (fixtures provided as seed).
3. Recommendations still seed/stub until PR-05+; chat handoff does not block FE chat UI.

## Consumer ack

- M5 ran samples / live chat: ⬜  
- M1 recorded replay path: ⬜  
