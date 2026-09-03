#!/bin/bash
# Double-click launcher for pykaxe on macOS.
# Opens in Terminal automatically, checks prerequisites, then runs the app
# via `pipx run --no-cache pykaxe` — no install step, always the latest
# PyPI release. --no-cache is required: pipx run otherwise reuses a cached
# ephemeral environment from a prior run and can silently launch a stale
# version even after a new release is published.
set -u

pause_and_exit() {
    echo ""
    read -n 1 -s -r -p "Press any key to close this window..."
    echo ""
    exit "$1"
}

if ! command -v python3 >/dev/null 2>&1; then
    echo "pykaxe needs Python 3, but it wasn't found on this Mac."
    echo "Install it from https://www.python.org/downloads/, then double-click pykaxe again."
    pause_and_exit 1
fi

if ! command -v pipx >/dev/null 2>&1; then
    echo "pykaxe needs pipx, but it wasn't found on this Mac."
    echo ""
    echo "Open Terminal and run these two commands:"
    echo "  python3 -m pip install --user pipx"
    echo "  python3 -m pipx ensurepath"
    echo ""
    echo "Then close this window, open a new Terminal (or double-click pykaxe again),"
    echo "and it will work from then on."
    pause_and_exit 1
fi

pipx run --no-cache pykaxe
pause_and_exit 0
