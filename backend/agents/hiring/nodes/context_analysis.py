"""Node: Context Analysis (§7.2). Understand the hiring context — no judgement."""

from __future__ import annotations

from backend.agents.hiring.nodes.base import get_llm_client, with_message
from backend.agents.hiring.prompts.base import SYSTEM_PROMPT
from backend.agents.hiring.prompts.reasoning import context_analysis_prompt
from backend.agents.hiring.services.fallbacks import fallback_interview_context
from backend.schemas.artifacts import InterviewContext
from backend.schemas.enums import WorkflowStage
from backend.schemas.workflow_state import WorkflowState


def context_analysis_node(state: WorkflowState) -> dict:
    mp = state["meeting_package"]
    ctx = get_llm_client().generate_structured(
        context_analysis_prompt(mp),
        InterviewContext,
        system=SYSTEM_PROMPT,
        fallback_fn=lambda: fallback_interview_context(mp),
    )
    return with_message(
        state,
        {"interview_context": ctx, "workflow_stage": WorkflowStage.CONTEXT_ANALYZED},
        "Analyzed the interview context.",
    )
