#!/usr/bin/env bash

# Run the project's unit tests.
#
# By default, this script runs the full test suite in `test/test_snake_game.py`.
# Any additional CLI args are forwarded to pytest.

set -euo pipefail

# Resolve script directory and repository root.
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)

# Path to the test module.
TEST_FILE="${REPO_ROOT}/test/test_snake_game.py"

# Verify the test file exists before running.
if [[ ! -f "${TEST_FILE}" ]]; then
  echo "ERROR: Expected test file not found: ${TEST_FILE}" >&2
  exit 1
fi

# Run pytest with src/ on PYTHONPATH.
PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}" \
  python3 -m pytest "${TEST_FILE}" "$@"
