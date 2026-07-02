"""Common platform utilities: config, logging, paths, ids, JSON IO."""

from backend.core.common.config import REPO_ROOT, Settings, get_settings
from backend.core.common.ids import (
    new_session_id,
    session_id_for,
    utcnow,
    utcnow_iso,
)
from backend.core.common.json_io import (
    dump_model,
    load_model,
    read_json,
    write_json,
)
from backend.core.common.logging import get_logger
from backend.core.common.paths import ensure_runtime_dirs, runtime_dirs

__all__ = [
    "REPO_ROOT",
    "Settings",
    "get_settings",
    "get_logger",
    "ensure_runtime_dirs",
    "runtime_dirs",
    "utcnow",
    "utcnow_iso",
    "new_session_id",
    "session_id_for",
    "read_json",
    "write_json",
    "load_model",
    "dump_model",
]
