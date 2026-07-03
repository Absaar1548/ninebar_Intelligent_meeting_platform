"""Bridge API `SessionView` JSON → Gradio-ready views.

The **chat** shows only human-facing (`kind=="chat"`) messages — the agent's
recommendation and its replies. The **Internal Processing & Memory** panel is
rendered from the Operations Package + the internal reasoning trace by the
backend renderer (`backend.core.renderer`). While a run is in flight the panel
shows a **live progress tracker** built from the same internal trace.
"""

from __future__ import annotations

from backend.core.renderer import render_internal

_STAGE_LABEL = {
    "created": "Starting",
    "validated": "Validating package",
    "context_analyzed": "Analyzing interview context",
    "evidence_constructed": "Building evidence graph",
    "issues_identified": "Identifying findings",
    "assessed": "Assessing suitability",
    "decision_synthesized": "Synthesizing decision",
    "actions_planned": "Planning actions",
    "drafts_generated": "Drafting communications",
    "operations_package_generated": "Assembling package",
    "waiting_approval": "Ready for approval",
    "executing": "Executing downstream actions",
    "completed": "Complete",
}
_SETTLED = {"completed", "failed", "rejected"}


def is_settled(view: dict) -> bool:
    """True when the pipeline is paused for the human or has terminated."""
    return bool(view.get("waiting_for_human")) or view.get("workflow_stage") in _SETTLED


def chat_history(view: dict) -> list[dict]:
    """Gradio Chatbot(type='messages') entries — chat-channel messages only."""
    out: list[dict] = []
    for m in view.get("messages", []):
        if m.get("kind") != "chat":
            continue
        role = "user" if m.get("role") == "human" else "assistant"
        out.append({"role": role, "content": m.get("content", "")})
    return out


def _internal_trace(view: dict) -> list[str]:
    return [
        m.get("content", "")
        for m in view.get("messages", [])
        if m.get("kind") == "internal"
    ]


def internal_panel(view: dict) -> str:
    """The reasoning trace + Operations Package internals (read-only)."""
    return render_internal(
        view.get("operations_package"), _internal_trace(view),
        view.get("workflow_stage", "unknown"),
    )


def progress_panel(view: dict) -> str:
    """Live tracker shown while the LLM pipeline is running."""
    stage = view.get("workflow_stage", "created")
    label = _STAGE_LABEL.get(stage, stage.replace("_", " "))
    lines = [f"### ⏳ Working — {label}…", ""]
    done = _internal_trace(view)
    if done:
        lines.append("**Completed steps**")
        lines += [f"- ✓ {step}" for step in done]
        lines.append("")
    lines.append("_Cloud reasoning runs one live LLM call per step and can take "
                 "1–2 minutes. Please wait…_")
    return "\n".join(lines)


def status_line(view: dict) -> str:
    stage = view.get("workflow_stage", "unknown")
    if view.get("waiting_for_human"):
        tail = "waiting for your decision"
    elif stage == "completed":
        tail = "workflow complete"
    elif stage in {"failed", "rejected"}:
        tail = "workflow ended"
    else:
        tail = "⏳ working…"
    return f"**Stage:** `{stage}` — {tail}"
