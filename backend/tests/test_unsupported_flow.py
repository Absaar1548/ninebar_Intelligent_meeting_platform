"""Unsupported flow — out-of-scope requests are rejected and the workflow stays
paused with no artifact change (§7.15, §13)."""

from __future__ import annotations

from backend.agents.hiring.workflow import resume, run_to_interrupt
from backend.schemas.enums import ApprovalStatus, Intent, WorkflowStage
from backend.tests.conftest import load_meeting


def test_unsupported_keeps_waiting_unchanged():
    mp = load_meeting("strong")
    run_to_interrupt(mp, thread_id="t-uns")
    snap = resume("what's the weather today?", thread_id="t-uns")
    v = snap.values

    assert snap.next == ("wait_for_human",)
    assert v["workflow_stage"] == WorkflowStage.WAITING_APPROVAL
    assert v["intent"] is Intent.UNSUPPORTED
    assert v["approval_package"].approval_status is ApprovalStatus.PENDING
    assert v.get("execution_results") is None  # execution never ran
    assert any("isn't supported" in m.content for m in v["messages"])


def test_unsupported_then_approve_still_works():
    mp = load_meeting("strong")
    run_to_interrupt(mp, thread_id="t-uns-approve")
    resume("tell me a joke", thread_id="t-uns-approve")
    snap = resume("approve", thread_id="t-uns-approve")
    assert snap.next == ()
    assert snap.values["workflow_stage"] == WorkflowStage.COMPLETED
