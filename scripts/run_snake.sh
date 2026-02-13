#!/usr/bin/env bash

# Launcher for Snake Game.
#
# Notes:
# - Ensures `src/` is on PYTHONPATH so the game can be executed from anywhere.
# - On some older macOS/Darwin versions, certain pygame wheels can abort the interpreter at
#   import time. The Python code has a guard, and this script also sets an env var for
#   additional safety.

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)

APP_FILE="${REPO_ROOT}/src/snake_game.py"

if [[ ! -f "${APP_FILE}" ]]; then
  echo "ERROR: Expected application file not found: ${APP_FILE}" >&2
  exit 1
fi

# If the user didn't explicitly decide, disable pygame on older macOS/Darwin versions.
if [[ "${SNAKE_DISABLE_PYGAME:-}" == "" && "${SNAKE_ENABLE_PYGAME:-}" == "" ]]; then
  if [[ "$(uname -s)" == "Darwin" ]]; then
    DARWIN_MAJOR="$(uname -r | cut -d. -f1)"
    if [[ "${DARWIN_MAJOR}" =~ ^[0-9]+$ ]] && (( DARWIN_MAJOR < 26 )); then
      export SNAKE_DISABLE_PYGAME=1
    fi
  fi
fi

PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}"

echo "Running: ${APP_FILE}"

# Prefer pythonw if available (helps some Tk setups on macOS), otherwise python3.
if command -v pythonw >/dev/null 2>&1; then
  exec env PYTHONPATH="${PYTHONPATH}" pythonw "${APP_FILE}" "$@"
fi

exec env PYTHONPATH="${PYTHONPATH}" python3 "${APP_FILE}" "$@"
