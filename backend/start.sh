#!/usr/bin/env bash
set -euo pipefail

# Backend launcher for the FastAPI server.
#
# Why this script exists:
# - `python backend/main.py` won't start a server; uvicorn is the entrypoint.
# - We keep model logic in `llm_model/`, so the repo should be installed once
#   into your env (`pip install -e .`) to make `import llm_model` work.
# - We do NOT install dependencies every time you start.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ENV_NAME="${ENV_NAME:-nlp}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
LOG_LEVEL="${LOG_LEVEL:-info}"
RELOAD="${RELOAD:-0}"

# Ollama settings (used by backend/main.py)
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen3:8b}"

usage() {
  cat <<EOF
Usage:
  ./backend/start.sh [setup|check|run]

Commands:
  setup   Install backend deps + install this repo editable (one-time)
  check   Verify imports and show config
  run     Start the server (default)

Environment variables:
  ENV_NAME         Conda env name (default: nlp)
  HOST             Bind host (default: 127.0.0.1)
  PORT             Bind port (default: 8000)
  LOG_LEVEL        Uvicorn log level (default: info)
  RELOAD           1 to enable --reload (default: 0)
  OLLAMA_BASE_URL  Ollama URL (default: http://127.0.0.1:11434)
  OLLAMA_MODEL     Ollama model name (default: qwen3:8b)

Examples:
  ./backend/start.sh setup
  OLLAMA_MODEL=qwen3:8b ./backend/start.sh
  RELOAD=1 ./backend/start.sh
EOF
}

setup_env() {
  echo "[setup] Installing backend deps into conda env: ${ENV_NAME}"
  cd "${ROOT_DIR}"
  conda run -n "${ENV_NAME}" python -m pip install -r backend/requirements.txt

  echo "[setup] Installing repo editable (for llm_model imports)"
  conda run -n "${ENV_NAME}" python -m pip install -e .
}

check_env() {
  cd "${ROOT_DIR}"
  echo "[check] ENV_NAME=${ENV_NAME}"
  echo "[check] HOST=${HOST} PORT=${PORT} LOG_LEVEL=${LOG_LEVEL} RELOAD=${RELOAD}"
  echo "[check] OLLAMA_BASE_URL=${OLLAMA_BASE_URL}"
  echo "[check] OLLAMA_MODEL=${OLLAMA_MODEL}"

  # Import checks (fast fail with a helpful message)
  if ! conda run -n "${ENV_NAME}" python -c "import fastapi, uvicorn, requests" >/dev/null 2>&1; then
    echo "[check] Missing backend dependencies in env '${ENV_NAME}'." >&2
    echo "        Run: ./backend/start.sh setup" >&2
    return 2
  fi
  if ! conda run -n "${ENV_NAME}" python -c "import llm_model" >/dev/null 2>&1; then
    echo "[check] 'llm_model' not importable in env '${ENV_NAME}'." >&2
    echo "        Run: ./backend/start.sh setup" >&2
    return 2
  fi

  echo "[check] OK"
}

run_server() {
  cd "${ROOT_DIR}"

  # Don’t auto-install, but do a quick check so failures are actionable.
  check_env

  RELOAD_FLAG=()
  if [[ "${RELOAD}" == "1" ]]; then
    RELOAD_FLAG=(--reload)
  fi

  exec conda run -n "${ENV_NAME}" env \
    OLLAMA_BASE_URL="${OLLAMA_BASE_URL}" \
    OLLAMA_MODEL="${OLLAMA_MODEL}" \
    python -m uvicorn backend.main:app \
      --app-dir "${ROOT_DIR}" \
      --host "${HOST}" \
      --port "${PORT}" \
      --log-level "${LOG_LEVEL}" \
      "${RELOAD_FLAG[@]}"
}

cmd="${1:-run}"
case "${cmd}" in
  -h|--help|help)
    usage
    ;;
  setup)
    setup_env
    ;;
  check)
    check_env
    ;;
  run)
    run_server
    ;;
  *)
    echo "Unknown command: ${cmd}" >&2
    usage
    exit 2
    ;;
esac