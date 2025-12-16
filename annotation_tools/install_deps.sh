#!/usr/bin/env bash
set -euo pipefail

# Install npm dependencies for annotation_tools

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Installing dependencies in: $SCRIPT_DIR"

if ! command -v npm >/dev/null 2>&1; then
  echo "Error: npm is not installed or not on PATH."
  echo "Install Node.js (which includes npm) first, then re-run this script."
  exit 1
fi

if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi

echo "Done." 
