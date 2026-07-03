"""Node: Decision Synthesis (§7.6). Grounded recommendation. Modification resume
entry point in Phase 3."""

from __future__ import annotations

from backend.agents.hiring.nodes.base import get_llm_client, with_message
from backend.agents.hiring.prompts.base import SYSTEM_PROMPT
from backend.agents.hiring.prompts.reasoning import decision_synthesis_prompt
from backend.agents.hiring.services.evidence import validate_decision_grounded
from backend.agents.hiring.services.fallbacks import fallback_decision
from backend.schemas.artifacts import Decision
from backend.schemas.enums import WorkflowStage
from backend.schemas.workflow_state import WorkflowState


def decision_synthesis_node(state: WorkflowState) -> dict:
    mp = state["meeting_package"]
    assessment = state["assessment"]
    findings = state["findings"]
    graph = state["evidence_graph"]
    decision = get_llm_client().generate_structured(
        decision_synthesis_prompt(assessment, findings, graph),
        Decision,
        system=SYSTEM_PROMPT,
        fallback_fn=lambda: fallback_decision(mp, assessment, findings, graph),
        validate=lambda d: validate_decision_grounded(d, graph),
    )
    return with_message(
        state,
        {"decision": decision, "workflow_stage": WorkflowStage.DECISION_SYNTHESIZED},
        f"Synthesized decision: {decision.recommendation.value.replace('_', ' ')}.",
    )
