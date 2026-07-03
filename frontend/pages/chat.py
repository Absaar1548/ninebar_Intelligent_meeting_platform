"""The Teams-like chat page.

Event handlers (``on_start`` / ``on_send``) are pure generator functions over an
injected ``HiringApiClient``. They run the (blocking) backend call in a thread
and poll ``GET /sessions/{id}`` for live per-node progress — so a slow cloud run
shows a stage-by-stage tracker instead of a frozen spinner. No business logic
here: every action is an HTTP call.
"""

from __future__ import annotations

import threading
import time

import gradio as gr

from backend.core.common.config import REPO_ROOT
from backend.core.common.json_io import read_json
from frontend.api_client import HiringApiClient
from frontend.components.renderers import (
    chat_history,
    internal_panel,
    is_settled,
    progress_panel,
    status_line,
)

_FIXTURES_DIR = REPO_ROOT / "data" / "fixtures" / "meeting_packages"
FIXTURES = {
    "Strong candidate — Absaar Ali": "meeting_package_strong.json",
    "Borderline candidate — Meera Krishnan": "meeting_package_borderline.json",
}

_INTRO = (
    "_Start a session — the agent presents its recommendation in chat. Reply "
    "**approve** · **rewrite the email** · **change the recommendation** · "
    "(anything off-topic is politely declined). The right panel shows the "
    "internal reasoning (and live progress while it runs)._"
)
_INTERNAL_PLACEHOLDER = "_Start a session to see the agent's internal reasoning._"
_POLL_SECONDS = 1.2


def _call(holder: dict, fn, *args) -> None:
    try:
        holder["result"] = fn(*args)
    except Exception as exc:  # noqa: BLE001 - surfaced to the UI
        holder["error"] = exc


def _safe_get(api: HiringApiClient, session_id: str) -> dict | None:
    try:
        return api.get(session_id)
    except Exception:  # noqa: BLE001 - 404 during startup / transient
        return None


def _run_with_progress(api, session_id, base_chat, call_fn, *call_args):
    """Drive a blocking backend call in a thread while yielding live progress."""
    holder: dict = {}
    thread = threading.Thread(target=_call, args=(holder, call_fn, *call_args), daemon=True)
    thread.start()
    yield session_id, base_chat, "### ⏳ Working…", "**Stage:** `starting` — ⏳ working…"
    while thread.is_alive():
        # Sleep first: a fast (fallback) run finishes here and we never poll it,
        # which keeps things simple and avoids racing the in-flight request.
        time.sleep(_POLL_SECONDS)
        if not thread.is_alive():
            break
        view = _safe_get(api, session_id)
        if view is not None and not is_settled(view):
            yield session_id, base_chat, progress_panel(view), status_line(view)
    thread.join()
    if "error" in holder:
        yield session_id, base_chat, f"**Error:** `{holder['error']}`", "**Stage:** `failed` — error"
        return
    view = holder["result"]
    yield view["session_id"], chat_history(view), internal_panel(view), status_line(view)


# -- pure handlers (generators) --------------------------------------------
def on_start(api: HiringApiClient, fixture_label: str):
    mp = read_json(_FIXTURES_DIR / FIXTURES[fixture_label])
    # Mirrors backend session_id_for(meeting_id) so we can poll during the run.
    session_id = f"sess-{mp['metadata']['meeting_id']}"
    yield from _run_with_progress(api, session_id, [], api.start, mp)


def on_send(api: HiringApiClient, session_id: str, message: str):
    if not session_id:
        yield "", [], _INTERNAL_PLACEHOLDER, "**No active session.**"
        return
    if not (message or "").strip():
        view = api.get(session_id)
        yield session_id, chat_history(view), internal_panel(view), status_line(view)
        return
    current = _safe_get(api, session_id)
    base_chat = (chat_history(current) if current else []) + [
        {"role": "user", "content": message}
    ]
    yield from _run_with_progress(api, session_id, base_chat, api.send, session_id, message)


# -- layout -----------------------------------------------------------------
def build_blocks(api: HiringApiClient) -> gr.Blocks:
    with gr.Blocks(
        title="Hiring Operations Agent", theme=gr.themes.Soft(), analytics_enabled=False
    ) as demo:
        gr.Markdown("# Hiring Operations Agent — Teams Simulation")
        gr.Markdown(_INTRO)
        session = gr.State("")

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(type="messages", height=520, label="Conversation")
                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="Reply to the agent…", scale=5, show_label=False,
                        autofocus=True,
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)
                approve_btn = gr.Button("✅ Approve & execute", variant="secondary")
            with gr.Column(scale=2):
                fixture = gr.Dropdown(
                    choices=list(FIXTURES), value=list(FIXTURES)[0], label="Meeting Package"
                )
                start_btn = gr.Button("▶ Start session", variant="primary")
                status = gr.Markdown("_No active session._")
                gr.Markdown("### 🧠 Internal Processing & Memory")
                internal = gr.Markdown(_INTERNAL_PLACEHOLDER)

        outputs = [session, chatbot, internal, status]

        # Generator wrappers close over ``api`` and keep generator semantics so
        # Gradio streams the intermediate progress yields.
        def _do_start(fixture_label):
            yield from on_start(api, fixture_label)

        def _do_send(sid, message):
            yield from on_send(api, sid, message)

        def _do_approve(sid):
            yield from on_send(api, sid, "approve")

        start_btn.click(_do_start, inputs=[fixture], outputs=outputs)
        send_btn.click(_do_send, inputs=[session, msg], outputs=outputs).then(
            lambda: "", outputs=[msg]
        )
        msg.submit(_do_send, inputs=[session, msg], outputs=outputs).then(
            lambda: "", outputs=[msg]
        )
        approve_btn.click(_do_approve, inputs=[session], outputs=outputs)
    return demo
