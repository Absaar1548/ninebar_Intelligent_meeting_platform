"""Hiring domain models.

Per the Phase 1 decision, the artifact **contracts** live in ``backend.schemas``
(the leaf layer). This module re-exports them so hiring code imports its models
from the domain package, and it is the home the ``data/hiring_tracker.json`` note
refers to (records align with ``TrackerContext``). Additive domain helpers may be
added here, but the contracts themselves are not redefined.
"""

from __future__ import annotations

from backend.schemas.artifacts import (
    ActionItem,
    ActionPlan,
    Assessment,
    Decision,
    DraftEmail,
    Drafts,
    EvidenceGraph,
    EvidenceNode,
    EvidenceRef,
    EvidenceRelationship,
    Finding,
    Findings,
    InterviewContext,
    TrackerUpdateProposal,
)
from backend.schemas.enums import (
    ActionType,
    EvidenceSourceType,
    Recommendation,
)
from backend.schemas.meeting_package import MeetingPackage, TrackerContext

__all__ = [
    "InterviewContext",
    "EvidenceGraph",
    "EvidenceNode",
    "EvidenceRelationship",
    "EvidenceRef",
    "Finding",
    "Findings",
    "Assessment",
    "Decision",
    "ActionItem",
    "ActionPlan",
    "DraftEmail",
    "Drafts",
    "TrackerUpdateProposal",
    "TrackerContext",
    "MeetingPackage",
    "Recommendation",
    "ActionType",
    "EvidenceSourceType",
]
