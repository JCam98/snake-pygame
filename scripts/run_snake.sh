#!/bin/bash
# Launcher for Snake Game - avoids Tcl/Tk "macOS 26 required" error on some setups.
# Prefer pythonw (macOS GUI Python) when available; otherwise use python3.

set -e
cd "$(dirname "$0")"

if command -v pythonw &>/dev/null; then
    exec pythonw snake_game.py "$@"
fi
if command -v python3 &>/dev/null; then
    exec python3 snake_game.py "$@"
fi
exec python snake_game.py "$@"
