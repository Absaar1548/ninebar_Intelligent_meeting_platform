"""Deterministic intent classifier + modification-target mapping (§10, §12).

Used as the intent node's ``fallback_fn`` and as the whole classifier offline.
Every human message maps to exactly one supported intent; an ambiguous message
or a modification with no resolvable target resolves to Unsupported, which
safely keeps the workflow paused (Appendix A#5/#7).
"""

from __future__ import annotations

from backend.schemas.artifacts import IntentClassification
from backend.schemas.enums import Intent

# Resume-target node names (must match the graph node ids).
DECISION_SYNTHESIS = "decision_synthesis"
ACTION_PLANNING = "action_planning"
DRAFT_GENERATION = "draft_generation"

_APPROVAL_CUES = (
    "approve", "approval", "approved", "execute", "proceed", "go ahead",
    "looks good", "lgtm", "ship it", "send it", "sign off", "sign-off", "accept",
)
_MODIFY_VERBS = (
    "rewrite", "reword", "retone", "revise", "change", "modify", "update", "edit",
    "adjust", "redo", "remove", "add", "replace", "shorten", "reconsider", "redraft",
)
_EMAIL_CUES = ("email", "e-mail", "draft", "letter", "note to", "message to")
_DECISION_CUES = (
    "recommendation", "recommend", "decision", "reject", "hold", "move forward",
    "advance", "reconsider", "verdict", "outcome",
)
_ACTION_CUES = (
    "action", "task", "tracker", "ats", "schedule", "notify", "hiring manager",
    "next step", "follow-up", "follow up",
)


def _has(text: str, cues: tuple[str, ...]) -> bool:
    return any(cue in text for cue in cues)


def _infer_target(text: str) -> str | None:
    if _has(text, _EMAIL_CUES):
        return DRAFT_GENERATION
    if _has(text, _DECISION_CUES):
        return DECISION_SYNTHESIS
    if _has(text, _ACTION_CUES):
        return ACTION_PLANNING
    return None


def classify_intent(message: str) -> IntentClassification:
    text = (message or "").lower().strip()
    if not text:
        return IntentClassification(intent=Intent.UNSUPPORTED, rationale="empty message")

    if _has(text, _APPROVAL_CUES):
        return IntentClassification(intent=Intent.APPROVAL,
                                    rationale="approval cue matched")

    target = _infer_target(text)
    if target is not None and (_has(text, _MODIFY_VERBS)
                               or _has(text, _EMAIL_CUES + _DECISION_CUES + _ACTION_CUES)):
        return IntentClassification(intent=Intent.MODIFICATION,
                                    modification_target=target,
                                    rationale=f"modification -> {target}")

    if _has(text, _MODIFY_VERBS):
        return IntentClassification(intent=Intent.UNSUPPORTED,
                                    rationale="modification target unresolved")

    return IntentClassification(intent=Intent.UNSUPPORTED,
                                rationale="no supported operational intent")
