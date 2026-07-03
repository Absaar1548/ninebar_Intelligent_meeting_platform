"""Node: Unsupported (§7.15). Reject out-of-scope requests and explain the
supported operations; no artifact changes, workflow stays paused."""

from __future__ import annotations

from backend.agents.hiring.nodes.base import with_message
from backend.schemas.workflow_state import WorkflowState


def unsupported_node(state: WorkflowState) -> dict:
    return with_message(
        state,
        {},  # approval_status stays pending; workflow_stage stays waiting_approval
        "That request isn't supported here. I can only Approve the operational "
        "package, or apply a Modification — for example: change the recommendation, "
        "add/remove an action item, adjust the tracker update, or rewrite the email.",
    )
