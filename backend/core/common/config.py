"""Typed application configuration loaded from ``.env`` (pydantic-settings).

Every key in ``.env.example`` maps to a field here. ``OLLAMA_API_KEY`` is the
only real secret (``SecretStr``); everything else is non-sensitive local config.
Defaults let the app run even with no ``.env`` present (e.g. CI), in which case
``LLM_MODE`` defaults to ``cloud`` but the deterministic fallback still covers a
missing key/network.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root = three levels up from this file: backend/core/common/config.py
REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Application settings. Field names match ``.env`` keys (case-insensitive)."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- LLM behaviour ---
    llm_mode: Literal["cloud", "fallback"] = "cloud"
    llm_fallback_enabled: bool = True
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 2
    llm_retry_backoff_seconds: float = 2.0

    # --- Ollama Cloud API (only real secret) ---
    ollama_host: str = "https://ollama.com/v1"
    ollama_model: str = "glm-5.2"
    ollama_api_key: SecretStr = SecretStr("")

    # --- Backend API ---
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # --- Frontend (Gradio) ---
    gradio_host: str = "127.0.0.1"
    gradio_port: int = 7860
    backend_base_url: str = "http://127.0.0.1:8000"

    # --- Local runtime storage ---
    data_dir: Path = REPO_ROOT / "data"
    runtime_input_dir: Path = REPO_ROOT / "data" / "runtime" / "input"
    runtime_processing_dir: Path = REPO_ROOT / "data" / "runtime" / "processing"
    runtime_operations_dir: Path = REPO_ROOT / "data" / "runtime" / "operations"
    runtime_approvals_dir: Path = REPO_ROOT / "data" / "runtime" / "approvals"
    runtime_completed_dir: Path = REPO_ROOT / "data" / "runtime" / "completed"
    runtime_logs_dir: Path = REPO_ROOT / "data" / "runtime" / "logs"
    hiring_tracker_path: Path = REPO_ROOT / "data" / "hiring_tracker.json"

    # --- Logging ---
    log_level: str = "INFO"

    @property
    def runtime_dirs(self) -> list[Path]:
        """All runtime directories the File Watcher / session manager use."""
        return [
            self.runtime_input_dir,
            self.runtime_processing_dir,
            self.runtime_operations_dir,
            self.runtime_approvals_dir,
            self.runtime_completed_dir,
            self.runtime_logs_dir,
        ]

    @property
    def has_ollama_key(self) -> bool:
        return bool(self.ollama_api_key.get_secret_value())


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()
