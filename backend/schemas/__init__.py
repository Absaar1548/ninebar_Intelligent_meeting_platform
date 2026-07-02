"""Schema-first data contracts for the Hiring Operations Agent.

This package is the leaf layer: it has no dependency on ``core`` or ``agents``.
The three governing contracts are the Meeting Package (input), the Operations
Package (internal), and the Approval Package (human-facing); ``WorkflowState``
ties them together for LangGraph. Convenience re-exports below.
"""

from backend.schemas.approval_package import ApprovalPackage, DecisionSummary
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
    ApprovalStatus,
    EventType,
    EvidenceSourceType,
    ExecutionStatus,
    Intent,
    Recommendation,
    WorkflowStage,
)
from backend.schemas.events import WorkflowEvent
from backend.schemas.hiring_tracker import (
    HiringTracker,
    TrackerHistoryEntry,
    TrackerRecord,
    TrackerRole,
)
from backend.schemas.meeting_package import (
    CandidateProfile,
    MeetingMetadata,
    MeetingPackage,
    Participant,
    Payload,
    RoleContext,
    TrackerContext,
    TranscriptTurn,
)
from backend.schemas.operations_package import OperationsPackage
from backend.schemas.workflow_state import (
    Message,
    SessionMetadata,
    WorkflowState,
)

__all__ = [
    # meeting package (input)
    "MeetingPackage",
    "MeetingMetadata",
    "Participant",
    "TranscriptTurn",
    "CandidateProfile",
    "RoleContext",
    "TrackerContext",
    "Payload",
    # hiring tracker (mock ATS)
    "HiringTracker",
    "TrackerRole",
    "TrackerRecord",
    "TrackerHistoryEntry",
    # artifacts
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
    "TrackerUpdateProposal",
    "Drafts",
    # packages
    "OperationsPackage",
    "ApprovalPackage",
    "DecisionSummary",
    # state & events
    "WorkflowState",
    "Message",
    "SessionMetadata",
    "WorkflowEvent",
    # enums
    "WorkflowStage",
    "Intent",
    "Recommendation",
    "ApprovalStatus",
    "ExecutionStatus",
    "EvidenceSourceType",
    "ActionType",
    "EventType",
]
