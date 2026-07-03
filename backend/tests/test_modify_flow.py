"""Modification flow — resume at the earliest affected node, regenerate
downstream only, and return to WAIT_FOR_HUMAN (§7.14, §12)."""

from __future__ import annotations

from backend.agents.hiring.workflow import resume, run_to_interrupt
from backend.schemas.enums import ApprovalStatus, Intent, WorkflowStage
from backend.tests.conftest import load_meeting


def test_rewrite_email_reflows_and_preserves_upstream():
    mp = load_meeting("strong")
    s0 = run_to_interrupt(mp, thread_id="t-mod-email")
    decision_before = s0.values["decision"].model_dump()
    findings_before = s0.values["findings"].model_dump()

    s1 = resume("please rewrite the email", thread_id="t-mod-email")
    v = s1.values
    assert s1.next == ("wait_for_human",)  # re-paused for approval
    assert v["workflow_stage"] == WorkflowStage.WAITING_APPROVAL
    assert v["intent"] is Intent.MODIFICATION
    assert v["modification_target"] == "draft_generation"
    assert v["approval_package"].approval_status is ApprovalStatus.PENDING
    # Artifacts upstream of draft_generation are untouched.
    assert v["decision"].model_dump() == decision_before
    assert v["findings"].model_dump() == findings_before


def test_change_recommendation_routes_to_decision_synthesis():
    mp = load_meeting("borderline")
    s0 = run_to_interrupt(mp, thread_id="t-mod-rec")
    findings_before = s0.values["findings"].model_dump()

    s1 = resume("please reconsider the recommendation", thread_id="t-mod-rec")
    assert s1.values["modification_target"] == "decision_synthesis"
    assert s1.next == ("wait_for_human",)
    # findings are upstream of decision_synthesis → preserved
    assert s1.values["findings"].model_dump() == findings_before


def test_modify_then_approve_completes():
    mp = load_meeting("strong")
    run_to_interrupt(mp, thread_id="t-mod-approve")
    resume("rewrite the email", thread_id="t-mod-approve")
    snap = resume("approve", thread_id="t-mod-approve")
    assert snap.next == ()
    assert snap.values["workflow_stage"] == WorkflowStage.COMPLETED
