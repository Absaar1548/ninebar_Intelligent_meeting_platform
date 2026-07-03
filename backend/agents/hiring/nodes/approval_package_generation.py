"""Node: Approval Package Generation (§7.10). Derive the human-facing approval
artifact; set pending / not_started; post the agent's recommendation to chat;
then the graph interrupts at WAIT_FOR_HUMAN."""

from __future__ import annotations

from backend.agents.hiring.nodes.base import with_chat_message
from backend.agents.hiring.services.approval_package_builder import (
    build_approval_package,
)
from backend.core.renderer import render_agent_recommendation
from backend.schemas.enums import ExecutionStatus, WorkflowStage
from backend.schemas.workflow_state import WorkflowState


def approval_package_generation_node(state: WorkflowState) -> dict:
    ap = build_approval_package(state["operations_package"])
    return with_chat_message(
        state,
        {
            "approval_package": ap,
            "workflow_stage": WorkflowStage.WAITING_APPROVAL,
            "execution_status": ExecutionStatus.NOT_STARTED,
        },
        render_agent_recommendation(ap),
    )
