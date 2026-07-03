"""FastAPI gateway for the AI Operations Platform (Hiring Agent MVP).

``create_app`` builds the app, registers the routers (hiring + health + the
pluggable agent stubs), and—via the lifespan—optionally starts the File Watcher.
A module-level ``app`` is exposed for ``uvicorn backend.api.main:app``.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.agents.hiring.session import HiringSessionService
from backend.api.middleware import RequestLogMiddleware
from backend.api.routes import (
    customer_success,
    engineering,
    health,
    hiring,
    llm_config,
    sales,
)
from backend.core.common.config import get_settings
from backend.core.common.logging import get_logger
from backend.core.common.paths import ensure_runtime_dirs
from backend.core.watcher.watcher import start_watcher

log = get_logger("api")


def create_app(enable_watcher: bool | None = None) -> FastAPI:
    settings = get_settings()
    ensure_runtime_dirs(settings)
    service = HiringSessionService(settings)
    watch = settings.enable_file_watcher if enable_watcher is None else enable_watcher

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        observer = None
        if watch:
            observer = start_watcher(settings.runtime_input_dir, service.start_from_file)
        try:
            yield
        finally:
            if observer is not None:
                observer.stop()
                observer.join()

    app = FastAPI(
        title="AI Operations Platform — Hiring Agent MVP",
        version="0.4.0",
        lifespan=lifespan,
    )
    app.state.session_service = service
    app.add_middleware(RequestLogMiddleware)

    app.include_router(health.router)
    app.include_router(hiring.router)
    app.include_router(llm_config.router)
    app.include_router(engineering.router)
    app.include_router(sales.router)
    app.include_router(customer_success.router)
    log.info("hiring agent API initialized (watcher=%s)", watch)
    return app


app = create_app()
