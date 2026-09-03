"""Resolves and persists where pykaxe stores the user's tools."""

import json
import os
from pathlib import Path

PYKAXE_DIR = Path.home() / "Documents" / "pykaxe"
CONFIG_PATH = PYKAXE_DIR / "config.json"
DEFAULT_TOOLS_DIR = PYKAXE_DIR / "scripts"
EXAMPLES_DIR = Path(__file__).resolve().parent / "examples"


def load_tools_dir() -> Path | None:
    try:
        data = json.loads(CONFIG_PATH.read_text())
    except (OSError, ValueError):
        return None
    saved = data.get("tools_dir")
    return Path(saved).expanduser() if saved else None


def save_tools_dir(path: Path) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps({"tools_dir": str(path)}, indent=2) + "\n")


def seed_examples(tools_dir: Path) -> None:
    if not EXAMPLES_DIR.is_dir():
        return
    for script in EXAMPLES_DIR.glob("*.py"):
        dest = tools_dir / script.name
        if not dest.exists():
            dest.write_bytes(script.read_bytes())


def resolve_tools_dir() -> Path:
    """Resolves the tools directory, defaulting to ~/Documents/pykaxe/scripts
    on first run and persisting the choice so this only happens once. The
    resolved directory is seeded with the example tools whenever it doesn't
    already exist OR exists but has no scripts in it yet, whichever of
    override/saved/default it came from — otherwise a saved config pointing
    at a not-yet-created directory (e.g. after the tools dir moved, or the
    folder was deleted) would silently create an empty folder with no
    examples in it, and a user would see no tools listed with no clue why."""
    override = os.environ.get("PYKAXE_TOOLS_DIR")
    if override:
        path = Path(override).expanduser()
    else:
        saved = load_tools_dir()
        path = saved if saved is not None else DEFAULT_TOOLS_DIR

    is_new = not path.exists()
    path.mkdir(parents=True, exist_ok=True)
    if is_new or not any(path.glob("*.py")):
        seed_examples(path)
    if is_new and not override:
        save_tools_dir(path)
    return path
