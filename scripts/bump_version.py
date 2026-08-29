#!/usr/bin/env python3
"""Bump the version in src/pykaxe/__init__.py.

Usage: bump_version.py [major|minor|patch]  (default: patch)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

INIT_PATH = Path(__file__).resolve().parent.parent / "src" / "pykaxe" / "__init__.py"
VERSION_RE = re.compile(r'^__version__ = "(\d+)\.(\d+)\.(\d+)"$', re.MULTILINE)


def bump(part: str) -> str:
    text = INIT_PATH.read_text()
    match = VERSION_RE.search(text)
    if not match:
        raise SystemExit(f"could not find __version__ in {INIT_PATH}")

    major, minor, patch = (int(g) for g in match.groups())
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    elif part == "patch":
        patch += 1
    else:
        raise SystemExit(f"unknown part: {part!r} (expected major, minor, or patch)")

    new_version = f"{major}.{minor}.{patch}"
    new_text = text[: match.start()] + f'__version__ = "{new_version}"' + text[match.end() :]
    INIT_PATH.write_text(new_text)
    return new_version


def main() -> int:
    part = sys.argv[1] if len(sys.argv) > 1 else "patch"
    new_version = bump(part)
    print(new_version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
