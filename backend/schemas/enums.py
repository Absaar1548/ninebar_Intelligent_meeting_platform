"""Enumerations shared across the data contracts.

String values are the on-the-wire representation and MUST match the workflow
specification. ``WorkflowStage`` values in particular are the ``workflow_stage``
labels in ``docs/system_flow.md`` Appendix B and must not be renamed.
"""

from __future__ import annotations

from enum import StrEnum


class WorkflowStage(StrEnum):
    """State-machine position (`workflow_stage`). Labels are authoritative.

    Ordered from session creation through the linear reasoning pipeline to the
    terminal states. See ``system_flow.md`` §7 (per-node) and Appendix B.
    """

    CREATED = "created"
    VALIDATED = "validated"
    CONTEXT_ANALYZED = "context_analyzed"
    EVIDENCE_CONSTRUCTED = "evidence_constructed"
    ISSUES_IDENTIFIED = "issues_identified"
    ASSESSED = "assessed"
    DECISION_SYNTHESIZED = "decision_synthesized"
    ACTIONS_PLANNED = "actions_planned"
    DRAFTS_GENERATED = "drafts_generated"
    OPERATIONS_PACKAGE_GENERATED = "operations_package_generated"
    WAITING_APPROVAL = "waiting_approval"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Intent(StrEnum):
    """Supported user intents (`system_flow.md` §7.12, §10)."""

    APPROVAL = "approval"
    MODIFICATION = "modification"
    UNSUPPORTED = "unsupported"


class Recommendation(StrEnum):
    """Hiring recommendation values (`system_flow.md` §7.6, non-exhaustive)."""

    MOVE_FORWARD = "move_forward"
    REJECT = "reject"
    HOLD = "hold"
    ADDITIONAL_INTERVIEW = "additional_interview"


class ApprovalStatus(StrEnum):
    """Approval Package approval lifecycle (`system_flow.md` §8.2)."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExecutionStatus(StrEnum):
    """Mock execution progress (`system_flow.md` §8.2, §7.16)."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class EvidenceSourceType(StrEnum):
    """Evidence sources linked by the Evidence Graph (`system_flow.md` §7.3)."""

    TRANSCRIPT = "transcript"
    RESUME = "resume"
    TRACKER = "tracker"
    INTERVIEW_NOTES = "interview_notes"
    JOB_DESCRIPTION = "job_description"
    RUBRIC = "rubric"


class ActionType(StrEnum):
    """Operational task types produced by Action Planning (`system_flow.md` §7.7)."""

    TRACKER_UPDATE = "tracker_update"
    CANDIDATE_EMAIL = "candidate_email"
    NOTIFY_HIRING_MANAGER = "notify_hiring_manager"
    SCHEDULE_INTERVIEW = "schedule_interview"


class EventType(StrEnum):
    """Runtime events emitted across a run (`system_flow.md` §15.1)."""

    MEETING_PACKAGE_CREATED = "meeting_package_created"
    WORKFLOW_STARTED = "workflow_started"
    OPERATIONS_PACKAGE_GENERATED = "operations_package_generated"
    APPROVAL_PACKAGE_GENERATED = "approval_package_generated"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    HUMAN_MESSAGE_RECEIVED = "human_message_received"
    WORKFLOW_RESUMED = "workflow_resumed"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
