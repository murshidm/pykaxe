"""Resolves and persists where pykaxe stores the user's tools."""

import json
import os
from pathlib import Path

HOME = Path.home() / ".pykaxe"
CONFIG_PATH = HOME / "config.json"
DEFAULT_TOOLS_DIR = HOME / "tools"
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


def ensure_tools_dir() -> Path:
    """Resolves the tools directory, prompting the user to choose one on
    first run (before the Textual app takes over the terminal) and
    persisting the choice so this only happens once."""
    override = os.environ.get("PYKAXE_TOOLS_DIR")
    if override:
        path = Path(override).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path

    saved = load_tools_dir()
    if saved is not None:
        saved.mkdir(parents=True, exist_ok=True)
        return saved

    answer = input(f"Where should pykaxe store your tools? [{DEFAULT_TOOLS_DIR}]: ").strip()
    chosen = Path(answer).expanduser() if answer else DEFAULT_TOOLS_DIR
    chosen.mkdir(parents=True, exist_ok=True)
    seed_examples(chosen)
    save_tools_dir(chosen)
    return chosen


def resolve_tools_dir() -> Path:
    """Like ensure_tools_dir(), but never prompts — for CLI commands (add,
    prompt, skill) that shouldn't block on stdin if the TUI hasn't been run
    yet. Falls back to the same default, seeding it if freshly created."""
    override = os.environ.get("PYKAXE_TOOLS_DIR")
    if override:
        path = Path(override).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path

    saved = load_tools_dir()
    if saved is not None:
        saved.mkdir(parents=True, exist_ok=True)
        return saved

    is_new = not DEFAULT_TOOLS_DIR.exists()
    DEFAULT_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    if is_new:
        seed_examples(DEFAULT_TOOLS_DIR)
        save_tools_dir(DEFAULT_TOOLS_DIR)
    return DEFAULT_TOOLS_DIR
