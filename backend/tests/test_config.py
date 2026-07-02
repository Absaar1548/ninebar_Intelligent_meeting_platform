"""Configuration tests — settings load, LLM mode is valid, paths resolve."""

from __future__ import annotations

from backend.core.common.config import get_settings
from backend.core.common.paths import ensure_runtime_dirs, runtime_dirs


def test_settings_load_and_llm_mode_valid():
    s = get_settings()
    assert s.llm_mode in {"cloud", "fallback"}
    assert s.llm_max_retries >= 0
    assert s.ollama_host.startswith("http")


def test_get_settings_is_cached():
    assert get_settings() is get_settings()


def test_runtime_dirs_shape_and_paths():
    s = get_settings()
    dirs = runtime_dirs(s)
    assert len(dirs) == 6
    # hiring tracker is a real file that ships with the repo
    assert s.hiring_tracker_path.exists()


def test_ensure_runtime_dirs_creates_all():
    created = ensure_runtime_dirs()
    assert len(created) == 6
    for d in created:
        assert d.exists() and d.is_dir()
