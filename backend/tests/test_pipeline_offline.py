"""Full linear pipeline, offline — runs both fixtures to the WAIT_FOR_HUMAN
interrupt and asserts differentiated, evidence-grounded outcomes."""

from __future__ import annotations

from backend.agents.hiring.services.evidence import evidence_ids
from backend.agents.hiring.workflow import run_to_interrupt
from backend.schemas.enums import ApprovalStatus, ExecutionStatus, Recommendation, WorkflowStage
from backend.tests.conftest import load_meeting


def _run(name: str):
    mp = load_meeting(name)
    return run_to_interrupt(mp, thread_id=f"test-{name}")


def test_pipeline_interrupts_at_wait_for_human():
    snap = _run("strong")
    assert snap.next == ("wait_for_human",)
    assert snap.values["workflow_stage"] == WorkflowStage.WAITING_APPROVAL
    ap = snap.values["approval_package"]
    assert ap.approval_status is ApprovalStatus.PENDING
    assert ap.execution_status is ExecutionStatus.NOT_STARTED


def test_strong_recommends_move_forward():
    ap = _run("strong").values["approval_package"]
    assert ap.recommendation is Recommendation.MOVE_FORWARD
    assert ap.confidence >= 0.7


def test_borderline_is_not_move_forward():
    ap = _run("borderline").values["approval_package"]
    assert ap.recommendation is not Recommendation.MOVE_FORWARD
    assert ap.recommendation in {Recommendation.HOLD, Recommendation.ADDITIONAL_INTERVIEW}


def test_strong_and_borderline_differ():
    strong = _run("strong").values["approval_package"]
    border = _run("borderline").values["approval_package"]
    assert strong.recommendation is not border.recommendation
    assert strong.confidence > border.confidence


def test_approval_package_evidence_is_grounded():
    snap = _run("strong")
    values = snap.values
    ap = values["approval_package"]
    ids = evidence_ids(values["operations_package"].evidence_graph)
    assert ap.evidence, "recommendation must cite evidence"
    assert all(ref.evidence_id in ids for ref in ap.evidence)


def test_operations_package_fully_populated():
    ops = _run("strong").values["operations_package"]
    assert ops.context_analysis and ops.evidence_graph and ops.findings
    assert ops.assessment and ops.decision and ops.action_plan and ops.drafts
    assert ops.drafts.draft_email is not None


def test_session_chat_record_accumulates():
    msgs = _run("strong").values["messages"]
    # one message per node in the linear pipeline (10 nodes)
    assert len(msgs) >= 10
