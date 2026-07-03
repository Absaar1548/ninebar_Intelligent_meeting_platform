"""Standalone File Watcher entrypoint (composition root).

    python -m backend.core.watcher.run

Wires the generic watcher to the Hiring session service and blocks. The FastAPI
app also starts the watcher in-process; this is for running it on its own.
"""

from __future__ import annotations

import time

from backend.agents.hiring.session import HiringSessionService
from backend.core.common.config import get_settings
from backend.core.watcher.watcher import start_watcher


def main() -> None:
    settings = get_settings()
    service = HiringSessionService(settings)
    observer = start_watcher(settings.runtime_input_dir, service.start_from_file)
    print(f"Watching {settings.runtime_input_dir} for Meeting Packages. Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
