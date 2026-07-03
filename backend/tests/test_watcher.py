"""File Watcher — handler routing + the input→processing→completed lifecycle."""

from __future__ import annotations

import shutil

from watchdog.events import FileCreatedEvent

from backend.agents.hiring.session import HiringSessionService
from backend.core.common.config import REPO_ROOT, Settings
from backend.core.watcher.handler import MeetingPackageHandler

STRONG = REPO_ROOT / "data" / "fixtures" / "meeting_packages" / "meeting_package_strong.json"


def test_handler_invokes_callback_for_json(tmp_path):
    seen: list[str] = []
    MeetingPackageHandler(seen.append).on_created(
        FileCreatedEvent(str(tmp_path / "pkg.json"))
    )
    assert seen == [str(tmp_path / "pkg.json")]


def test_handler_ignores_non_json(tmp_path):
    seen: list[str] = []
    MeetingPackageHandler(seen.append).on_created(
        FileCreatedEvent(str(tmp_path / "notes.txt"))
    )
    assert seen == []


def _tmp_settings(tmp_path) -> Settings:
    b = tmp_path
    settings = Settings(
        llm_mode="fallback",
        runtime_input_dir=b / "input",
        runtime_processing_dir=b / "processing",
        runtime_operations_dir=b / "operations",
        runtime_approvals_dir=b / "approvals",
        runtime_completed_dir=b / "completed",
        runtime_logs_dir=b / "logs",
    )
    for d in settings.runtime_dirs:
        d.mkdir(parents=True, exist_ok=True)
    return settings


def test_input_processing_completed_lifecycle(tmp_path):
    settings = _tmp_settings(tmp_path)
    service = HiringSessionService(settings=settings)

    src = settings.runtime_input_dir / "meeting_package_strong.json"
    shutil.copy(STRONG, src)

    result = service.start_from_file(src)
    assert result.next == ("wait_for_human",)
    assert not src.exists()  # moved out of input
    assert (settings.runtime_processing_dir / src.name).exists()
    # artifacts persisted
    assert (settings.runtime_operations_dir / f"{result.meeting_id}.json").exists()
    assert (settings.runtime_approvals_dir / f"{result.meeting_id}.json").exists()

    # Approve → terminal → source file moves to completed.
    done = service.resume(result.session_id, "approve")
    assert done.next == ()
    assert (settings.runtime_completed_dir / src.name).exists()
    assert not (settings.runtime_processing_dir / src.name).exists()
