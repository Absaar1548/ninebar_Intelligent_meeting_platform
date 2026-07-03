"""Mock candidate-email adapter. Simulate + log only."""

from __future__ import annotations

from backend.schemas.approval_package import ApprovalPackage
from backend.schemas.execution import ExecutionResult


class EmailAdapter:
    name = "email"

    def run(self, approval_package: ApprovalPackage) -> ExecutionResult:
        email = approval_package.draft_email
        if email is None:
            return ExecutionResult(adapter=self.name, ok=True,
                                   detail="No candidate email to send.")
        detail = f"Simulated email to {email.to}: subject '{email.subject}'"
        return ExecutionResult(adapter=self.name, ok=True, detail=detail)
