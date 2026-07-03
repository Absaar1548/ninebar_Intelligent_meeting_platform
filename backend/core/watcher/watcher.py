"""File Watcher lifecycle (Watchdog Observer).

Production equivalent: an event bus (Kafka / Service Bus / Event Grid).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from watchdog.observers import Observer

from backend.core.common.logging import get_logger
from backend.core.watcher.handler import MeetingPackageHandler

log = get_logger(__name__)


def start_watcher(input_dir: str | Path, on_package: Callable[[str], object]) -> Observer:
    """Start watching ``input_dir`` for new Meeting Packages; return the Observer.

    Caller owns the Observer lifecycle (``observer.stop(); observer.join()``).
    """
    input_dir = Path(input_dir)
    input_dir.mkdir(parents=True, exist_ok=True)
    observer = Observer()
    observer.schedule(MeetingPackageHandler(on_package), str(input_dir), recursive=False)
    observer.start()
    log.info("file watcher started on %s", input_dir)
    return observer
