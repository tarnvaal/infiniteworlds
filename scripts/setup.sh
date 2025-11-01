#!/usr/bin/env bash
set -euo pipefail

BACKEND_DIR="/home/tarnv/dev/PersistentDM"
FRONTEND_DIR="/home/tarnv/dev/PersistentDM/frontend"

echo "[setup] Backend: $BACKEND_DIR"
echo "[setup] Frontend: $FRONTEND_DIR"

cd "$BACKEND_DIR"
if [ ! -d ".venv" ]; then
  echo "[setup] Creating Python venv..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

cd "$FRONTEND_DIR"
npm install

echo "[setup] Done. To start dev servers: /home/tarnv/dev/PersistentDM/scripts/run.sh"
