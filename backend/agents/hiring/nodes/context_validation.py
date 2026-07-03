"""Node: Context Validation (§7.1). Structural gatekeeper — no reasoning.

The Meeting Package is already schema-validated when bound into state; this node
enforces the business rules and routes an invalid package to a terminal
Rejected state.
"""

from __future__ import annotations

from backend.agents.hiring.nodes.base import with_message
from backend.schemas.enums import WorkflowStage
from backend.schemas.meeting_package import MeetingPackage
from backend.schemas.workflow_state import WorkflowState


def business_errors(mp: MeetingPackage) -> list[str]:
    errs: list[str] = []
    if mp.domain != "hiring":
        errs.append("domain must be 'hiring'")
    if not mp.transcript:
        errs.append("transcript is empty")
    if not mp.payload.candidate.name:
        errs.append("candidate is missing")
    if not mp.payload.role.title:
        errs.append("role is missing")
    return errs


def context_validation_node(state: WorkflowState) -> dict:
    mp = state["meeting_package"]
    errs = business_errors(mp)
    if errs:
        return with_message(
            state,
            {"workflow_stage": WorkflowStage.REJECTED},
            f"Meeting Package rejected: {'; '.join(errs)}.",
        )
    return with_message(
        state,
        {"workflow_stage": WorkflowStage.VALIDATED},
        f"Validated Meeting Package for {mp.payload.candidate.name}.",
    )
