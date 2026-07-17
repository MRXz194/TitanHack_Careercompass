# Chat / demo replay samples (PR-04+)

Fictional sanitized multi-turn sessions for M5 integration and M1 `DEMO_MODE=replay` work.

| File | Mode | Producer |
|---|---|---|
| `explore_sample_session.json` | explore | `scripts/capture_chat_samples.py` |
| `launch_sample_session.json` | launch | same |

Metadata: `contract_version`, `prompt_version`, `fictional: true`.

**Do not** commit real student transcripts or API keys.

Regenerate:

```bash
cd backend && PYTHONPATH=. python scripts/capture_chat_samples.py
```
