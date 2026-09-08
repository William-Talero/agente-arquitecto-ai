#!/usr/bin/env bash
# Arranca backend (FastAPI) y frontend (Vite) en desarrollo.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Backend en http://127.0.0.1:8050"
"${ROOT_DIR}/backend/.venv/bin/uvicorn" --app-dir "${ROOT_DIR}/backend" app.main:app \
  --host 127.0.0.1 --port 8050 --log-level info &
BACKEND_PID=$!

cleanup() { kill "${BACKEND_PID}" 2>/dev/null || true; }
trap cleanup EXIT

echo "==> Frontend en http://localhost:5186"
npm --prefix "${ROOT_DIR}/frontend" run dev
