"""Assemble the internal Operations Package from upstream artifacts (§7.9).

Deterministic assembly only — no reasoning. A missing artifact means an upstream
node did not complete and is surfaced as an error rather than silently skipped.
"""

from __future__ import annotations

from backend.schemas.artifacts import (
    ActionPlan,
    Assessment,
    Decision,
    Drafts,
    EvidenceGraph,
    Findings,
    InterviewContext,
)
from backend.schemas.operations_package import OperationsPackage


def build_operations_package(
    *,
    meeting_id: str,
    interview_context: InterviewContext,
    evidence_graph: EvidenceGraph,
    findings: Findings,
    assessment: Assessment,
    decision: Decision,
    action_plan: ActionPlan,
    drafts: Drafts,
) -> OperationsPackage:
    return OperationsPackage(
        meeting_id=meeting_id,
        context_analysis=interview_context,
        evidence_graph=evidence_graph,
        findings=findings,
        assessment=assessment,
        decision=decision,
        action_plan=action_plan,
        drafts=drafts,
    )
