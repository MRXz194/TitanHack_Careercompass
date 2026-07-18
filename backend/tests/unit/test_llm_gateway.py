from collections.abc import Iterable

import pytest
from pydantic import BaseModel

from app.services import llm


pytestmark = pytest.mark.unit


class ExampleOutput(BaseModel):
    value: str


class FakeStructuredModel:
    def __init__(self, outcomes: Iterable[object]) -> None:
        self.outcomes = iter(outcomes)
        self.calls = 0
        self.last_messages: list[object] = []

    def invoke(self, messages: list[object]) -> object:
        self.calls += 1
        self.last_messages = messages
        outcome = next(self.outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeChatModel:
    def __init__(self, structured: FakeStructuredModel) -> None:
        self.structured = structured
        self.response_model: type[BaseModel] | None = None

    def with_structured_output(
        self,
        response_model: type[BaseModel],
        **kwargs: object,
    ) -> FakeStructuredModel:
        self.response_model = response_model
        assert kwargs == {"method": "json_mode", "include_raw": True}
        return self.structured


def _success(value: str) -> dict[str, object]:
    return {
        "raw": None,
        "parsed": ExampleOutput(value=value),
        "parsing_error": None,
    }


def test_chat_json_uses_pydantic_structured_output_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    structured = FakeStructuredModel([_success("ok")])
    model = FakeChatModel(structured)
    monkeypatch.setattr(llm, "_chat_model", lambda: model)

    result = llm.chat_json("Return JSON", [{"role": "user", "content": "hello"}], ExampleOutput)

    assert result == ExampleOutput(value="ok")
    assert model.response_model is ExampleOutput
    assert structured.calls == 1
    assert "ExampleOutput" in str(getattr(structured.last_messages[0], "content", ""))


def test_chat_json_retries_once_then_returns_valid_result(monkeypatch: pytest.MonkeyPatch) -> None:
    structured = FakeStructuredModel([RuntimeError("temporary"), _success("recovered")])
    monkeypatch.setattr(llm, "_chat_model", lambda: FakeChatModel(structured))

    result = llm.chat_json("Return JSON", [], ExampleOutput, max_retries=1)

    assert result.value == "recovered"
    assert structured.calls == 2


def test_chat_json_repairs_malformed_structured_output(monkeypatch: pytest.MonkeyPatch) -> None:
    malformed = {
        "raw": None,
        "parsed": None,
        "parsing_error": ValueError("malformed JSON"),
    }
    structured = FakeStructuredModel([malformed, _success("repaired")])
    monkeypatch.setattr(llm, "_chat_model", lambda: FakeChatModel(structured))

    result = llm.chat_json("Return JSON", [], ExampleOutput, max_retries=1)

    assert result.value == "repaired"
    assert structured.calls == 2
    assert "failed validation" in str(
        getattr(structured.last_messages[-1], "content", "")
    )


def test_chat_json_raises_gateway_error_after_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    structured = FakeStructuredModel([RuntimeError("provider unavailable")])
    monkeypatch.setattr(llm, "_chat_model", lambda: FakeChatModel(structured))

    with pytest.raises(llm.LLMError, match="after 1 attempts"):
        llm.chat_json("Return JSON", [], ExampleOutput, max_retries=0)


def test_embed_uses_gateway_adapter_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeEmbeddings:
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            assert texts == ["xin chào"]
            return [[0.1, 0.2]]

    monkeypatch.setattr(llm, "_embedding_model", lambda: FakeEmbeddings())

    assert llm.embed(["xin chào"]) == [[0.1, 0.2]]


def test_embed_empty_input_does_not_build_provider_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called() -> object:
        raise AssertionError("provider adapter must not be created for empty input")

    monkeypatch.setattr(llm, "_embedding_model", fail_if_called)

    assert llm.embed([]) == []


def test_fpt_embedding_adapter_sends_raw_text_and_provider_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    class FakeSettings:
        embed_model = "Vietnamese_Embedding"
        embed_api_base = "https://mkp-api.fptcloud.com/v1"
        embed_api_key = "test-only"
        embed_dimensions = 1024
        embed_input_type = "passage"
        embed_input_text_truncate = "none"

    class FakeAdapter:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(llm, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(llm, "OpenAIEmbeddings", FakeAdapter)

    llm._embedding_model()

    assert captured["dimensions"] == 1024
    assert captured["check_embedding_ctx_length"] is False
    assert captured["model_kwargs"]["encoding_format"] == "float"
    assert captured["model_kwargs"]["extra_body"] == {
        "input_type": "passage",
        "input_text_truncate": "none",
    }
