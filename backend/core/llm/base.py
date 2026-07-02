"""LLM provider interface and error taxonomy.

A provider is a thin transport that turns a prompt into raw (expected-JSON)
text. All parsing, schema validation, retry, and fallback live in
``LLMClient`` — providers stay dumb and swappable.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


class LLMError(Exception):
    """Base class for LLM errors."""


class LLMUnavailableError(LLMError):
    """The LLM could not be reached (network, timeout, auth, HTTP error).

    Distinct from a bad *response*: this means no usable output was produced and
    the deterministic fallback should take over when enabled.
    """


class LLMValidationError(LLMError):
    """The model produced output that could not be validated against the schema
    after all retries were exhausted."""


@runtime_checkable
class LLMProvider(Protocol):
    """Transport contract: prompt (+ optional system) → raw model text."""

    def complete_json(self, prompt: str, *, system: str | None = None) -> str:
        """Return the model's raw text response (expected to be JSON).

        Raises:
            LLMUnavailableError: if the provider cannot produce a response.
        """
        ...
