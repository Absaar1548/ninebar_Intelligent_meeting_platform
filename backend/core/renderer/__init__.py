"""Renderer — artifacts → Markdown views for the UI."""

from backend.core.renderer.renderer import (
    render_agent_recommendation,
    render_execution_markdown,
    render_internal,
)

__all__ = [
    "render_agent_recommendation",
    "render_internal",
    "render_execution_markdown",
]
