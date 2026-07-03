"""Node: Intent Classification (§7.12). The sole gateway between the human and
the workflow — every message is classified into exactly one supported intent."""

from __future__ import annotations

from backend.agents.hiring.nodes.base import get_llm_client
from backend.agents.hiring.prompts.base import SYSTEM_PROMPT
from backend.agents.hiring.prompts.reasoning import intent_classification_prompt
from backend.agents.hiring.services.intent import (
    ACTION_PLANNING,
    DECISION_SYNTHESIS,
    DRAFT_GENERATION,
    classify_intent,
)
from backend.schemas.artifacts import IntentClassification
from backend.schemas.enums import Intent
from backend.schemas.workflow_state import Message, WorkflowState

_VALID_TARGETS = {DECISION_SYNTHESIS, ACTION_PLANNING, DRAFT_GENERATION}


def intent_classification_node(state: WorkflowState) -> dict:
    message = state.get("human_feedback", "") or ""
    ap = state["approval_package"]

    result = get_llm_client().generate_structured(
        intent_classification_prompt(message, ap),
        IntentClassification,
        system=SYSTEM_PROMPT,
        fallback_fn=lambda: classify_intent(message),
    )

    intent = result.intent
    target = result.modification_target
    # Guard: a modification with an unresolvable target is Unsupported (A#7).
    if intent is Intent.MODIFICATION and target not in _VALID_TARGETS:
        intent = Intent.UNSUPPORTED
        target = None

    msgs = list(state.get("messages", []))
    msgs.append(Message(role="human", content=message, kind="chat"))
    label = intent.value + (f" -> {target}" if target else "")
    msgs.append(Message(role="agent", content=f"Classified intent: {label}.", kind="internal"))

    updates: dict = {"intent": intent, "messages": msgs}
    if target:
        updates["modification_target"] = target
    return updates
