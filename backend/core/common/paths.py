"""Filesystem path helpers for the local runtime storage.

Wraps the directory settings and provides ``ensure_runtime_dirs`` so the File
Watcher / session manager (later phases) can rely on the runtime tree existing.
"""

from __future__ import annotations

from pathlib import Path

from backend.core.common.config import REPO_ROOT, Settings, get_settings

__all__ = ["REPO_ROOT", "ensure_runtime_dirs", "runtime_dirs"]


def runtime_dirs(settings: Settings | None = None) -> list[Path]:
    """Return the list of runtime directories."""
    return (settings or get_settings()).runtime_dirs


def ensure_runtime_dirs(settings: Settings | None = None) -> list[Path]:
    """Create all runtime directories if missing; return them."""
    dirs = runtime_dirs(settings)
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs
