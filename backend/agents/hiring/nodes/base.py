"""Shared node plumbing.

Nodes are plain ``(state) -> dict`` functions returning partial state updates.
They obtain the LLM client through ``get_llm_client`` so a test or the dev
runner can inject a ``fallback``-mode client (``set_llm_client``) to run the
whole pipeline offline. ``with_message`` appends to the session chat record
(plain list overwrite semantics — we extend the current list explicitly).
"""

from __future__ import annotations

from backend.core.llm.client import LLMClient
from backend.schemas.workflow_state import Message, WorkflowState

_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


def set_llm_client(client: LLMClient | None) -> None:
    """Override (or reset with ``None``) the shared client — used by tests and
    the dev runner to force ``LLM_MODE=fallback``."""
    global _client
    _client = client


def with_message(state: WorkflowState, updates: dict, content: str) -> dict:
    msgs = list(state.get("messages", []))
    msgs.append(Message(role="agent", content=content))
    updates["messages"] = msgs
    return updates
