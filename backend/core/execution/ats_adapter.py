"""Mock ATS / tracker adapter. Simulate + log only — never mutates the source
``data/hiring_tracker.json`` or any external system."""

from __future__ import annotations

from backend.schemas.approval_package import ApprovalPackage
from backend.schemas.execution import ExecutionResult


class ATSAdapter:
    name = "ats"

    def run(self, approval_package: ApprovalPackage) -> ExecutionResult:
        tu = approval_package.tracker_updates
        if tu is None:
            return ExecutionResult(adapter=self.name, ok=True,
                                   detail="No tracker update proposed.")
        changes = ", ".join(f"{k}={v}" for k, v in tu.changes.items())
        detail = f"Simulated ATS update for {tu.candidate_id}: {changes or tu.summary}"
        return ExecutionResult(adapter=self.name, ok=True, detail=detail)
