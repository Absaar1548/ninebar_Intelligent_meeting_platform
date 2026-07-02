"""LLM client tests — mode selection, retry-with-feedback, and deterministic
fallback when the provider is unavailable or output stays invalid. No network."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field

from backend.core.common.config import Settings
from backend.core.llm.base import LLMUnavailableError, LLMValidationError
from backend.core.llm.client import LLMClient


class Widget(BaseModel):
    name: str
    score: float = Field(ge=0.0, le=1.0)


def _settings(**overrides) -> Settings:
    base = dict(llm_retry_backoff_seconds=0.0, llm_max_retries=1)
    base.update(overrides)
    return Settings(**base)


# --- fake providers --------------------------------------------------------
class AlwaysUnavailable:
    def __init__(self) -> None:
        self.calls = 0

    def complete_json(self, prompt: str, *, system: str | None = None) -> str:
        self.calls += 1
        raise LLMUnavailableError("boom")


class BadThenGood:
    def __init__(self) -> None:
        self.calls = 0

    def complete_json(self, prompt: str, *, system: str | None = None) -> str:
        self.calls += 1
        if self.calls == 1:
            return "not-json-at-all"
        return '{"name": "ok", "score": 0.9}'


# --- tests -----------------------------------------------------------------
def test_fallback_mode_uses_fallback_fn():
    client = LLMClient(settings=_settings(llm_mode="fallback"))
    out = client.generate_structured(
        "irrelevant", Widget, fallback_fn=lambda: {"name": "fb", "score": 0.5}
    )
    assert isinstance(out, Widget)
    assert out.name == "fb" and out.score == 0.5


def test_fallback_mode_without_fn_uses_minimal_instance():
    client = LLMClient(settings=_settings(llm_mode="fallback"))
    out = client.generate_structured("irrelevant", Widget)
    assert isinstance(out, Widget)
    assert out.name == "" and out.score == 0.0  # minimal valid instance


def test_cloud_unavailable_degrades_to_fallback():
    provider = AlwaysUnavailable()
    client = LLMClient(
        settings=_settings(llm_mode="cloud", llm_fallback_enabled=True),
        provider=provider,
    )
    out = client.generate_structured(
        "x", Widget, fallback_fn=lambda: Widget(name="fb", score=0.2)
    )
    assert out.name == "fb"
    assert provider.calls == 2  # max_retries(1) + 1


def test_cloud_retries_then_succeeds():
    provider = BadThenGood()
    client = LLMClient(
        settings=_settings(llm_mode="cloud", llm_fallback_enabled=True),
        provider=provider,
    )
    out = client.generate_structured("x", Widget)
    assert out.name == "ok" and out.score == 0.9
    assert provider.calls == 2  # first invalid, second valid


def test_cloud_exhausted_without_fallback_raises():
    provider = AlwaysUnavailable()
    client = LLMClient(
        settings=_settings(llm_mode="cloud", llm_fallback_enabled=False),
        provider=provider,
    )
    with pytest.raises(LLMValidationError):
        client.generate_structured("x", Widget, fallback_fn=lambda: {"name": "a", "score": 0.1})
