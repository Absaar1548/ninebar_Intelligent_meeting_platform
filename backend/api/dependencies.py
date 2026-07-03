"""FastAPI dependency providers."""

from __future__ import annotations

from fastapi import Request

from backend.agents.hiring.session import HiringSessionService
from backend.core.common.config import Settings
from backend.core.common.config import get_settings as _get_settings


def get_settings() -> Settings:
    return _get_settings()


def get_session_service(request: Request) -> HiringSessionService:
    """The per-app singleton session service (created in ``create_app``)."""
    return request.app.state.session_service
