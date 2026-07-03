"""Mock Execution engine (`system_flow.md` §7.16, §11, §15.2).

Runs the mock adapters against an approved Approval Package, models adapter
failure (config-driven), writes an execution log under ``data/runtime/logs``,
and emits the runtime events. No real external side effects.
"""

from __future__ import annotations

from backend.core.common.config import Settings, get_settings
from backend.core.common.json_io import dump_model
from backend.core.execution.ats_adapter import ATSAdapter
from backend.core.execution.base import ExecutionAdapter
from backend.core.execution.email_adapter import EmailAdapter
from backend.core.execution.teams_adapter import TeamsAdapter
from backend.core.workflow.engine import emit
from backend.schemas._time import utcnow
from backend.schemas.approval_package import ApprovalPackage
from backend.schemas.enums import EventType, ExecutionStatus
from backend.schemas.execution import ExecutionReport, ExecutionResult

ADAPTERS: list[ExecutionAdapter] = [ATSAdapter(), EmailAdapter(), TeamsAdapter()]


def execute(
    approval_package: ApprovalPackage, settings: Settings | None = None
) -> ExecutionReport:
    settings = settings or get_settings()
    meeting_id = approval_package.meeting_id
    fail = settings.mock_execution_fail_adapter.strip().lower()

    emit(meeting_id, EventType.EXECUTION_STARTED)
    results: list[ExecutionResult] = []
    for adapter in ADAPTERS:
        if fail and adapter.name == fail:
            results.append(ExecutionResult(
                adapter=adapter.name, ok=False,
                detail="Simulated adapter failure (MOCK_EXECUTION_FAIL_ADAPTER)."))
        else:
            results.append(adapter.run(approval_package))

    ok = all(r.ok for r in results)
    status = ExecutionStatus.COMPLETED if ok else ExecutionStatus.FAILED
    report = ExecutionReport(
        meeting_id=meeting_id, status=status, results=results, completed_at=utcnow()
    )

    _write_log(report, settings)
    if ok:
        emit(meeting_id, EventType.EXECUTION_COMPLETED)
        emit(meeting_id, EventType.WORKFLOW_COMPLETED)
    else:
        failed = ", ".join(r.adapter for r in results if not r.ok)
        emit(meeting_id, EventType.WORKFLOW_FAILED, reason=f"execution_failed:{failed}")
    return report


def _write_log(report: ExecutionReport, settings: Settings) -> None:
    path = settings.runtime_logs_dir / f"{report.meeting_id}.execution.json"
    dump_model(path, report)
