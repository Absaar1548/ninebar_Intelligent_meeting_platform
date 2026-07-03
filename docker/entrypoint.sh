#!/bin/bash
# Start both processes in one container: FastAPI backend, then the Gradio UI.
# The container stops as soon as either process exits.
set -uo pipefail

API_PORT="${API_PORT:-8000}"

uvicorn backend.api.main:app --host "${API_HOST:-0.0.0.0}" --port "$API_PORT" &
BACKEND_PID=$!

echo "Waiting for backend on :$API_PORT ..."
for _ in $(seq 1 60); do
  if python -c "import httpx,sys; sys.exit(0 if httpx.get('http://127.0.0.1:$API_PORT/health',timeout=1).status_code==200 else 1)" 2>/dev/null; then
    echo "Backend ready."
    break
  fi
  sleep 1
done

python -m frontend.app &
FRONTEND_PID=$!

trap 'kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true' TERM INT

# Exit (stopping the container) when either process exits.
wait -n
echo "A process exited — shutting down the container."
kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
