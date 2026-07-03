"""Gradio app entrypoint.

    python -m frontend.app

Requires the backend running (``uvicorn backend.api.main:app``). Talks to it at
``BACKEND_BASE_URL``.
"""

from __future__ import annotations

import frontend  # noqa: F401 - sets GRADIO_ANALYTICS_ENABLED before gradio import
from backend.core.common.config import get_settings
from frontend.api_client import HiringApiClient
from frontend.pages.chat import build_blocks


def main() -> None:
    settings = get_settings()
    api = HiringApiClient(base_url=settings.backend_base_url)
    demo = build_blocks(api)
    demo.launch(server_name=settings.gradio_host, server_port=settings.gradio_port)


if __name__ == "__main__":
    main()
