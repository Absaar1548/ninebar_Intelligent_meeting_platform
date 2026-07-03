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
    llm_status_line,
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


# -- LLM settings handlers (presentation only — forward + render) -----------
def _error_detail(exc: Exception) -> str:
    """Pull the backend's 422 message out of an httpx error, if present."""
    resp = getattr(exc, "response", None)
    if resp is not None:
        try:
            return resp.json().get("detail") or str(exc)
        except Exception:  # noqa: BLE001
            return str(exc)
    return str(exc)


def _group_visibility(provider: str):
    """Show only the field group for the selected provider (mock has none)."""
    return (
        gr.update(visible=provider == "mock"),
        gr.update(visible=provider == "ollama"),
        gr.update(visible=provider == "azure_openai"),
    )


def load_llm_config(api: HiringApiClient):
    """Prefill the LLM panel from the backend (non-secret fields + status)."""
    try:
        cfg = api.get_llm_config()
    except Exception as exc:  # noqa: BLE001 - backend down at page load
        return (
            f"_Could not load LLM status: {exc}_",
            "mock", "", "", "", "", "",
            *_group_visibility("mock"),
        )
    provider = cfg.get("provider", "mock")
    return (
        llm_status_line(cfg),
        provider,
        cfg.get("ollama_model", ""),
        cfg.get("ollama_host", ""),
        cfg.get("azure_endpoint", ""),
        cfg.get("azure_deployment", ""),
        cfg.get("azure_api_version", ""),
        *_group_visibility(provider),
    )


def apply_llm_config(
    api: HiringApiClient, provider, o_model, o_host, o_key,
    az_endpoint, az_deploy, az_version, az_key,
):
    """Forward the settings to the backend; clear key boxes on success.

    The single Provider control drives the mode: ``mock`` runs offline, while
    ``ollama`` / ``azure_openai`` switch to live cloud reasoning.
    """
    payload = {
        "provider": provider,
        "ollama_model": o_model,
        "ollama_host": o_host,
        "ollama_api_key": o_key,
        "azure_endpoint": az_endpoint,
        "azure_deployment": az_deploy,
        "azure_api_version": az_version,
        "azure_api_key": az_key,
    }
    try:
        cfg = api.set_llm_config(payload)
    except Exception as exc:  # noqa: BLE001 - surfaced to the UI
        return f"⚠️ {_error_detail(exc)}", gr.update(), gr.update()
    # Keys are write-only: never keep the secret in the box after applying.
    return f"✅ Applied — {llm_status_line(cfg)}", "", ""


def _toggle_provider(provider: str):
    return _group_visibility(provider)


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

                with gr.Accordion("⚙️ LLM Settings", open=False):
                    llm_status = gr.Markdown("_Loading LLM status…_")
                    provider = gr.Dropdown(
                        choices=[
                            ("Mock (deterministic, offline)", "mock"),
                            ("Ollama Cloud", "ollama"),
                            ("Azure OpenAI", "azure_openai"),
                        ],
                        value="mock", label="Provider",
                    )
                    mock_note = gr.Markdown(
                        "_Deterministic offline reasoner — no key or network needed._",
                        visible=True,
                    )
                    with gr.Group(visible=False) as ollama_group:
                        o_model = gr.Textbox(label="Ollama model", placeholder="glm-5.2")
                        o_host = gr.Textbox(
                            label="Ollama host", placeholder="https://ollama.com/v1"
                        )
                        o_key = gr.Textbox(
                            label="Ollama API key", type="password",
                            placeholder="leave blank to keep the current key",
                        )
                    with gr.Group(visible=False) as azure_group:
                        az_endpoint = gr.Textbox(
                            label="Azure endpoint",
                            placeholder="https://<resource>.openai.azure.com",
                        )
                        az_deploy = gr.Textbox(
                            label="Azure deployment", placeholder="deployment name"
                        )
                        az_version = gr.Textbox(
                            label="Azure API version", placeholder="2024-10-21"
                        )
                        az_key = gr.Textbox(
                            label="Azure API key", type="password",
                            placeholder="leave blank to keep the current key",
                        )
                    apply_llm_btn = gr.Button("Apply LLM settings", variant="secondary")

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

        def _do_load_llm():
            return load_llm_config(api)

        def _do_apply_llm(*vals):
            return apply_llm_config(api, *vals)

        start_btn.click(_do_start, inputs=[fixture], outputs=outputs)
        send_btn.click(_do_send, inputs=[session, msg], outputs=outputs).then(
            lambda: "", outputs=[msg]
        )
        msg.submit(_do_send, inputs=[session, msg], outputs=outputs).then(
            lambda: "", outputs=[msg]
        )
        approve_btn.click(_do_approve, inputs=[session], outputs=outputs)

        # LLM settings: toggle field groups, apply, and load current on open.
        provider.change(
            _toggle_provider,
            inputs=[provider],
            outputs=[mock_note, ollama_group, azure_group],
        )
        apply_llm_btn.click(
            _do_apply_llm,
            inputs=[
                provider, o_model, o_host, o_key,
                az_endpoint, az_deploy, az_version, az_key,
            ],
            outputs=[llm_status, o_key, az_key],
        )
        demo.load(
            _do_load_llm,
            inputs=None,
            outputs=[
                llm_status, provider, o_model, o_host,
                az_endpoint, az_deploy, az_version,
                mock_note, ollama_group, azure_group,
            ],
        )
    return demo
