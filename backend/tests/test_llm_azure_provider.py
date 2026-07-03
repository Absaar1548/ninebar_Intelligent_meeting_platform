"""Azure OpenAI provider tests — request shape, auth header, response parsing,
error mapping, and provider selection. No network (``httpx.post`` is patched)."""

from __future__ import annotations

import httpx
import pytest
from pydantic import SecretStr

from backend.core.common.config import Settings
from backend.core.llm.azure_openai_provider import AzureOpenAIProvider
from backend.core.llm.base import LLMUnavailableError
from backend.core.llm.client import build_provider
from backend.core.llm.ollama_provider import OllamaProvider


class _Resp:
    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self) -> None:  # 200 in these tests
        return None

    def json(self) -> dict:
        return self._payload


def _settings(**overrides) -> Settings:
    base = dict(
        llm_provider="azure_openai",
        azure_openai_endpoint="https://myres.openai.azure.com/",
        azure_openai_deployment="gpt4o",
        azure_openai_api_version="2024-10-21",
        azure_openai_api_key=SecretStr("az-key"),
    )
    base.update(overrides)
    return Settings(**base)


def test_azure_request_shape(monkeypatch):
    captured: dict = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured.update(url=url, json=json, headers=headers)
        return _Resp({"choices": [{"message": {"content": '{"ok": true}'}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    out = AzureOpenAIProvider(_settings()).complete_json("hello", system="sys")

    assert out == '{"ok": true}'
    assert captured["url"] == (
        "https://myres.openai.azure.com/openai/deployments/gpt4o"
        "/chat/completions?api-version=2024-10-21"
    )
    # Azure uses the api-key header, never Bearer, and never sends a model field.
    assert captured["headers"]["api-key"] == "az-key"
    assert "Authorization" not in captured["headers"]
    assert "model" not in captured["json"]
    assert captured["json"]["response_format"] == {"type": "json_object"}
    assert [m["role"] for m in captured["json"]["messages"]] == ["system", "user"]


def test_azure_http_error_becomes_unavailable(monkeypatch):
    def boom(*args, **kwargs):
        raise httpx.ConnectError("nope")

    monkeypatch.setattr(httpx, "post", boom)
    with pytest.raises(LLMUnavailableError):
        AzureOpenAIProvider(_settings()).complete_json("x")


def test_build_provider_selects_by_provider():
    assert isinstance(build_provider(_settings(llm_provider="azure_openai")), AzureOpenAIProvider)
    assert isinstance(build_provider(_settings(llm_provider="ollama")), OllamaProvider)
