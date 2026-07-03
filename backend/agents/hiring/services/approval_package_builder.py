"""Derive the human-facing Approval Package from the Operations Package (§7.10).

The Approval Package is the approval source of truth: it starts ``pending`` /
``not_started`` and surfaces exactly the §8.2 fields. It is regenerated (never
hand-edited) whenever a Modification re-flows through here in Phase 3.
"""

from __future__ import annotations

from backend.schemas.approval_package import ApprovalPackage, DecisionSummary
from backend.schemas.operations_package import OperationsPackage


def build_approval_package(ops: OperationsPackage) -> ApprovalPackage:
    d = ops.decision
    a = ops.assessment
    ctx = ops.context_analysis
    rec_label = d.recommendation.value.replace("_", " ")

    summary = (
        f"{ctx.candidate_name} — {rec_label.upper()} for {ctx.role_title} "
        f"({ctx.role_level}). Confidence {d.confidence:.2f}. {a.suitability}: "
        f"{len(ops.findings.strengths)} strength(s), "
        f"{len(ops.findings.weaknesses)} gap(s), "
        f"{len(ops.findings.risks)} risk(s)."
    )

    return ApprovalPackage(
        meeting_id=ops.meeting_id,
        executive_summary=summary,
        recommendation=d.recommendation,
        confidence=d.confidence,
        evidence=list(d.evidence_refs),
        decision=DecisionSummary(
            recommendation=d.recommendation,
            reasoning=d.reasoning,
            confidence=d.confidence,
        ),
        action_items=list(ops.action_plan.items),
        draft_email=ops.drafts.draft_email,
        tracker_updates=ops.drafts.tracker_update_proposal,
    )
