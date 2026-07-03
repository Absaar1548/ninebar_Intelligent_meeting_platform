"""Hiring reasoning artifacts — the strongly-typed outputs of each node.

Defined in the ``schemas`` (leaf) layer so the Operations Package, Approval
Package, and Workflow State can be fully typed and validated in Phase 1. Phase 2
``agents/hiring/models.py`` re-exports these and adds node logic; Phase 2 may
make **additive** refinements only. Field sets come from ``system_flow.md``
§7.2–7.8. Evidence-first: findings/decisions/actions carry ``evidence_refs``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.enums import (
    ActionType,
    EvidenceSourceType,
    Intent,
    Recommendation,
)


class ArtifactBaseModel(BaseModel):
    """Base for internal artifacts. ``extra="ignore"`` tolerates stray keys from
    LLM structured output without failing validation."""

    model_config = ConfigDict(extra="ignore")


# --------------------------------------------------------------------------
# Context Analysis (§7.2)
# --------------------------------------------------------------------------
class InterviewContext(ArtifactBaseModel):
    interview_stage: str
    candidate_name: str
    candidate_title: str | None = None
    role_title: str
    role_level: str
    meeting_objective: str
    historical_context: str | None = None
    tracker_state: str | None = None
    focus_areas: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Evidence Graph Construction (§7.3)
# --------------------------------------------------------------------------
class EvidenceNode(ArtifactBaseModel):
    id: str
    source_type: EvidenceSourceType
    locator: str  # e.g. transcript turn index, "payload.candidate.skills"
    content: str  # the quoted / summarized evidence snippet


class EvidenceRelationship(ArtifactBaseModel):
    from_id: str
    to_id: str
    relation: str  # e.g. "supports", "contradicts", "elaborates"


class EvidenceGraph(ArtifactBaseModel):
    nodes: list[EvidenceNode] = Field(default_factory=list)
    relationships: list[EvidenceRelationship] = Field(default_factory=list)
    missing_sources: list[EvidenceSourceType] = Field(default_factory=list)

    def has_node(self, evidence_id: str) -> bool:
        return any(n.id == evidence_id for n in self.nodes)


class EvidenceRef(ArtifactBaseModel):
    """A grounding pointer from a finding/decision/action to an EvidenceNode."""

    evidence_id: str
    quote: str | None = None


# --------------------------------------------------------------------------
# Issue Identification (§7.4)
# --------------------------------------------------------------------------
class Finding(ArtifactBaseModel):
    statement: str
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


class Findings(ArtifactBaseModel):
    strengths: list[Finding] = Field(default_factory=list)
    weaknesses: list[Finding] = Field(default_factory=list)
    risks: list[Finding] = Field(default_factory=list)
    contradictions: list[Finding] = Field(default_factory=list)
    missing_information: list[Finding] = Field(default_factory=list)
    open_questions: list[Finding] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Operational Assessment (§7.5)
# --------------------------------------------------------------------------
class Assessment(ArtifactBaseModel):
    suitability: str
    confidence: float = Field(ge=0.0, le=1.0)
    risk: str
    escalation: bool = False
    blockers: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Decision Synthesis (§7.6)
# --------------------------------------------------------------------------
class Decision(ArtifactBaseModel):
    recommendation: Recommendation
    alternatives: list[Recommendation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Action Planning (§7.7)
# --------------------------------------------------------------------------
class ActionItem(ArtifactBaseModel):
    type: ActionType
    description: str
    target: str | None = None
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)


class ActionPlan(ArtifactBaseModel):
    items: list[ActionItem] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Draft Generation (§7.8)
# --------------------------------------------------------------------------
class DraftEmail(ArtifactBaseModel):
    to: str
    subject: str
    body: str


class TrackerUpdateProposal(ArtifactBaseModel):
    candidate_id: str
    summary: str | None = None
    changes: dict[str, str] = Field(default_factory=dict)


class Drafts(ArtifactBaseModel):
    draft_email: DraftEmail | None = None
    tracker_update_proposal: TrackerUpdateProposal | None = None


# --------------------------------------------------------------------------
# Intent Classification (§7.12) — the sole gateway between human and workflow
# --------------------------------------------------------------------------
class IntentClassification(ArtifactBaseModel):
    intent: Intent
    modification_target: str | None = None  # resume node for a Modification
    rationale: str = ""
