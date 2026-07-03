"""Azure OpenAI provider via the Chat Completions REST API.

Azure differs from the OpenAI/Ollama shape in three ways: the model is selected
by the *deployment name* in the URL path (not a ``model`` field), the base URL
is the resource endpoint, and auth uses the ``api-key`` header (not ``Bearer``).
Otherwise the request/response bodies match, so — like ``OllamaProvider`` — this
stays a thin ``httpx`` transport with no extra dependency. Any transport/HTTP
failure surfaces as ``LLMUnavailableError`` so the client can fall back
deterministically.
"""

from __future__ import annotations

import httpx

from backend.core.common.config import Settings, get_settings
from backend.core.llm.base import LLMProvider, LLMUnavailableError


class AzureOpenAIProvider(LLMProvider):
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def _endpoint(self) -> str:
        s = self._settings
        base = s.azure_openai_endpoint.rstrip("/")
        return (
            f"{base}/openai/deployments/{s.azure_openai_deployment}"
            f"/chat/completions?api-version={s.azure_openai_api_version}"
        )

    def complete_json(self, prompt: str, *, system: str | None = None) -> str:
        settings = self._settings
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # No "model" field: the deployment in the URL selects the model.
        payload = {
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "stream": False,
        }
        headers = {
            "api-key": settings.azure_openai_api_key.get_secret_value(),
            "Content-Type": "application/json",
        }

        try:
            resp = httpx.post(
                self._endpoint,
                json=payload,
                headers=headers,
                timeout=settings.llm_timeout_seconds,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise LLMUnavailableError(
                f"Azure OpenAI request failed: {type(exc).__name__}: {exc}"
            ) from exc
