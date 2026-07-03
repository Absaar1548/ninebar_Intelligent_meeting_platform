"""Generic workflow session tracking + runtime artifact persistence.

Agent-agnostic: an in-memory registry of sessions plus helpers that write the
Operations/Approval packages to the runtime directories and move a processed
input file to ``completed/``. No domain (hiring) imports.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from backend.core.common.config import Settings, get_settings
from backend.core.common.json_io import dump_model
from backend.core.common.logging import get_logger
from backend.schemas._time import utcnow
from backend.schemas.enums import WorkflowStage

log = get_logger(__name__)

_TERMINAL = {WorkflowStage.COMPLETED, WorkflowStage.FAILED, WorkflowStage.REJECTED}


class SessionInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    session_id: str
    meeting_id: str
    agent: str = "hiring"
    workflow_stage: WorkflowStage = WorkflowStage.CREATED
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @property
    def is_terminal(self) -> bool:
        return self.workflow_stage in _TERMINAL


class SessionRegistry:
    """In-memory session index (MVP single-process; prod = persistent store)."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionInfo] = {}

    def upsert(self, session_id: str, meeting_id: str, stage: WorkflowStage,
               agent: str = "hiring") -> SessionInfo:
        info = self._sessions.get(session_id)
        if info is None:
            info = SessionInfo(session_id=session_id, meeting_id=meeting_id,
                               agent=agent, workflow_stage=stage)
        else:
            info.workflow_stage = stage
            info.updated_at = utcnow()
        self._sessions[session_id] = info
        return info

    def get(self, session_id: str) -> SessionInfo | None:
        return self._sessions.get(session_id)

    def list(self) -> list[SessionInfo]:
        return list(self._sessions.values())


def persist_artifacts(state: dict, settings: Settings | None = None) -> None:
    """Write the Operations and Approval packages (when present) to runtime."""
    settings = settings or get_settings()
    ops = state.get("operations_package")
    if ops is not None:
        dump_model(settings.runtime_operations_dir / f"{ops.meeting_id}.json", ops)
    ap = state.get("approval_package")
    if ap is not None:
        dump_model(settings.runtime_approvals_dir / f"{ap.meeting_id}.json", ap)


def finalize_input_file(src: Path, settings: Settings | None = None) -> Path | None:
    """Move a processed input file into ``completed/``. Returns the new path."""
    settings = settings or get_settings()
    src = Path(src)
    if not src.exists():
        return None
    dest = settings.runtime_completed_dir / src.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    log.info("moved processed package to completed: %s", dest.name)
    return dest
