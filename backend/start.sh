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

# Optional: load repo-root .env (for GEMINI_API_KEY etc.)
if [ -f "${ROOT_DIR}/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/.env"
  set +a
fi

ENV_NAME="${ENV_NAME:-nlp}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
LOG_LEVEL="${LOG_LEVEL:-info}"
RELOAD="${RELOAD:-0}"

# Ollama settings (used by backend/main.py)
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen3:8b}"
OLLAMA_EMBEDDING_MODEL="${OLLAMA_EMBEDDING_MODEL:-qwen3-embedding:4b}"

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

  LLM_PROVIDER      LLM provider: ollama or gemini (default: ollama)
  LLM_THINKING      1 to enable thinking mode (default: 0)

  GEMINI_API_KEY    Gemini API key (recommended via repo-root .env)
  GEMINI_MODEL      Gemini model name (provider-specific)
  GEMINI_MODEL_THINKING  Gemini thinking model name

  OLLAMA_BASE_URL  Ollama URL (default: http://127.0.0.1:11434)
  OLLAMA_MODEL     Ollama model name (default: qwen3:8b)
  OLLAMA_EMBEDDING_MODEL  Ollama embedding model (default: qwen3-embedding:4b)

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
  echo "[check] LLM_PROVIDER=${LLM_PROVIDER:-ollama} LLM_THINKING=${LLM_THINKING:-0}"
  echo "[check] GEMINI_MODEL=${GEMINI_MODEL:-} GEMINI_MODEL_THINKING=${GEMINI_MODEL_THINKING:-} GEMINI_API_KEY=$([ -n "${GEMINI_API_KEY:-}" ] && echo set || echo missing)"
  echo "[check] OLLAMA_BASE_URL=${OLLAMA_BASE_URL}"
  echo "[check] OLLAMA_MODEL=${OLLAMA_MODEL}"
  echo "[check] OLLAMA_EMBEDDING_MODEL=${OLLAMA_EMBEDDING_MODEL}"

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

# Check if a port is available (returns 0 if available, 1 if in use)
check_port_available() {
  local host=$1
  local port=$2
  # Try to connect to the port, if connection succeeds, port is in use
  if command -v nc >/dev/null 2>&1; then
    if nc -z "${host}" "${port}" >/dev/null 2>&1; then
      return 1  # Port is in use
    else
      return 0  # Port is available
    fi
  elif command -v python3 >/dev/null 2>&1; then
    # Python check: if connect_ex returns 0, port is in use; if non-zero, port is available
    python3 -c "import socket; s = socket.socket(); s.settimeout(0.1); result = s.connect_ex(('${host}', ${port})); s.close(); exit(0 if result != 0 else 1)" >/dev/null 2>&1
    return $?
  else
    # Fallback: assume port is available if we can't check
    return 0
  fi
}

# Find an available port starting from the specified port
find_available_port() {
  local host=$1
  local start_port=$2
  local max_attempts=10
  local current_port=$start_port
  local attempt=0

  while [ $attempt -lt $max_attempts ]; do
    if check_port_available "${host}" "${current_port}"; then
      echo "${current_port}"
      return 0
    fi
    echo "[run] Port ${current_port} is in use, trying $((current_port + 1))..." >&2
    current_port=$((current_port + 1))
    attempt=$((attempt + 1))
  done

  echo "[run] ERROR: Could not find an available port after ${max_attempts} attempts" >&2
  return 1
}

run_server() {
  cd "${ROOT_DIR}"

  # Don’t auto-install, but do a quick check so failures are actionable.
  check_env

  # Find an available port if the default one is in use
  AVAILABLE_PORT=$(find_available_port "${HOST}" "${PORT}")
  if [ $? -ne 0 ]; then
    echo "[run] Failed to find an available port. Exiting." >&2
    exit 1
  fi

  # Update PORT if we had to use a different one
  if [ "${AVAILABLE_PORT}" != "${PORT}" ]; then
    echo "[run] Using port ${AVAILABLE_PORT} instead of ${PORT} (port ${PORT} was in use)"
    PORT="${AVAILABLE_PORT}"
  fi

  # Write port to file for frontend to discover
  echo "${PORT}" > "${ROOT_DIR}/.backend-port"

  RELOAD_FLAG=()
  if [[ "${RELOAD}" == "1" ]]; then
    RELOAD_FLAG=(--reload)
  fi

  echo "[run] Starting backend on http://${HOST}:${PORT} (env=${ENV_NAME})"
  echo "[run] Ollama: ${OLLAMA_BASE_URL}  model=${OLLAMA_MODEL}"
  echo "[run] Embedding model: ${OLLAMA_EMBEDDING_MODEL}"
  echo "[run] Press Ctrl+C to stop"

  exec conda run -n "${ENV_NAME}" env \
    PYTHONUNBUFFERED=1 \
    OLLAMA_BASE_URL="${OLLAMA_BASE_URL}" \
    OLLAMA_MODEL="${OLLAMA_MODEL}" \
    OLLAMA_EMBEDDING_MODEL="${OLLAMA_EMBEDDING_MODEL}" \
    python -m uvicorn backend.main:app \
      --app-dir "${ROOT_DIR}" \
      --host "${HOST}" \
      --port "${PORT}" \
      --log-level "${LOG_LEVEL}" \
      --access-log \
      # "${RELOAD_FLAG[@]}"
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