"""Timezone-aware timestamp helper shared by the schema layer.

Kept inside ``schemas`` so the data contracts stay a self-contained leaf layer
(no dependency on ``core``).
"""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current time as a timezone-aware UTC ``datetime``."""
    return datetime.now(timezone.utc)
