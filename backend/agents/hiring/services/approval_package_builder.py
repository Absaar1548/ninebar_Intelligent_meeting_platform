"""Derive the human-facing Approval Package from the Operations Package (§7.10).

The Approval Package is the approval source of truth: it starts ``pending`` /
``not_started`` and surfaces exactly the §8.2 fields. It is regenerated (never
hand-edited) whenever a Modification re-flows through here. The executive
summary is an **evidence-based narrative** — it names the key strengths, gaps,
and risks with their citations rather than bare counts.
"""

from __future__ import annotations

from backend.schemas.approval_package import ApprovalPackage, DecisionSummary
from backend.schemas.artifacts import Finding
from backend.schemas.operations_package import OperationsPackage


def _cite(finding: Finding) -> str:
    ids = ", ".join(r.evidence_id for r in finding.evidence_refs[:3])
    return f" ({ids})" if ids else ""


def _clause(label: str, findings: list[Finding], limit: int = 2) -> str:
    picked = findings[:limit]
    if not picked:
        return ""
    body = "; ".join(f"{f.statement.rstrip('.')}{_cite(f)}" for f in picked)
    return f"**{label}:** {body}."


def build_executive_summary(ops: OperationsPackage) -> str:
    d = ops.decision
    a = ops.assessment
    ctx = ops.context_analysis
    f = ops.findings
    rec = d.recommendation.value.replace("_", " ").upper()

    head = (
        f"**{ctx.candidate_name}** — assessed as *{a.suitability.lower()}* for "
        f"{ctx.role_title} ({ctx.role_level}). Recommendation: **{rec}** at "
        f"{d.confidence * 100:.0f}% confidence."
    )
    clauses = [
        _clause("Strengths", f.strengths),
        _clause("Gaps", f.weaknesses + f.missing_information),
        _clause("Risks", f.risks, limit=1),
    ]
    return " ".join([head, *[c for c in clauses if c]])


def build_approval_package(ops: OperationsPackage) -> ApprovalPackage:
    d = ops.decision
    return ApprovalPackage(
        meeting_id=ops.meeting_id,
        executive_summary=build_executive_summary(ops),
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
