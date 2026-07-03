"""Node: Draft Generation (§7.8). Human-consumable drafts for planned actions.
Modification resume entry point (e.g. "rewrite email") in Phase 3."""

from __future__ import annotations

from backend.agents.hiring.nodes.base import get_llm_client, with_message
from backend.agents.hiring.prompts.base import SYSTEM_PROMPT
from backend.agents.hiring.prompts.reasoning import draft_generation_prompt
from backend.agents.hiring.services.fallbacks import fallback_drafts
from backend.schemas.artifacts import Drafts
from backend.schemas.enums import WorkflowStage
from backend.schemas.workflow_state import WorkflowState


def draft_generation_node(state: WorkflowState) -> dict:
    mp = state["meeting_package"]
    action_plan = state["action_plan"]
    decision = state["decision"]
    ctx = state["interview_context"]
    drafts = get_llm_client().generate_structured(
        draft_generation_prompt(action_plan, decision, ctx),
        Drafts,
        system=SYSTEM_PROMPT,
        fallback_fn=lambda: fallback_drafts(mp, decision, action_plan),
    )
    return with_message(
        state,
        {"drafts": drafts, "workflow_stage": WorkflowStage.DRAFTS_GENERATED},
        "Generated draft communications.",
    )
