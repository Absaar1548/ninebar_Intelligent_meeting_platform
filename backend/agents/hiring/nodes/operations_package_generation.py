"""Node: Operations Package Generation (§7.9). Deterministic assembly of the
internal reasoning artifact. Modification resume convergence point in Phase 3."""

from __future__ import annotations

from backend.agents.hiring.nodes.base import with_message
from backend.agents.hiring.services.operations_package_builder import (
    build_operations_package,
)
from backend.schemas.enums import WorkflowStage
from backend.schemas.workflow_state import WorkflowState


def operations_package_generation_node(state: WorkflowState) -> dict:
    mp = state["meeting_package"]
    ops = build_operations_package(
        meeting_id=mp.meeting_id,
        interview_context=state["interview_context"],
        evidence_graph=state["evidence_graph"],
        findings=state["findings"],
        assessment=state["assessment"],
        decision=state["decision"],
        action_plan=state["action_plan"],
        drafts=state["drafts"],
    )
    return with_message(
        state,
        {
            "operations_package": ops,
            "workflow_stage": WorkflowStage.OPERATIONS_PACKAGE_GENERATED,
        },
        "Assembled the Operations Package.",
    )
