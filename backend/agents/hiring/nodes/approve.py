"""Node: Approve (§7.13). Confirm human approval and hand off to execution."""

from __future__ import annotations

from backend.agents.hiring.nodes.base import with_chat_message
from backend.schemas.enums import ApprovalStatus, WorkflowStage
from backend.schemas.workflow_state import WorkflowState


def approve_node(state: WorkflowState) -> dict:
    ap = state["approval_package"]
    message = (state.get("human_feedback") or "").strip()
    comments = list(ap.human_comments)
    if message:
        comments.append(message)
    approved = ap.model_copy(
        update={"approval_status": ApprovalStatus.APPROVED, "human_comments": comments}
    )
    return with_chat_message(
        state,
        {"approval_package": approved, "workflow_stage": WorkflowStage.EXECUTING},
        "Approval recorded — proceeding to mock execution.",
    )
