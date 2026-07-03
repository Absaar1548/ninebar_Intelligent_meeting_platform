"""Hiring Operations Agent router.

Thin HTTP adapter over ``HiringSessionService`` — no business logic here
(§4). Creates/resumes/reads workflow sessions.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from backend.agents.hiring.session import HiringSessionService
from backend.api.dependencies import get_session_service
from backend.api.models import MessageRequest, SessionView, StartSessionRequest
from backend.schemas.meeting_package import MeetingPackage

router = APIRouter(prefix="/api/v1/agents/hiring", tags=["hiring"])


@router.post("/sessions", response_model=SessionView)
def start_session(
    body: StartSessionRequest,
    service: HiringSessionService = Depends(get_session_service),
) -> SessionView:
    try:
        mp = MeetingPackage.model_validate(body.meeting_package)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422, detail=f"invalid Meeting Package ({exc.error_count()} errors)"
        ) from exc
    return SessionView.from_result(service.start_from_package(mp))


@router.post("/sessions/{session_id}/messages", response_model=SessionView)
def send_message(
    session_id: str,
    body: MessageRequest,
    service: HiringSessionService = Depends(get_session_service),
) -> SessionView:
    try:
        result = service.resume(session_id, body.message)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session not found") from exc
    return SessionView.from_result(result)


@router.get("/sessions/{session_id}", response_model=SessionView)
def get_session(
    session_id: str,
    service: HiringSessionService = Depends(get_session_service),
) -> SessionView:
    result = service.get(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="session not found")
    return SessionView.from_result(result)


@router.get("/sessions")
def list_sessions(
    service: HiringSessionService = Depends(get_session_service),
) -> list[dict]:
    return [info.model_dump(mode="json") for info in service.list()]
