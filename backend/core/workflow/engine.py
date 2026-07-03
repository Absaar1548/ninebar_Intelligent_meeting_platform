"""Generic workflow-run helpers (agent-agnostic).

Runs a compiled LangGraph to its interrupt for a given ``thread_id`` and emits
the runtime events (`system_flow.md` §15.1). Kept generic so any future domain
agent reuses it unchanged.
"""

from __future__ import annotations

from typing import Any

from backend.core.common.logging import get_logger
from backend.schemas.enums import EventType, WorkflowStage
from backend.schemas.events import WorkflowEvent

log = get_logger(__name__)


def thread_config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


def emit(meeting_id: str, event_type: EventType, **detail: Any) -> WorkflowEvent:
    evt = WorkflowEvent(type=event_type, meeting_id=meeting_id, detail=detail)
    log.info("event=%s meeting=%s %s", event_type.value, meeting_id, detail or "")
    return evt


def run_to_interrupt(app: Any, initial_state: dict, thread_id: str, meeting_id: str):
    """Invoke ``app`` to its interrupt; emit events; return the state snapshot."""
    emit(meeting_id, EventType.WORKFLOW_STARTED)
    cfg = thread_config(thread_id)
    app.invoke(initial_state, config=cfg)
    snap = app.get_state(cfg)
    if snap.values.get("workflow_stage") == WorkflowStage.REJECTED:
        emit(meeting_id, EventType.WORKFLOW_FAILED, reason="invalid_meeting_package")
    else:
        emit(meeting_id, EventType.OPERATIONS_PACKAGE_GENERATED)
        emit(meeting_id, EventType.APPROVAL_PACKAGE_GENERATED)
        emit(meeting_id, EventType.WAITING_FOR_APPROVAL)
    return snap
