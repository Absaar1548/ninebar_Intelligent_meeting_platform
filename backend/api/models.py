"""API request/response DTOs.

The workflow's own contracts (Approval Package, Execution Report) are reused
directly; these DTOs only wrap the transport surface.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from backend.schemas.approval_package import ApprovalPackage
from backend.schemas.execution import ExecutionReport

WAIT_FOR_HUMAN = "wait_for_human"


class StartSessionRequest(BaseModel):
    meeting_package: dict[str, Any]


class MessageRequest(BaseModel):
    message: str


class SessionView(BaseModel):
    """Human-facing snapshot of a session returned by every hiring endpoint."""

    model_config = ConfigDict(extra="ignore")

    session_id: str
    meeting_id: str
    workflow_stage: str
    waiting_for_human: bool
    approval_package: ApprovalPackage | None = None
    execution_results: ExecutionReport | None = None

    @classmethod
    def from_result(cls, result: Any) -> "SessionView":
        values = result.values
        stage = values.get("workflow_stage")
        return cls(
            session_id=result.session_id,
            meeting_id=result.meeting_id,
            workflow_stage=str(stage) if stage is not None else "unknown",
            waiting_for_human=(tuple(result.next) == (WAIT_FOR_HUMAN,)),
            approval_package=values.get("approval_package"),
            execution_results=values.get("execution_results"),
        )
