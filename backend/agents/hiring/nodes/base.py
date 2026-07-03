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


def with_message(
    state: WorkflowState, updates: dict, content: str, *, kind: str = "internal"
) -> dict:
    """Append an agent message to the session record (default: internal trace)."""
    msgs = list(state.get("messages", []))
    msgs.append(Message(role="agent", content=content, kind=kind))
    updates["messages"] = msgs
    return updates


def with_chat_message(state: WorkflowState, updates: dict, content: str) -> dict:
    """Append a human-facing (chat) agent message."""
    return with_message(state, updates, content, kind="chat")


def revision_for(state: WorkflowState, node_name: str) -> str | None:
    """The human's modification instruction, if THIS node is the resume target
    of the active Modification.

    Returns ``None`` on the initial pipeline pass and for non-target nodes, so a
    downstream node regenerates from the updated upstream artifacts rather than
    re-applying the raw request. This is what makes "rewrite the email to say X"
    actually change the email at Draft Generation.
    """
    if state.get("modification_target") == node_name:
        feedback = (state.get("human_feedback") or "").strip()
        return feedback or None
    return None
