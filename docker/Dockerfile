# syntax=docker/dockerfile:1
# Single-image build: one container runs both the FastAPI backend (:8000) and
# the Gradio UI (:7860). Defaults to LLM_MODE=fallback so it runs offline with
# no API key; pass -e LLM_MODE=cloud -e OLLAMA_API_KEY=... for live reasoning
# (or -e LLM_PROVIDER=azure_openai + the AZURE_OPENAI_* vars for Azure OpenAI).
#
# Build from the repo root (build context = repo root, Dockerfile lives here):
#     docker build -f docker/Dockerfile -t hiring-agent .

# ---------- builder: install deps into a venv from the lockfile ----------
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app
RUN python -m venv /opt/venv
COPY requirements.lock ./
RUN pip install -r requirements.lock

# ---------- runtime ----------
FROM python:3.12-slim AS runtime

RUN useradd --create-home --uid 1000 appuser

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Container defaults: offline + keyless out of the box; bind all interfaces.
    LLM_MODE=fallback \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    GRADIO_HOST=0.0.0.0 \
    GRADIO_PORT=7860 \
    BACKEND_BASE_URL=http://127.0.0.1:8000 \
    ENABLE_FILE_WATCHER=true \
    GRADIO_ANALYTICS_ENABLED=False

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY data/templates/ ./data/templates/
COPY data/fixtures/meeting_packages/ ./data/fixtures/meeting_packages/
COPY data/hiring_tracker.json ./data/
COPY docker/entrypoint.sh ./entrypoint.sh

RUN sed -i 's/\r$//' entrypoint.sh \
    && chmod +x entrypoint.sh \
    && mkdir -p data/runtime/input data/runtime/processing data/runtime/operations \
       data/runtime/approvals data/runtime/completed data/runtime/logs \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000 7860

HEALTHCHECK --interval=15s --timeout=3s --start-period=25s --retries=5 \
    CMD python -c "import httpx,sys; sys.exit(0 if httpx.get('http://127.0.0.1:8000/health',timeout=2).status_code==200 else 1)"

ENTRYPOINT ["./entrypoint.sh"]
