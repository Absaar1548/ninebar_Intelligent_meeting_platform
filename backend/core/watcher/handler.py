"""Watchdog event handler for the runtime input directory.

Generic: it detects a new ``*.json`` Meeting Package and invokes an injected
``on_package(path)`` callback. Wiring the callback to a specific agent's session
service happens at composition time (FastAPI startup / the run entrypoint).
"""

from __future__ import annotations

from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler

from backend.core.common.logging import get_logger

log = get_logger(__name__)


class MeetingPackageHandler(FileSystemEventHandler):
    def __init__(self, on_package: Callable[[str], object]) -> None:
        self._on_package = on_package

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = str(event.src_path)
        if not path.lower().endswith(".json"):
            return
        log.info("file watcher detected new meeting package: %s", path)
        try:
            self._on_package(path)
        except Exception:  # noqa: BLE001 - watcher must not die on one bad file
            log.exception("file watcher failed to process %s", path)
