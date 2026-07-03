"""Frontend UI handlers exercised against the real app via an injected
TestClient (no live server, no network). Handlers are generators (they stream
live progress), so we consume to the final yield. The recommendation goes to the
chat; the reasoning goes to the internal panel."""

from __future__ import annotations

import gradio as gr
from fastapi.testclient import TestClient

from backend.api.main import create_app
from frontend.api_client import HiringApiClient
from frontend.pages.chat import FIXTURES, build_blocks, on_send, on_start

STRONG = list(FIXTURES)[0]
BORDERLINE = list(FIXTURES)[1]


def _api() -> HiringApiClient:
    return HiringApiClient(client=TestClient(create_app(enable_watcher=False)))


def _final(gen):
    """Exhaust a handler generator and return its last yielded tuple."""
    last = None
    for last in gen:
        pass
    return last


def _chat_text(chat) -> str:
    return "\n".join(m["content"] for m in chat)


def test_recommendation_is_in_chat_reasoning_in_panel():
    sid, chat, internal, status = _final(on_start(_api(), STRONG))
    assert sid.startswith("sess-")
    text = _chat_text(chat)
    assert "MOVE FORWARD" in text            # recommendation lives in chat
    assert "Evidence cited" in text
    assert "waiting for your decision" in status
    # the per-node reasoning trace + artifacts live in the internal panel
    assert "Processing trace" in internal
    assert "Evidence graph" in internal
    assert "Findings" in internal
    assert "Evidence cited" not in internal  # recommendation not dumped here


def test_approve_posts_execution_to_chat():
    api = _api()
    sid, *_ = _final(on_start(api, STRONG))
    _, chat, _, status = _final(on_send(api, sid, "approve"))
    assert "completed" in status
    assert "Mock execution" in _chat_text(chat)


def test_modify_returns_to_waiting():
    api = _api()
    sid, *_ = _final(on_start(api, STRONG))
    _, _, _, status = _final(on_send(api, sid, "rewrite the email"))
    assert "waiting for your decision" in status


def test_borderline_is_hold_in_chat():
    _, chat, _, _ = _final(on_start(_api(), BORDERLINE))
    assert "HOLD" in _chat_text(chat)


def test_send_without_session_is_safe():
    _, _chat, internal, _status = _final(on_send(_api(), "", "approve"))
    assert "Start a session" in internal


def test_build_blocks_constructs():
    assert isinstance(build_blocks(_api()), gr.Blocks)
