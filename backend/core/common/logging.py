"""Rich-based logging setup.

``get_logger`` returns a standard library logger wired to a single Rich handler,
with the level taken from ``LOG_LEVEL``. Idempotent: the root handler is
installed once.
"""

from __future__ import annotations

import logging

from rich.logging import RichHandler

from backend.core.common.config import get_settings

_CONFIGURED = False


def _configure_root() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    level = get_settings().log_level.upper()
    handler = RichHandler(rich_tracebacks=True, show_path=False, markup=True)
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[handler],
        force=True,
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for ``name``."""
    _configure_root()
    return logging.getLogger(name)
