"""Mock execution results (`system_flow.md` §7.16, §15.2).

Produced by the Mock Execution engine when an approved Approval Package is
executed. Adapter failures are modelled so production adapters reuse the same
shape and failure path.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas._time import utcnow
from backend.schemas.enums import ExecutionStatus


class ExecutionResult(BaseModel):
    """Outcome of a single mock adapter (ATS / email / Teams)."""

    model_config = ConfigDict(extra="ignore")

    adapter: str
    ok: bool
    detail: str
    timestamp: datetime = Field(default_factory=utcnow)


class ExecutionReport(BaseModel):
    """Aggregate result of a mock execution run."""

    model_config = ConfigDict(extra="ignore")

    meeting_id: str
    status: ExecutionStatus = ExecutionStatus.NOT_STARTED
    results: list[ExecutionResult] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None

    @property
    def ok(self) -> bool:
        return self.status is ExecutionStatus.COMPLETED
