"""Mock execution engine — adapters simulate + log; failure is modelled
(§7.16, §15.2, Appendix A#10)."""

from __future__ import annotations

from backend.agents.hiring.workflow import run_to_interrupt
from backend.core.common.config import Settings, get_settings
from backend.core.execution.engine import execute
from backend.schemas.enums import ExecutionStatus
from backend.tests.conftest import load_meeting


def _approval_package(thread: str):
    mp = load_meeting("strong")
    return run_to_interrupt(mp, thread_id=thread).values["approval_package"]


def test_all_adapters_succeed_and_log_written():
    ap = _approval_package("t-exec-ok")
    report = execute(ap, settings=Settings(mock_execution_fail_adapter=""))
    assert report.status is ExecutionStatus.COMPLETED
    assert report.ok
    assert len(report.results) == 3 and all(r.ok for r in report.results)
    log = get_settings().runtime_logs_dir / f"{ap.meeting_id}.execution.json"
    assert log.exists()


def test_failure_injection_marks_report_failed():
    ap = _approval_package("t-exec-fail")
    report = execute(ap, settings=Settings(mock_execution_fail_adapter="teams"))
    assert report.status is ExecutionStatus.FAILED
    assert not report.ok
    failed = [r for r in report.results if not r.ok]
    assert len(failed) == 1 and failed[0].adapter == "teams"


def test_adapter_details_reference_approval_package():
    ap = _approval_package("t-exec-detail")
    report = execute(ap, settings=Settings(mock_execution_fail_adapter=""))
    by_name = {r.adapter: r.detail for r in report.results}
    assert ap.tracker_updates.candidate_id in by_name["ats"]
    assert ap.draft_email.to in by_name["email"]
