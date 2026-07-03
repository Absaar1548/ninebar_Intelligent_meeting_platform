"""HTTP client for the Hiring backend.

Thin wrapper over a sync ``httpx.Client``-compatible object so the UI never
touches workflow internals. Tests inject a Starlette ``TestClient`` (same
``.get``/``.post`` interface) to exercise the UI against the real app with no
live server.
"""

from __future__ import annotations

from typing import Any

import httpx

from backend.core.common.config import get_settings

BASE = "/api/v1/agents/hiring"


class HiringApiClient:
    def __init__(self, client: Any | None = None, base_url: str | None = None) -> None:
        self._client = client or httpx.Client(
            base_url=base_url or get_settings().backend_base_url, timeout=300.0
        )

    def health(self) -> dict:
        return self._client.get("/health").json()

    def start(self, meeting_package: dict) -> dict:
        r = self._client.post(f"{BASE}/sessions", json={"meeting_package": meeting_package})
        r.raise_for_status()
        return r.json()

    def send(self, session_id: str, message: str) -> dict:
        r = self._client.post(
            f"{BASE}/sessions/{session_id}/messages", json={"message": message}
        )
        r.raise_for_status()
        return r.json()

    def get(self, session_id: str) -> dict:
        r = self._client.get(f"{BASE}/sessions/{session_id}")
        r.raise_for_status()
        return r.json()

    def list(self) -> list[dict]:
        return self._client.get(f"{BASE}/sessions").json()

    # -- LLM configuration (platform-level, not under the hiring prefix) --
    def get_llm_config(self) -> dict:
        r = self._client.get("/api/v1/llm/config")
        r.raise_for_status()
        return r.json()

    def set_llm_config(self, payload: dict) -> dict:
        """Apply an LLM config change; raises httpx.HTTPStatusError with the
        backend's 422 detail if the requested cloud config is incomplete."""
        r = self._client.put("/api/v1/llm/config", json=payload)
        r.raise_for_status()
        return r.json()
