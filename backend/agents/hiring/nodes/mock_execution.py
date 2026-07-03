"""Node: Mock Execution (§7.16). Simulate downstream actions after approval and
finalize the workflow. No real external side effects."""

from __future__ import annotations

from backend.agents.hiring.nodes.base import with_chat_message
from backend.core.execution.engine import execute
from backend.core.renderer import render_execution_markdown
from backend.schemas.enums import WorkflowStage
from backend.schemas.workflow_state import WorkflowState


def mock_execution_node(state: WorkflowState) -> dict:
    ap = state["approval_package"]
    report = execute(ap)
    updated = ap.model_copy(update={"execution_status": report.status})
    stage = WorkflowStage.COMPLETED if report.ok else WorkflowStage.FAILED
    return with_chat_message(
        state,
        {
            "approval_package": updated,
            "execution_results": report,
            "execution_status": report.status,
            "workflow_stage": stage,
        },
        render_execution_markdown(report),
    )
