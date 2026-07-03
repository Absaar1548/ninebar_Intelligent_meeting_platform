"""Stub routers for the not-yet-implemented domain agents.

Their presence proves the platform is pluggable: a future agent registers its
own router under ``/api/v1/agents/<name>`` with no change to the gateway.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException


def make_stub_router(agent: str) -> APIRouter:
    router = APIRouter(prefix=f"/api/v1/agents/{agent}", tags=[agent])

    @router.post("/sessions")
    def _not_implemented() -> None:
        raise HTTPException(
            status_code=501,
            detail=f"The {agent} Operations Agent is not implemented in this MVP.",
        )

    return router
