"""Runtime workflow events (`system_flow.md` §15.1).

Lightweight, serializable records emitted across a run. The normal-run ordering
is documented on ``EventType`` in ``enums.py``. ``WorkflowFailed`` may be
emitted from any stage on unrecoverable failure.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas._time import utcnow
from backend.schemas.enums import EventType


class WorkflowEvent(BaseModel):
    """A single emitted event, tied to a meeting/session."""

    model_config = ConfigDict(extra="ignore")

    type: EventType
    meeting_id: str
    timestamp: datetime = Field(default_factory=utcnow)
    detail: dict[str, Any] = Field(default_factory=dict)
