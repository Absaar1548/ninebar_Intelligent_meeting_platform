"""Identifier and timestamp helpers."""

from __future__ import annotations

import uuid

from backend.schemas._time import utcnow

__all__ = ["utcnow", "utcnow_iso", "new_session_id", "session_id_for"]


def utcnow_iso() -> str:
    """Current UTC time as an ISO-8601 string."""
    return utcnow().isoformat()


def new_session_id() -> str:
    """Generate a fresh opaque session id."""
    return uuid.uuid4().hex


def session_id_for(meeting_id: str) -> str:
    """Derive a stable, readable session id from a meeting id.

    Each Meeting Package owns exactly one workflow session; deriving the id from
    ``meeting_id`` keeps sessions per-interview and reproducible.
    """
    return f"sess-{meeting_id}"
