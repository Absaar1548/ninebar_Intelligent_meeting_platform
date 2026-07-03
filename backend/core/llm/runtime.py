"""Runtime LLM configuration — the backend's single source of truth for the
*effective* provider / mode / credentials, and the thing that swaps the shared
client so a UI-driven change takes effect on the next workflow run.

All logic lives here (the API route stays a thin adapter). Applied values are
held **in memory only** — never written to disk or logged. ``.env`` / ``-e VAR``
remains the persistent path; a process restart reverts to those.

``apply`` rebuilds an ``LLMClient`` and installs it via the nodes' shared
``set_llm_client`` (imported lazily to avoid a core→agents import at module
load). ``snapshot`` returns a masked view: booleans for whether each key is set,
never the secret itself.
"""

from __future__ import annotations

from pydantic import SecretStr

from backend.core.common.config import Settings, get_settings
from backend.core.common.logging import get_logger
from backend.core.llm.client import LLMClient

log = get_logger(__name__)

# UI-friendly value key -> Settings field name. Key fields are marked so we can
# wrap them in SecretStr and treat a blank value as "leave the existing key".
# ``provider`` / ``mode`` are handled separately (see _mode_provider_overrides):
# the UI's single Provider control (mock | ollama | azure_openai) drives both.
_FIELD_MAP: dict[str, str] = {
    "ollama_model": "ollama_model",
    "ollama_host": "ollama_host",
    "ollama_api_key": "ollama_api_key",
    "azure_endpoint": "azure_openai_endpoint",
    "azure_deployment": "azure_openai_deployment",
    "azure_api_version": "azure_openai_api_version",
    "azure_api_key": "azure_openai_api_key",
}
_SECRET_FIELDS = {"ollama_api_key", "azure_openai_api_key"}
# The composite provider value "mock" means "no LLM" (mode=fallback).
MOCK_PROVIDER = "mock"


class LLMConfigError(ValueError):
    """The requested effective LLM configuration is incomplete/invalid."""


class LLMRuntime:
    """Holds the effective ``Settings`` and swaps the shared LLM client."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    # -- read -------------------------------------------------------------
    def current(self) -> Settings:
        return self._settings

    def snapshot(self) -> dict:
        """Masked, non-secret view of the effective configuration.

        ``provider`` is the composite UI value: ``mock`` when running offline
        (fallback), otherwise the cloud provider in use.
        """
        s = self._settings
        provider = MOCK_PROVIDER if s.llm_mode == "fallback" else s.llm_provider
        return {
            "mode": s.llm_mode,
            "provider": provider,
            "ollama_model": s.ollama_model,
            "ollama_host": s.ollama_host,
            "azure_endpoint": s.azure_openai_endpoint,
            "azure_deployment": s.azure_openai_deployment,
            "azure_api_version": s.azure_openai_api_version,
            "ollama_key_set": s.has_ollama_key,
            "azure_key_set": s.has_azure_key,
        }

    # -- write ------------------------------------------------------------
    def apply(self, update: dict) -> dict:
        """Merge ``update`` onto the effective settings, validate, swap the
        client, and return the new masked snapshot.

        Only provided, non-blank fields override; a blank key preserves the
        existing one (so you can re-apply without retyping the secret). Raises
        ``LLMConfigError`` if the resulting cloud config is missing credentials.
        """
        new = self._merge(update)
        self._validate(new)

        # Install the rebuilt client for the reasoning nodes. Imported lazily so
        # importing this module never drags in the agents package.
        from backend.agents.hiring.nodes.base import set_llm_client

        set_llm_client(LLMClient(settings=new))
        self._settings = new
        log.info(
            "LLM config applied: mode=%s provider=%s (ollama_key=%s azure_key=%s)",
            new.llm_mode,
            new.llm_provider,
            new.has_ollama_key,
            new.has_azure_key,
        )
        return self.snapshot()

    # -- helpers ----------------------------------------------------------
    def _merge(self, update: dict) -> Settings:
        overrides = self._value_overrides(update)
        overrides.update(self._mode_provider_overrides(update))
        return self._settings.model_copy(update=overrides)

    @staticmethod
    def _value_overrides(update: dict) -> dict:
        overrides: dict[str, object] = {}
        for ui_key, field in _FIELD_MAP.items():
            if ui_key not in update:
                continue
            value = update[ui_key]
            if value is None:
                continue
            if isinstance(value, str):
                value = value.strip()
                if value == "":  # blank -> leave the existing value untouched
                    continue
            if field in _SECRET_FIELDS:
                value = SecretStr(str(value))
            overrides[field] = value
        return overrides

    @staticmethod
    def _mode_provider_overrides(update: dict) -> dict:
        """Translate the UI's single Provider control into (mode, provider).

        ``mock`` -> offline (fallback); ``ollama`` / ``azure_openai`` -> cloud
        with that provider. Falls back to an explicit ``mode`` for direct API
        callers that don't send a provider.
        """
        provider = update.get("provider")
        if provider == MOCK_PROVIDER:
            return {"llm_mode": "fallback"}
        if provider in ("ollama", "azure_openai"):
            return {"llm_mode": "cloud", "llm_provider": provider}
        mode = update.get("mode")
        if mode in ("cloud", "fallback"):
            return {"llm_mode": mode}
        return {}

    @staticmethod
    def _validate(s: Settings) -> None:
        if s.llm_mode != "cloud":
            return  # fallback needs no credentials
        if s.llm_provider == "azure_openai":
            missing = [
                name
                for name, ok in (
                    ("AZURE_OPENAI_ENDPOINT", bool(s.azure_openai_endpoint.strip())),
                    ("AZURE_OPENAI_DEPLOYMENT", bool(s.azure_openai_deployment.strip())),
                    ("AZURE_OPENAI_API_KEY", s.has_azure_key),
                )
                if not ok
            ]
            if missing:
                raise LLMConfigError(
                    "Azure OpenAI cloud mode requires: " + ", ".join(missing)
                )
        elif not s.has_ollama_key:
            raise LLMConfigError("Ollama cloud mode requires an API key.")


_runtime: LLMRuntime | None = None


def get_llm_runtime() -> LLMRuntime:
    global _runtime
    if _runtime is None:
        _runtime = LLMRuntime()
    return _runtime


def reset_llm_runtime() -> None:
    """Drop the singleton so it re-reads settings — used by tests."""
    global _runtime
    _runtime = None
