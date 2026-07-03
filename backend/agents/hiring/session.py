"""Hiring session orchestration.

Wraps the LangGraph workflow (``run_to_interrupt`` / ``resume``) with session
tracking + runtime persistence so the API router and the File Watcher stay thin.
A session is one checkpointer thread keyed by ``session_id_for(meeting_id)`` —
each Meeting Package owns exactly one session (§10).
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from backend.agents.hiring.workflow import (
    get_hiring_app,
    resume as _resume,
    run_to_interrupt,
)
from backend.core.common.config import Settings, get_settings
from backend.core.common.ids import session_id_for
from backend.core.common.json_io import read_json
from backend.core.common.logging import get_logger
from backend.core.workflow.engine import emit, thread_config
from backend.core.workflow.session import (
    SessionInfo,
    SessionRegistry,
    finalize_input_file,
    persist_artifacts,
)
from backend.schemas.enums import EventType, WorkflowStage
from backend.schemas.meeting_package import MeetingPackage

log = get_logger(__name__)


@dataclass
class SessionResult:
    session_id: str
    meeting_id: str
    values: dict
    next: tuple


class HiringSessionService:
    def __init__(
        self, settings: Settings | None = None, registry: SessionRegistry | None = None
    ) -> None:
        self._settings = settings or get_settings()
        self._registry = registry or SessionRegistry()
        self._input_files: dict[str, Path] = {}

    # -- helpers ----------------------------------------------------------
    def _finalize(self, snap, session_id: str, meeting_id: str) -> SessionResult:
        stage = snap.values.get("workflow_stage", WorkflowStage.CREATED)
        self._registry.upsert(session_id, meeting_id, stage)
        persist_artifacts(snap.values, self._settings)
        result = SessionResult(session_id, meeting_id, snap.values, tuple(snap.next))
        if result.next == ():  # terminal — move any tracked input file
            src = self._input_files.pop(session_id, None)
            if src is not None:
                finalize_input_file(src, self._settings)
        return result

    # -- public API -------------------------------------------------------
    def start_from_package(self, mp: MeetingPackage) -> SessionResult:
        session_id = session_id_for(mp.meeting_id)
        log.info("starting hiring session %s", session_id)
        # Register up front so the session is queryable (GET) while the pipeline
        # runs — the UI polls it for live per-node progress.
        self._registry.upsert(session_id, mp.meeting_id, WorkflowStage.CREATED)
        snap = run_to_interrupt(mp, thread_id=session_id)
        return self._finalize(snap, session_id, mp.meeting_id)

    def start_from_file(self, path: str | Path) -> SessionResult:
        path = Path(path)
        processing = self._settings.runtime_processing_dir / path.name
        processing.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(processing))
        try:
            mp = MeetingPackage.model_validate(read_json(processing))
        except (ValidationError, ValueError):
            log.exception("invalid Meeting Package: %s", path.name)
            finalize_input_file(processing, self._settings)
            raise
        emit(mp.meeting_id, EventType.MEETING_PACKAGE_CREATED, source=path.name)
        self._input_files[session_id_for(mp.meeting_id)] = processing
        return self.start_from_package(mp)

    def resume(self, session_id: str, message: str) -> SessionResult:
        info = self._registry.get(session_id)
        if info is None:
            raise KeyError(session_id)
        snap = _resume(message, thread_id=session_id)
        return self._finalize(snap, session_id, info.meeting_id)

    def get(self, session_id: str) -> SessionResult | None:
        info = self._registry.get(session_id)
        if info is None:
            return None
        snap = get_hiring_app().get_state(thread_config(session_id))
        return SessionResult(session_id, info.meeting_id, snap.values, tuple(snap.next))

    def list(self) -> list[SessionInfo]:
        return self._registry.list()
