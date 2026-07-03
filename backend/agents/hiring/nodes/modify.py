"""Node: Modify (§7.14). Route back into the graph at the earliest affected node
without restarting. Approval Package stays pending; downstream regenerates. The
conditional edge out of this node picks the resume target."""

from __future__ import annotations

from backend.agents.hiring.nodes.base import with_chat_message
from backend.schemas.workflow_state import WorkflowState


def modify_node(state: WorkflowState) -> dict:
    target = state.get("modification_target")
    return with_chat_message(
        state,
        {},  # artifacts upstream of the target are preserved untouched
        f"Modification accepted — regenerating from {target}.",
    )
