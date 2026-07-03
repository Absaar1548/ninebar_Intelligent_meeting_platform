"""File Watcher — Meeting Package ingestion trigger (event-bus stand-in)."""

from backend.core.watcher.handler import MeetingPackageHandler
from backend.core.watcher.watcher import start_watcher

__all__ = ["MeetingPackageHandler", "start_watcher"]
