#!/bin/bash
# Double-click launcher for PyKaxe on macOS.
# Opens in Terminal automatically, checks prerequisites, then runs the app
# via `pipx run pykaxe` — no install step, always the latest PyPI release.
set -u

pause_and_exit() {
    echo ""
    read -n 1 -s -r -p "Press any key to close this window..."
    echo ""
    exit "$1"
}

if ! command -v python3 >/dev/null 2>&1; then
    echo "PyKaxe needs Python 3, but it wasn't found on this Mac."
    echo "Install it from https://www.python.org/downloads/, then double-click PyKaxe again."
    pause_and_exit 1
fi

if ! command -v pipx >/dev/null 2>&1; then
    echo "PyKaxe needs pipx, but it wasn't found on this Mac."
    echo ""
    echo "Open Terminal and run these two commands:"
    echo "  python3 -m pip install --user pipx"
    echo "  python3 -m pipx ensurepath"
    echo ""
    echo "Then close this window, open a new Terminal (or double-click PyKaxe again),"
    echo "and it will work from then on."
    pause_and_exit 1
fi

pipx run pykaxe
pause_and_exit 0
