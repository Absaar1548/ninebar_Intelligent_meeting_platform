"""Meeting Package — the input data contract (Layer 1 → Layer 2).

Produced by the (mocked) Meeting Intelligence Platform and consumed by the
Hiring Operations Agent. Immutable for the remainder of a session once
validated (`system_flow.md` §7.1). This module mirrors the fixtures under
``data/fixtures/meeting_packages/`` exactly.

``TrackerContext`` is the shared tracker core; the mock-ATS contract in
``hiring_tracker.py`` extends it (one-directional import, keeping ``schemas``
a clean leaf layer).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MeetingBaseModel(BaseModel):
    """Base for input-contract models.

    ``extra="allow"`` keeps forward-compatibility with additional fields a
    future Layer 1 may attach, without weakening required-field validation.
    """

    model_config = ConfigDict(extra="allow")


class MeetingMetadata(MeetingBaseModel):
    meeting_id: str
    title: str
    meeting_type: str
    started_at: datetime
    duration_minutes: int
    platform: str


class Participant(MeetingBaseModel):
    name: str
    role: str
    title: str | None = None


class TranscriptTurn(MeetingBaseModel):
    turn_index: int
    speaker: str
    timestamp: str
    text: str


class CandidateProfile(MeetingBaseModel):
    name: str
    current_title: str
    current_company: str
    years_experience: int
    location: str | None = None
    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    links: dict[str, str] = Field(default_factory=dict)


class RoleContext(MeetingBaseModel):
    title: str
    level: str
    company: str
    must_have_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    jd_highlights: list[str] = Field(default_factory=list)


class TrackerContext(MeetingBaseModel):
    """Shared tracker core (the Meeting Package's ``payload.tracker`` block).

    Extended by ``hiring_tracker.TrackerRecord`` for the mock-ATS file.
    Records align with this model per the note in ``data/hiring_tracker.json``.
    """

    candidate_id: str
    current_stage: str
    status: str
    interview_round: int
    notes: str | None = None


class InterviewInfo(MeetingBaseModel):
    """The Meeting Package ``payload.interview`` block.

    Named ``InterviewInfo`` (not ``InterviewContext``) to avoid clashing with
    the richer ``InterviewContext`` artifact produced by Context Analysis
    (see ``schemas/artifacts.py``).
    """

    round_name: str
    round_number: int
    total_rounds: int
    focus_areas: list[str] = Field(default_factory=list)
    next_stage: str | None = None


class Payload(MeetingBaseModel):
    candidate: CandidateProfile
    role: RoleContext
    tracker: TrackerContext
    interview: InterviewInfo


class MeetingPackage(MeetingBaseModel):
    """Top-level input contract validated by the Context Validation node."""

    schema_version: str
    domain: str
    metadata: MeetingMetadata
    participants: list[Participant] = Field(default_factory=list)
    transcript: list[TranscriptTurn] = Field(default_factory=list)
    payload: Payload

    @property
    def meeting_id(self) -> str:
        return self.metadata.meeting_id
