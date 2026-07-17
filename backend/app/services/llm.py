"""LLM Gateway — the ONLY module allowed to call LLM / embedding APIs.

- chat_json(): structured-output chat call, validated against a Pydantic model,
  retries ≤2 with error feedback, raises LLMError after that (callers must have
  a deterministic fallback — see docs/AI_DESIGN.md).
- embed(): OpenAI embeddings (separate client — DeepSeek has no embeddings).

Every call is logged: model, tokens, latency.
"""
import json
import logging
import time
from typing import Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings

log = logging.getLogger("llm")
T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    pass


def _chat_client() -> OpenAI:
    s = get_settings()
    return OpenAI(base_url=s.chat_api_base, api_key=s.chat_api_key, timeout=30)


def _embed_client() -> OpenAI:
    s = get_settings()
    return OpenAI(base_url=s.embed_api_base, api_key=s.embed_api_key, timeout=30)


def chat_json(system: str, messages: list[dict], response_model: Type[T], max_retries: int = 2) -> T:
    """Call chat model, parse JSON response into response_model. Retry with error feedback."""
    s = get_settings()
    client = _chat_client()
    convo = [{"role": "system", "content": system}, *messages]

    last_err = ""
    for attempt in range(max_retries + 1):
        t0 = time.time()
        resp = client.chat.completions.create(
            model=s.chat_model,
            messages=convo,
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        raw = resp.choices[0].message.content or ""
        log.info("llm chat model=%s tokens=%s latency=%.1fs attempt=%d",
                 s.chat_model, getattr(resp, "usage", None), time.time() - t0, attempt)
        try:
            return response_model.model_validate(json.loads(raw))
        except (json.JSONDecodeError, ValidationError) as e:
            last_err = str(e)
            convo.append({"role": "assistant", "content": raw})
            convo.append({"role": "user", "content":
                          f"Your JSON was invalid: {last_err}. Reply again with ONLY valid JSON matching the schema."})
    raise LLMError(f"LLM failed structured output after {max_retries + 1} attempts: {last_err}")


def embed(texts: list[str]) -> list[list[float]]:
    s = get_settings()
    t0 = time.time()
    resp = _embed_client().embeddings.create(model=s.embed_model, input=texts)
    log.info("llm embed model=%s n=%d latency=%.1fs", s.embed_model, len(texts), time.time() - t0)
    return [d.embedding for d in resp.data]
