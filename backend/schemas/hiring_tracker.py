"""Mock-ATS contract for ``data/hiring_tracker.json``.

The Hiring agent reads this file for context and proposes updates that are
applied on approval (later phases). Each candidate record extends the shared
``TrackerContext`` (per the file's own ``_note``). Only the contract and its
validation live in Phase 1; reading/mutating the file is a later phase.
"""

from __future__ import annotations

from datetime import date

from pydantic import Field

from backend.schemas.meeting_package import MeetingBaseModel, TrackerContext


class TrackerRole(MeetingBaseModel):
    title: str
    level: str
    company: str
    pipeline_stages: list[str] = Field(default_factory=list)


class TrackerHistoryEntry(MeetingBaseModel):
    stage: str
    outcome: str
    date: date


class TrackerRecord(TrackerContext):
    """A candidate row in the mock ATS: the shared core plus ATS-only fields."""

    name: str
    role_applied: str
    history: list[TrackerHistoryEntry] = Field(default_factory=list)


class HiringTracker(MeetingBaseModel):
    """Top-level mock-ATS file contract (``role`` + ``candidates[]``)."""

    role: TrackerRole
    candidates: list[TrackerRecord] = Field(default_factory=list)

    def find(self, candidate_id: str) -> TrackerRecord | None:
        """Return the record for ``candidate_id`` if present."""
        return next(
            (c for c in self.candidates if c.candidate_id == candidate_id), None
        )
