"""Node: Operational Assessment (§7.5). Hiring assessment — still no actions."""

from __future__ import annotations

from backend.agents.hiring.nodes.base import get_llm_client, with_message
from backend.agents.hiring.prompts.base import SYSTEM_PROMPT
from backend.agents.hiring.prompts.reasoning import operational_assessment_prompt
from backend.agents.hiring.services.fallbacks import fallback_assessment
from backend.schemas.artifacts import Assessment
from backend.schemas.enums import WorkflowStage
from backend.schemas.workflow_state import WorkflowState


def operational_assessment_node(state: WorkflowState) -> dict:
    mp = state["meeting_package"]
    ctx = state["interview_context"]
    findings = state["findings"]
    graph = state["evidence_graph"]
    assessment = get_llm_client().generate_structured(
        operational_assessment_prompt(ctx, findings, graph),
        Assessment,
        system=SYSTEM_PROMPT,
        fallback_fn=lambda: fallback_assessment(mp, findings, graph),
    )
    return with_message(
        state,
        {"assessment": assessment, "workflow_stage": WorkflowStage.ASSESSED},
        f"Assessed suitability: {assessment.suitability} "
        f"(confidence {assessment.confidence:.2f}).",
    )
