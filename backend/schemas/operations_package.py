"""Operations Package — the internal reasoning artifact (`system_flow.md` §8.1).

Assembled by Operations Package Generation from all upstream artifacts. Not
user-editable and never surfaced for human editing. The Approval Package is
derived from it.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.artifacts import (
    ActionPlan,
    Assessment,
    Decision,
    Drafts,
    EvidenceGraph,
    Findings,
    InterviewContext,
)
from backend.schemas._time import utcnow


class OperationsPackage(BaseModel):
    """Internal contract. One field per producing node (§8.1)."""

    model_config = ConfigDict(extra="ignore")

    meeting_id: str
    generated_at: datetime = Field(default_factory=utcnow)

    context_analysis: InterviewContext
    evidence_graph: EvidenceGraph
    findings: Findings
    assessment: Assessment
    decision: Decision
    action_plan: ActionPlan
    drafts: Drafts
