#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-localhost}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

cd "$ROOT_DIR"

python3 backend/server.py --host "$BACKEND_HOST" --port "$BACKEND_PORT" &
BACKEND_PID="$!"

cleanup() {
  kill "$BACKEND_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

NEXT_PUBLIC_API_BASE_URL="http://${BACKEND_HOST}:${BACKEND_PORT}" \
  npm run dev:frontend -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
