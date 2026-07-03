"""Hiring Operations Agent — LangGraph workflow.

Builds the full graph: the linear reasoning pipeline (Context Validation →
Approval Package Generation) interrupts before ``wait_for_human``; on resume,
the human message is classified and routed to Approve (→ mock execution → END),
Modify (→ resume at the earliest affected node → regenerate downstream → back
to WAIT_FOR_HUMAN), or Unsupported (→ WAIT_FOR_HUMAN, unchanged). Node
identifiers match ``system_flow.md`` §7 / Diagram 3 and must not be renamed.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from backend.agents.hiring.nodes import (
    action_planning_node,
    approval_package_generation_node,
    approve_node,
    context_analysis_node,
    context_validation_node,
    decision_synthesis_node,
    draft_generation_node,
    evidence_graph_construction_node,
    intent_classification_node,
    issue_identification_node,
    mock_execution_node,
    modify_node,
    operational_assessment_node,
    operations_package_generation_node,
    unsupported_node,
)
from backend.agents.hiring.services.intent import (
    ACTION_PLANNING,
    DECISION_SYNTHESIS,
    DRAFT_GENERATION,
)
from backend.core.common.ids import session_id_for
from backend.core.workflow.checkpointer import get_checkpointer
from backend.core.workflow.engine import emit, thread_config
from backend.core.workflow.engine import run_to_interrupt as _run_to_interrupt
from backend.schemas.enums import EventType, Intent, WorkflowStage
from backend.schemas.meeting_package import MeetingPackage
from backend.schemas.workflow_state import SessionMetadata, WorkflowState

WAIT_FOR_HUMAN = "wait_for_human"
_RESUME_TARGETS = {DECISION_SYNTHESIS, ACTION_PLANNING, DRAFT_GENERATION}

# The linear reasoning chain, in order. (name, node function)
_PIPELINE: list[tuple[str, object]] = [
    ("context_validation", context_validation_node),
    ("context_analysis", context_analysis_node),
    ("evidence_graph_construction", evidence_graph_construction_node),
    ("issue_identification", issue_identification_node),
    ("operational_assessment", operational_assessment_node),
    ("decision_synthesis", decision_synthesis_node),
    ("action_planning", action_planning_node),
    ("draft_generation", draft_generation_node),
    ("operations_package_generation", operations_package_generation_node),
    ("approval_package_generation", approval_package_generation_node),
]


def _wait_for_human_node(state: WorkflowState) -> dict:
    """Placeholder — the interrupt happens *before* this node. Phase 3 gives it
    a body and wires Intent Classification after it."""
    return {}


def _route_after_validation(state: WorkflowState) -> str:
    if state.get("workflow_stage") == WorkflowStage.REJECTED:
        return "reject"
    return "continue"


def _route_intent(state: WorkflowState) -> str:
    return state.get("intent", Intent.UNSUPPORTED).value


def _route_modification(state: WorkflowState) -> str:
    target = state.get("modification_target")
    if target in _RESUME_TARGETS:
        return target
    return "unsupported"


def build_hiring_graph() -> StateGraph:
    g = StateGraph(WorkflowState)
    for name, fn in _PIPELINE:
        g.add_node(name, fn)
    g.add_node(WAIT_FOR_HUMAN, _wait_for_human_node)
    # Resume-half nodes.
    g.add_node("intent_classification", intent_classification_node)
    g.add_node("approve", approve_node)
    g.add_node("modify", modify_node)
    g.add_node("unsupported", unsupported_node)
    g.add_node("mock_execution", mock_execution_node)

    g.add_edge(START, "context_validation")
    # Rejected packages terminate without reasoning (§7.1).
    g.add_conditional_edges(
        "context_validation",
        _route_after_validation,
        {"reject": END, "continue": "context_analysis"},
    )
    # Chain the rest of the linear pipeline.
    chain = [name for name, _ in _PIPELINE[1:]]
    for src, dst in zip(chain, chain[1:]):
        g.add_edge(src, dst)
    g.add_edge("approval_package_generation", WAIT_FOR_HUMAN)

    # Resume half: classify the human message, then route.
    g.add_edge(WAIT_FOR_HUMAN, "intent_classification")
    g.add_conditional_edges(
        "intent_classification",
        _route_intent,
        {"approval": "approve", "modification": "modify", "unsupported": "unsupported"},
    )
    g.add_edge("approve", "mock_execution")
    g.add_edge("mock_execution", END)
    # Modify re-enters the pipeline at the earliest affected node; those nodes
    # already chain forward to Approval Package Generation → WAIT_FOR_HUMAN.
    g.add_conditional_edges(
        "modify",
        _route_modification,
        {
            DECISION_SYNTHESIS: DECISION_SYNTHESIS,
            ACTION_PLANNING: ACTION_PLANNING,
            DRAFT_GENERATION: DRAFT_GENERATION,
            "unsupported": "unsupported",
        },
    )
    g.add_edge("unsupported", WAIT_FOR_HUMAN)
    return g


_app = None


def get_hiring_app():
    """Compiled graph singleton (shared checkpointer for interrupt/resume)."""
    global _app
    if _app is None:
        _app = build_hiring_graph().compile(
            checkpointer=get_checkpointer(),
            interrupt_before=[WAIT_FOR_HUMAN],
        )
    return _app


def reset_hiring_app() -> None:
    """Drop the compiled app (fresh checkpointer) — used by tests."""
    global _app
    _app = None


def initial_state(mp: MeetingPackage, thread_id: str) -> WorkflowState:
    return {
        "meeting_package": mp,
        "workflow_stage": WorkflowStage.CREATED,
        "messages": [],
        "session_metadata": SessionMetadata(
            meeting_id=mp.meeting_id, session_id=thread_id
        ),
    }


def run_to_interrupt(mp: MeetingPackage, thread_id: str | None = None):
    """Run the pipeline to the WAIT_FOR_HUMAN interrupt (or terminal Rejected).

    Returns the LangGraph state snapshot: ``.values`` holds the artifacts and
    ``.next`` is ``('wait_for_human',)`` when paused for approval.
    """
    thread_id = thread_id or session_id_for(mp.meeting_id)
    return _run_to_interrupt(
        get_hiring_app(), initial_state(mp, thread_id), thread_id, mp.meeting_id
    )


def resume(message: str, thread_id: str):
    """Resume a paused session with a human message.

    Injects the message and continues past the interrupt in one call
    (``Command(update=...)``). Returns the new state snapshot: for Approval the
    workflow ends (``next == ()``); for Modification/Unsupported it re-pauses
    at ``wait_for_human``.
    """
    app = get_hiring_app()
    cfg = thread_config(thread_id)
    meeting_id = app.get_state(cfg).values["meeting_package"].meeting_id
    emit(meeting_id, EventType.HUMAN_MESSAGE_RECEIVED, message=message)
    emit(meeting_id, EventType.WORKFLOW_RESUMED)
    app.invoke(Command(update={"human_feedback": message}), config=cfg)
    return app.get_state(cfg)
