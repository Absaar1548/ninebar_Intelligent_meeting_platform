"""Approval flow — resume with an approval message executes the mock adapters
and completes the workflow (§7.13, §7.16, §11)."""

from __future__ import annotations

from backend.agents.hiring.workflow import resume, run_to_interrupt
from backend.core.common.config import get_settings
from backend.schemas.enums import ApprovalStatus, ExecutionStatus, WorkflowStage
from backend.tests.conftest import load_meeting


def test_approve_executes_and_completes():
    mp = load_meeting("strong")
    run_to_interrupt(mp, thread_id="t-approve")
    snap = resume("approve all", thread_id="t-approve")
    v = snap.values

    assert snap.next == ()  # workflow ended
    assert v["workflow_stage"] == WorkflowStage.COMPLETED

    ap = v["approval_package"]
    assert ap.approval_status is ApprovalStatus.APPROVED
    assert ap.execution_status is ExecutionStatus.COMPLETED

    report = v["execution_results"]
    assert report.ok
    assert {r.adapter for r in report.results} == {"ats", "email", "teams"}
    assert all(r.ok for r in report.results)


def test_approve_writes_execution_log():
    mp = load_meeting("strong")
    run_to_interrupt(mp, thread_id="t-approve-log")
    resume("approve", thread_id="t-approve-log")
    log = get_settings().runtime_logs_dir / f"{mp.meeting_id}.execution.json"
    assert log.exists()


def test_human_comment_recorded_on_approval():
    mp = load_meeting("strong")
    run_to_interrupt(mp, thread_id="t-approve-cmt")
    snap = resume("approve — great candidate", thread_id="t-approve-cmt")
    assert any("great candidate" in c for c in snap.values["approval_package"].human_comments)
