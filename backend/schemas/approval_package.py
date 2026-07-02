"""Approval Package — the human-facing artifact and approval source of truth.

Derived from the Operations Package (`system_flow.md` §8.2). Stored as JSON and
rendered in the UI; Markdown is never authoritative. Regenerated (never
hand-edited) whenever a Modification re-flows through Approval Package
Generation. Field set matches §8.2.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas._time import utcnow
from backend.schemas.artifacts import (
    ActionItem,
    DraftEmail,
    EvidenceRef,
    TrackerUpdateProposal,
)
from backend.schemas.enums import ApprovalStatus, ExecutionStatus, Recommendation


class DecisionSummary(BaseModel):
    """Compact, human-facing decision record for the Approval Package."""

    model_config = ConfigDict(extra="ignore")

    recommendation: Recommendation
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)


class ApprovalPackage(BaseModel):
    """Human interaction contract (§8.2). ``approval_status`` starts ``pending``
    and ``execution_status`` starts ``not_started`` per §7.10."""

    model_config = ConfigDict(extra="ignore")

    meeting_id: str
    generated_at: datetime = Field(default_factory=utcnow)

    executive_summary: str
    recommendation: Recommendation
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    decision: DecisionSummary
    action_items: list[ActionItem] = Field(default_factory=list)
    draft_email: DraftEmail | None = None
    tracker_updates: TrackerUpdateProposal | None = None

    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    human_comments: list[str] = Field(default_factory=list)
    execution_status: ExecutionStatus = ExecutionStatus.NOT_STARTED
