"""LLM client: mode selection, bounded retry, validation, and fallback.

This is the single entry point every reasoning/classification node uses. It
implements the retry policy from ``system_flow.md`` §15 (default 2 retries with
backoff, feeding the validation error back to the model) and the user-mandated
deterministic fallback when the LLM is unavailable or output stays invalid.

Behaviour by ``LLM_MODE``:
  * ``fallback`` — never calls the network; returns the caller's ``fallback_fn``
    result (or a minimal valid instance) validated against the schema.
  * ``cloud`` — calls the provider with bounded retries; on exhaustion, degrades
    to the fallback when ``LLM_FALLBACK_ENABLED`` is true, else raises.
"""

from __future__ import annotations

import json
import time
from typing import Callable, TypeVar, cast

from pydantic import BaseModel, ValidationError

from backend.core.common.config import Settings, get_settings
from backend.core.common.logging import get_logger
from backend.core.llm.base import (
    LLMProvider,
    LLMUnavailableError,
    LLMValidationError,
)
from backend.core.llm.fallback_provider import minimal_valid_instance

_M = TypeVar("_M", bound=BaseModel)

log = get_logger(__name__)

# A fallback function returns a schema instance, a dict, or a JSON string.
FallbackFn = Callable[[], "BaseModel | dict | str"]


def _strip_fences(text: str) -> str:
    """Remove Markdown code fences the model may wrap JSON in."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1] if "\n" in t else t
        if t.endswith("```"):
            t = t[: -len("```")]
        # drop a possible leading language tag left on the first line
        if t.lstrip().startswith("json"):
            t = t.lstrip()[len("json") :]
    return t.strip()


class LLMClient:
    """Structured-output client with retry + deterministic fallback."""

    def __init__(
        self,
        settings: Settings | None = None,
        provider: LLMProvider | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._injected_provider = provider
        self._cached_provider: LLMProvider | None = None

    @property
    def mode(self) -> str:
        return self._settings.llm_mode

    def _provider(self) -> LLMProvider:
        if self._injected_provider is not None:
            return self._injected_provider
        if self._cached_provider is None:
            # Imported lazily so ``fallback`` mode never requires httpx/config.
            from backend.core.llm.ollama_provider import OllamaProvider

            self._cached_provider = OllamaProvider(self._settings)
        return self._cached_provider

    # -- public API -------------------------------------------------------
    def generate_structured(
        self,
        prompt: str,
        schema: type[_M],
        *,
        fallback_fn: FallbackFn | None = None,
        system: str | None = None,
    ) -> _M:
        """Return a validated instance of ``schema``.

        In ``fallback`` mode the network is never touched. In ``cloud`` mode the
        provider is retried up to ``llm_max_retries`` times with the validation
        error fed back; on exhaustion it degrades to the fallback when enabled.
        """
        if self._settings.llm_mode == "fallback":
            return self._from_fallback(schema, fallback_fn)

        attempts = self._settings.llm_max_retries + 1
        current_prompt = prompt
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                raw = self._provider().complete_json(current_prompt, system=system)
            except LLMUnavailableError as exc:
                last_error = exc
                log.warning(
                    "LLM unavailable (attempt %d/%d): %s", attempt, attempts, exc
                )
            else:
                try:
                    obj = json.loads(_strip_fences(raw))
                    return schema.model_validate(obj)
                except (json.JSONDecodeError, ValidationError) as exc:
                    last_error = exc
                    log.warning(
                        "LLM output invalid (attempt %d/%d): %s",
                        attempt,
                        attempts,
                        exc,
                    )
                    current_prompt = self._augment_prompt(prompt, raw, exc)

            if attempt < attempts:
                time.sleep(self._settings.llm_retry_backoff_seconds * attempt)

        # Retries exhausted.
        if self._settings.llm_fallback_enabled:
            log.warning(
                "LLM exhausted after %d attempts; using deterministic fallback.",
                attempts,
            )
            return self._from_fallback(schema, fallback_fn)

        raise LLMValidationError(
            f"LLM failed after {attempts} attempts and fallback is disabled: "
            f"{last_error}"
        ) from last_error

    # -- helpers ----------------------------------------------------------
    def _from_fallback(
        self, schema: type[_M], fallback_fn: FallbackFn | None
    ) -> _M:
        if fallback_fn is None:
            return cast(_M, minimal_valid_instance(schema))
        result = fallback_fn()
        if isinstance(result, schema):
            return result
        if isinstance(result, BaseModel):
            return schema.model_validate(result.model_dump())
        if isinstance(result, str):
            return schema.model_validate_json(result)
        return schema.model_validate(result)

    @staticmethod
    def _augment_prompt(original: str, bad_output: str, error: Exception) -> str:
        return (
            f"{original}\n\n"
            "Your previous response could not be parsed/validated.\n"
            f"Previous response:\n{bad_output}\n\n"
            f"Validation error:\n{error}\n\n"
            "Return ONLY a corrected JSON object that satisfies the schema."
        )
