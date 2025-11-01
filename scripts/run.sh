#!/usr/bin/env bash
set -euo pipefail

BACKEND_DIR="/home/tarnv/dev/PersistentDM"
FRONTEND_DIR="/home/tarnv/dev/PersistentDM/frontend"

APP_IMPORT="${APP_IMPORT:-backend.app.main:app}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
HOST="${HOST:-0.0.0.0}"

start_backend() {
  cd "$BACKEND_DIR"
  if [ ! -d ".venv" ]; then
    echo "[start] Missing .venv. Run /home/tarnv/dev/PersistentDM/scripts/setup.sh first." >&2
    exit 1
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  echo "[start] Launching backend: uvicorn $APP_IMPORT --host $HOST --port $BACKEND_PORT"
  nohup python -m uvicorn "$APP_IMPORT" --host "$HOST" --port "$BACKEND_PORT" --reload > "$BACKEND_DIR/backend.log" 2>&1 &
  echo $! > "$BACKEND_DIR/.backend.pid"
}

wait_for_backend() {
  echo "[start] Waiting for backend health at http://localhost:${BACKEND_PORT}/health ..."
  for i in {1..120}; do
    if curl -fs "http://localhost:${BACKEND_PORT}/health" >/dev/null 2>&1; then
      echo "[start] Backend healthy."
      return 0
    fi
    sleep 0.5
  done
  echo "[start] Warning: backend did not report healthy in time." >&2
  return 1
}

cleanup() {
  if [ -f "$BACKEND_DIR/.backend.pid" ]; then
    echo "[start] Stopping backend..."
    kill "$(cat "$BACKEND_DIR/.backend.pid")" >/dev/null 2>&1 || true
    rm -f "$BACKEND_DIR/.backend.pid"
  fi
}
trap cleanup EXIT

if [ -n "${MODEL_PATH:-}" ]; then
  export MODEL_PATH
  echo "[start] MODEL_PATH is set."
fi

start_backend
wait_for_backend || true

cd "$FRONTEND_DIR"
echo "[start] Starting frontend (Vite) on :$FRONTEND_PORT"
npm run dev -- --port "$FRONTEND_PORT"
