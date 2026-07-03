"""Node: Approval Package Generation (§7.10). Derive the human-facing approval
artifact; set pending / not_started; then the graph interrupts at WAIT_FOR_HUMAN."""

from __future__ import annotations

from backend.agents.hiring.nodes.base import with_message
from backend.agents.hiring.services.approval_package_builder import (
    build_approval_package,
)
from backend.schemas.enums import ExecutionStatus, WorkflowStage
from backend.schemas.workflow_state import WorkflowState


def approval_package_generation_node(state: WorkflowState) -> dict:
    ap = build_approval_package(state["operations_package"])
    return with_message(
        state,
        {
            "approval_package": ap,
            "workflow_stage": WorkflowStage.WAITING_APPROVAL,
            "execution_status": ExecutionStatus.NOT_STARTED,
        },
        "Generated the Approval Package — awaiting human approval.",
    )
