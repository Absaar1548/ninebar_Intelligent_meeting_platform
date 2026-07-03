"""Mock Teams-notification adapter. Simulate + log only."""

from __future__ import annotations

from backend.schemas.approval_package import ApprovalPackage
from backend.schemas.execution import ExecutionResult


class TeamsAdapter:
    name = "teams"

    def run(self, approval_package: ApprovalPackage) -> ExecutionResult:
        rec = approval_package.recommendation.value.replace("_", " ")
        detail = (f"Simulated Teams notification for {approval_package.meeting_id}: "
                  f"recommendation '{rec}'.")
        return ExecutionResult(adapter=self.name, ok=True, detail=detail)
