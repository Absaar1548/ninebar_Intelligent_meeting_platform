"""LangGraph workflow state (`system_flow.md` §14.1).

Modeled as a ``TypedDict`` (``total=False``) so LangGraph nodes can return
partial updates, with Pydantic models as the typed values for each artifact.
Every field is scoped to a single interview session; there is no shared or
conversational memory across sessions in the MVP. Keys here are frozen in
Phase 1; Phase 2 wires this into the ``StateGraph``.
"""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas._time import utcnow
from backend.schemas.approval_package import ApprovalPackage
from backend.schemas.artifacts import (
    ActionPlan,
    Assessment,
    Decision,
    Drafts,
    EvidenceGraph,
    Findings,
    InterviewContext,
)
from backend.schemas.enums import ExecutionStatus, Intent, WorkflowStage
from backend.schemas.execution import ExecutionReport
from backend.schemas.meeting_package import MeetingPackage
from backend.schemas.operations_package import OperationsPackage


class Message(BaseModel):
    """One entry in the session's ordered chat/interaction record.

    ``kind`` separates the human-facing conversation (``chat``) from the
    internal reasoning trace (``internal``) so the UI can route them to the
    chat vs. the "Internal Processing & Memory" panel.
    """

    model_config = ConfigDict(extra="ignore")

    role: str  # "agent" | "human" | "system"
    content: str
    kind: str = "internal"  # "internal" (trace) | "chat" (human-facing)
    timestamp: datetime = Field(default_factory=utcnow)


class SessionMetadata(BaseModel):
    """Session identity & bookkeeping (written by the router / engine)."""

    model_config = ConfigDict(extra="ignore")

    meeting_id: str
    session_id: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class WorkflowState(TypedDict, total=False):
    """Per-interview isolated state. Field → producing node per §14.1."""

    # Input contract (immutable after Context Validation)
    meeting_package: MeetingPackage

    # Reasoning artifacts (linear pipeline)
    interview_context: InterviewContext
    evidence_graph: EvidenceGraph
    findings: Findings
    assessment: Assessment
    decision: Decision
    action_plan: ActionPlan
    drafts: Drafts

    # Terminal artifacts
    operations_package: OperationsPackage
    approval_package: ApprovalPackage

    # State-machine / human-in-the-loop
    workflow_stage: WorkflowStage
    human_feedback: str
    intent: Intent
    modification_target: str  # resume node for a Modification
    execution_status: ExecutionStatus
    execution_results: ExecutionReport

    # Session bookkeeping
    messages: list[Message]
    session_metadata: SessionMetadata
