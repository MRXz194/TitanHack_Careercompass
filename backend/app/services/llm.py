"""LangChain LLM gateway — the ONLY module allowed to call model APIs.

- chat_json(): structured-output chat call, validated against a Pydantic model,
  retries ≤2 with error feedback, raises LLMError after that (callers must have
  a deterministic fallback — see docs/AI_DESIGN.md).
- embed(): OpenAI embeddings through the LangChain provider adapter.

Every call is logged: model, tokens, latency.
"""
import json
import logging
import time
from typing import Type, TypeVar

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel

from app.core.config import get_settings

log = logging.getLogger("llm")
T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    pass


def _chat_model() -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        model=s.chat_model,
        base_url=s.chat_api_base,
        api_key=s.chat_api_key,
        timeout=30,
        max_retries=0,  # gateway loop below is the single retry budget owner
        temperature=0.7,
    )


def _embedding_model() -> OpenAIEmbeddings:
    s = get_settings()
    extra_body: dict[str, str] = {}
    if s.embed_input_type:
        extra_body["input_type"] = s.embed_input_type
    if s.embed_input_text_truncate:
        extra_body["input_text_truncate"] = s.embed_input_text_truncate
    model_kwargs: dict[str, object] = {"encoding_format": "float"}
    if extra_body:
        model_kwargs["extra_body"] = extra_body
    return OpenAIEmbeddings(
        model=s.embed_model,
        base_url=s.embed_api_base,
        api_key=s.embed_api_key,
        dimensions=s.embed_dimensions,
        model_kwargs=model_kwargs,
        check_embedding_ctx_length=False,
        request_timeout=30,
        max_retries=2,
    )


def _to_message(item: dict) -> BaseMessage:
    role = item.get("role")
    content = str(item.get("content", ""))
    if role == "assistant":
        return AIMessage(content=content)
    return HumanMessage(content=content)


def _parse_prompt_json(raw: BaseMessage, response_model: Type[T]) -> T:
    """Parse prompt-enforced JSON for providers that reject response_format."""
    content = raw.content if isinstance(raw.content, str) else str(raw.content)
    text = content.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```")
        text = text.removesuffix("```").strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("model response did not contain a JSON object")
    return response_model.model_validate_json(text[start : end + 1])


def chat_json(system: str, messages: list[dict], response_model: Type[T], max_retries: int = 2) -> T:
    """Invoke a LangChain structured-output model and validate the Pydantic result."""
    s = get_settings()
    model = _chat_model()
    use_prompt_json = (s.chat_structured_method or "json_mode").lower() == "prompt"
    structured_model = None if use_prompt_json else model.with_structured_output(
        response_model, method="json_mode", include_raw=True
    )
    schema_json = json.dumps(response_model.model_json_schema(), ensure_ascii=False)
    convo: list[BaseMessage] = [SystemMessage(content=(
        f"{system}\nReturn one valid JSON object matching this JSON Schema: {schema_json}"
    ))]
    convo.extend(_to_message(item) for item in messages)

    last_err = ""
    for attempt in range(max_retries + 1):
        t0 = time.time()
        try:
            if use_prompt_json:
                raw = model.invoke(convo)
                parsed = _parse_prompt_json(raw, response_model)
                parsing_error = None
            else:
                result = structured_model.invoke(convo)  # type: ignore[union-attr]
                raw = result.get("raw") if isinstance(result, dict) else None
                parsed = result.get("parsed") if isinstance(result, dict) else result
                parsing_error = result.get("parsing_error") if isinstance(result, dict) else None
            usage = getattr(raw, "usage_metadata", None)
            log.info(
                "llm chat model=%s tokens=%s latency=%.1fs attempt=%d",
                s.chat_model,
                usage,
                time.time() - t0,
                attempt,
            )
            if parsing_error is not None:
                raise ValueError(str(parsing_error))
            return parsed if isinstance(parsed, response_model) else response_model.model_validate(parsed)
        except Exception as exc:  # provider, parse and schema errors share one bounded retry path
            last_err = str(exc)
            log.warning(
                "llm chat failed model=%s latency=%.1fs attempt=%d error=%s",
                s.chat_model,
                time.time() - t0,
                attempt,
                type(exc).__name__,
            )
            convo.append(HumanMessage(
                content=(
                    "The previous response failed validation. Return only JSON matching "
                    f"the requested schema. Validation error: {last_err[:500]}"
                )
            ))
    raise LLMError(f"LLM failed structured output after {max_retries + 1} attempts: {last_err}")


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    s = get_settings()
    t0 = time.time()
    vectors = _embedding_model().embed_documents(texts)
    log.info("llm embed model=%s n=%d latency=%.1fs", s.embed_model, len(texts), time.time() - t0)
    return vectors
