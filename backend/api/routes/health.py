"""Health endpoint."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "hiring-operations-agent",
        "version": "0.4.0",
    }
