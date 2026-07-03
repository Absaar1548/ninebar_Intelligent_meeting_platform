"""Node: Action Planning (§7.7). Decision → concrete operational tasks.
Modification resume entry point in Phase 3."""

from __future__ import annotations

from backend.agents.hiring.nodes.base import (
    get_llm_client,
    revision_for,
    with_message,
)
from backend.agents.hiring.prompts.base import SYSTEM_PROMPT
from backend.agents.hiring.prompts.reasoning import action_planning_prompt
from backend.agents.hiring.services.fallbacks import fallback_action_plan
from backend.schemas.artifacts import ActionPlan
from backend.schemas.enums import WorkflowStage
from backend.schemas.workflow_state import WorkflowState


def action_planning_node(state: WorkflowState) -> dict:
    mp = state["meeting_package"]
    decision = state["decision"]
    assessment = state["assessment"]
    ctx = state["interview_context"]
    revision = revision_for(state, "action_planning")
    plan = get_llm_client().generate_structured(
        action_planning_prompt(decision, assessment, ctx, revision=revision),
        ActionPlan,
        system=SYSTEM_PROMPT,
        fallback_fn=lambda: fallback_action_plan(mp, decision),
    )
    return with_message(
        state,
        {"action_plan": plan, "workflow_stage": WorkflowStage.ACTIONS_PLANNED},
        f"Planned {len(plan.items)} action item(s).",
    )
