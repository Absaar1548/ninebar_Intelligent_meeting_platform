"""Ollama Cloud provider via the OpenAI-compatible ``/v1`` endpoint.

``OLLAMA_HOST`` already points at ``https://ollama.com/v1`` (OpenAI-compatible),
so we POST to ``{host}/chat/completions`` with ``httpx`` and request a JSON
object response. Any transport/HTTP failure is surfaced as
``LLMUnavailableError`` so the client can fall back deterministically.
"""

from __future__ import annotations

import httpx

from backend.core.common.config import Settings, get_settings
from backend.core.llm.base import LLMProvider, LLMUnavailableError


class OllamaProvider(LLMProvider):
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def _endpoint(self) -> str:
        return self._settings.ollama_host.rstrip("/") + "/chat/completions"

    def complete_json(self, prompt: str, *, system: str | None = None) -> str:
        settings = self._settings
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": settings.ollama_model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {settings.ollama_api_key.get_secret_value()}",
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
                f"Ollama request failed: {type(exc).__name__}: {exc}"
            ) from exc
