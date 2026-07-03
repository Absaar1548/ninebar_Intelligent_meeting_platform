"""Gradio frontend (Teams chat simulation).

Presentation only: it talks to the FastAPI backend over HTTP and renders the
Approval Package; it holds no business logic (AGENTS.md §4). Gradio telemetry is
disabled here so importing the UI makes no external calls.
"""

import os

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
