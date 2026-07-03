"""Hiring Operations Agent — LangGraph workflow (Phase 2 slice).

Builds the linear reasoning pipeline (Context Validation → Approval Package
Generation) and interrupts before ``wait_for_human``. Node identifiers match
``system_flow.md`` §7 / Diagram 3 and must not be renamed. The resume half
(intent classification, approve/modify/unsupported, mock execution) is Phase 3;
``wait_for_human`` is a pass-through placeholder here and the edge from it to
END is provisional.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from backend.agents.hiring.nodes import (
    action_planning_node,
    approval_package_generation_node,
    context_analysis_node,
    context_validation_node,
    decision_synthesis_node,
    draft_generation_node,
    evidence_graph_construction_node,
    issue_identification_node,
    operational_assessment_node,
    operations_package_generation_node,
)
from backend.core.common.ids import session_id_for
from backend.core.workflow.checkpointer import get_checkpointer
from backend.core.workflow.engine import run_to_interrupt as _run_to_interrupt
from backend.schemas.enums import WorkflowStage
from backend.schemas.meeting_package import MeetingPackage
from backend.schemas.workflow_state import SessionMetadata, WorkflowState

WAIT_FOR_HUMAN = "wait_for_human"

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


def build_hiring_graph() -> StateGraph:
    g = StateGraph(WorkflowState)
    for name, fn in _PIPELINE:
        g.add_node(name, fn)
    g.add_node(WAIT_FOR_HUMAN, _wait_for_human_node)

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
    g.add_edge(WAIT_FOR_HUMAN, END)  # provisional; Phase 3 replaces
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
