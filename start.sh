#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo ""
echo "  ========================================"
echo "   Hearth - Local Character AI"
echo "  ========================================"
echo ""

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "  [ERROR] '$1' not found. Please install it and re-run."
    exit 1
  fi
}

need python3
need node
need npm

echo "  [1/4] Backend virtual environment..."
if [ ! -x backend/.venv/bin/python ]; then
  python3 -m venv backend/.venv
fi

echo "  [2/4] Python packages..."
backend/.venv/bin/python -m pip install --upgrade pip >/dev/null
backend/.venv/bin/python -m pip install -r backend/requirements.txt

echo "  [3/4] Frontend packages..."
if [ ! -d frontend/node_modules ]; then
  (cd frontend && npm install)
fi

echo "  [4/4] Starting API + UI..."
echo ""
echo "  Backend:  http://127.0.0.1:8741"
echo "  Frontend: http://127.0.0.1:5173"
echo "  Tip: ollama pull llama3.2"
echo ""

(cd backend && ../backend/.venv/bin/python run.py) &
BACKEND_PID=$!
(cd frontend && npm run dev) &
FRONTEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 3
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://127.0.0.1:5173" >/dev/null 2>&1 || true
elif command -v open >/dev/null 2>&1; then
  open "http://127.0.0.1:5173" >/dev/null 2>&1 || true
fi

echo "  Running (Ctrl+C to stop both)..."
wait
