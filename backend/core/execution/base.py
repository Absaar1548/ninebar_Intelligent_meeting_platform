"""Mock execution adapter contract.

Each adapter simulates one downstream enterprise integration and returns an
``ExecutionResult``. Production swaps the adapter body for a real API call with
no change to the engine or the failure-handling topology (`system_flow.md` §17).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.schemas.approval_package import ApprovalPackage
from backend.schemas.execution import ExecutionResult


@runtime_checkable
class ExecutionAdapter(Protocol):
    name: str

    def run(self, approval_package: ApprovalPackage) -> ExecutionResult:
        """Simulate the downstream action; return its result."""
        ...
