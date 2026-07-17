# Chat / demo replay samples (PR-04+)

Fictional sanitized multi-turn sessions for M5 integration and M1 `DEMO_MODE=replay` work.

| File | Mode | Producer |
|---|---|---|
| `explore_sample_session.json` | explore | `scripts/capture_chat_samples.py` |
| `launch_sample_session.json` | launch | same |
| `agent_sanitized_trace.json` | agent meta (PR-14) | hand-authored sanitized tools/versions only |

Metadata: `contract_version`, `prompt_version`, `fictional: true`.

**Do not** commit real student transcripts, CoT, or API keys.
Agent replay exposes tools / policy codes / latency / versions only — never raw messages.

Regenerate:

```bash
cd backend && PYTHONPATH=. python scripts/capture_chat_samples.py
```
