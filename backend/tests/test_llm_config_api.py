"""LLM config API tests — masked reads, the single provider control
(mock | ollama | azure_openai), required-credential validation, and that the
shared client actually gets swapped. Offline (no reasoning call is made here)."""

from __future__ import annotations

import pytest
from pydantic import SecretStr

from backend.agents.hiring.nodes import get_llm_client
from backend.core.common.config import Settings
from backend.core.llm import runtime as rt


def _known_settings(**overrides) -> Settings:
    """A fully-specified baseline so assertions don't depend on a local .env.
    Defaults to the mock (offline) path with no keys."""
    base = dict(
        llm_mode="fallback",
        llm_provider="ollama",
        ollama_model="glm-5.2",
        ollama_host="https://ollama.com/v1",
        ollama_api_key=SecretStr(""),
        azure_openai_endpoint="",
        azure_openai_deployment="",
        azure_openai_api_version="2024-10-21",
        azure_openai_api_key=SecretStr(""),
    )
    base.update(overrides)
    return Settings(**base)


@pytest.fixture
def seed_runtime():
    """Seed the runtime singleton with a known mock (offline) config."""
    rt._runtime = rt.LLMRuntime(settings=_known_settings())
    yield
    rt.reset_llm_runtime()


def test_get_config_is_mock_and_masked(api_client, seed_runtime):
    body = api_client.get("/api/v1/llm/config").json()
    assert body["mode"] == "fallback"
    assert body["provider"] == "mock"  # composite: offline -> mock
    assert body["ollama_key_set"] is False
    assert body["azure_key_set"] is False
    # The raw secrets are never part of the view.
    assert "ollama_api_key" not in body
    assert "azure_api_key" not in body


def test_switch_to_ollama_requires_key_then_swaps_client(api_client, seed_runtime):
    # Ollama cloud with no key is rejected (validation lives in the backend).
    r = api_client.put("/api/v1/llm/config", json={"provider": "ollama"})
    assert r.status_code == 422

    r = api_client.put(
        "/api/v1/llm/config",
        json={"provider": "ollama", "ollama_api_key": "secret-xyz"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "ollama" and body["mode"] == "cloud"
    assert body["ollama_key_set"] is True
    assert "secret-xyz" not in r.text  # key never echoed back
    # The reasoning nodes' shared client was swapped to live cloud reasoning.
    assert get_llm_client().mode == "cloud"


def test_switch_back_to_mock_needs_no_key(api_client, seed_runtime):
    api_client.put(
        "/api/v1/llm/config",
        json={"provider": "ollama", "ollama_api_key": "k1"},
    )
    r = api_client.put("/api/v1/llm/config", json={"provider": "mock"})
    assert r.status_code == 200
    assert r.json()["provider"] == "mock" and r.json()["mode"] == "fallback"
    assert rt.get_llm_runtime().current().llm_mode == "fallback"
    assert get_llm_client().mode == "fallback"


def test_azure_requires_endpoint_deployment_and_key(api_client, seed_runtime):
    r = api_client.put("/api/v1/llm/config", json={"provider": "azure_openai"})
    assert r.status_code == 422
    assert "AZURE_OPENAI" in r.json()["detail"]

    r = api_client.put(
        "/api/v1/llm/config",
        json={
            "provider": "azure_openai",
            "azure_endpoint": "https://x.openai.azure.com",
            "azure_deployment": "gpt4o",
            "azure_api_version": "2024-10-21",
            "azure_api_key": "az-secret-123",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "azure_openai" and body["mode"] == "cloud"
    assert body["azure_deployment"] == "gpt4o"
    assert body["azure_key_set"] is True
    assert "az-secret-123" not in r.text


def test_blank_key_preserves_existing(api_client, seed_runtime):
    api_client.put(
        "/api/v1/llm/config",
        json={"provider": "ollama", "ollama_api_key": "k1"},
    )
    # Re-apply the same provider without a key (blank) — key must be kept.
    r = api_client.put("/api/v1/llm/config", json={"provider": "ollama"})
    assert r.status_code == 200
    assert r.json()["ollama_key_set"] is True
