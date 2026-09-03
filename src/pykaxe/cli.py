"""pykaxe command-line entry point: launches the TUI with no arguments, or
runs one of a few small commands for getting AI-generated tools installed."""

import argparse
import ast
import importlib.resources
import subprocess
import sys
from pathlib import Path

from pykaxe import __version__, config
from pykaxe.app import run as run_tui

REQUIRED_NAMES = ("TOOL_NAME", "TOOL_DESCRIPTION")
REQUIRED_FUNCS = ("build_parser", "main")


def check_contract(source: str) -> list[str]:
    """Static AST check for the pykaxe tool contract. Never imports or
    executes the script, since it may be AI-generated and untrusted —
    only `ast.parse` sees it here."""
    tree = ast.parse(source)
    assigned: set[str] = set()
    defined: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            assigned.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assigned.add(node.target.id)
        elif isinstance(node, ast.FunctionDef):
            defined.add(node.name)

    missing = [f"module-level `{name} = ...`" for name in REQUIRED_NAMES if name not in assigned]
    missing += [f"`def {name}(...):`" for name in REQUIRED_FUNCS if name not in defined]
    return missing


def copy_to_clipboard(text: str) -> None:
    if sys.platform == "darwin":
        subprocess.run(["pbcopy"], input=text.encode(), check=True)
        return
    if sys.platform == "win32":
        subprocess.run(["clip"], input=text.encode(), check=True)
        return
    for cmd in (["wl-copy"], ["xclip", "-selection", "clipboard"]):
        try:
            subprocess.run(cmd, input=text.encode(), check=True)
            return
        except (OSError, subprocess.CalledProcessError):
            continue
    raise RuntimeError("no clipboard utility found (tried pbcopy/clip/wl-copy/xclip)")


def cmd_add(args: argparse.Namespace) -> int:
    source_path = Path(args.path).expanduser()
    if not source_path.is_file():
        print(f"no such file: {source_path}", file=sys.stderr)
        return 1

    text = source_path.read_text()
    try:
        missing = check_contract(text)
    except SyntaxError as exc:
        print(f"{source_path.name} is not valid Python: {exc}", file=sys.stderr)
        return 1

    if missing and not args.force:
        print(f"{source_path.name} is missing the pykaxe tool contract:", file=sys.stderr)
        for item in missing:
            print(f"  - {item}", file=sys.stderr)
        print("pass --force to add it anyway", file=sys.stderr)
        return 1

    dest = config.resolve_tools_dir() / source_path.name
    dest.write_text(text)
    print(f"added {source_path.name} -> {dest}")
    return 0


def cmd_prompt(args: argparse.Namespace) -> int:
    text = importlib.resources.files("pykaxe.assets").joinpath("PROMPT.md").read_text()
    if args.copy:
        try:
            copy_to_clipboard(text)
        except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
            print(f"copy failed: {exc}", file=sys.stderr)
            return 1
        print("prompt copied to clipboard")
    else:
        print(text)
    return 0


def cmd_skill(args: argparse.Namespace) -> int:
    text = importlib.resources.files("pykaxe.assets").joinpath("SKILL.md").read_text()
    dest = Path.home() / ".claude" / "skills" / "pykaxe-tool" / "SKILL.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)
    print(f"installed skill -> {dest}")
    return 0


def cmd_tools_dir(args: argparse.Namespace) -> int:
    print(config.resolve_tools_dir())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pykaxe",
        description="A terminal UI for discovering and running small Python CLI tools.",
    )
    parser.add_argument("--version", action="version", version=f"pykaxe {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="validate and copy a tool script into your tools folder")
    add_parser.add_argument("path", help="path to a .py file")
    add_parser.add_argument("--force", action="store_true", help="add it even if the contract check fails")
    add_parser.set_defaults(func=cmd_add)

    prompt_parser = subparsers.add_parser("prompt", help="print the prompt for asking an AI to write a pykaxe tool")
    prompt_parser.add_argument("--copy", action="store_true", help="copy it to the clipboard instead of printing it")
    prompt_parser.set_defaults(func=cmd_prompt)

    skill_parser = subparsers.add_parser("skill", help="install the pykaxe Claude Code skill")
    skill_parser.set_defaults(func=cmd_skill)

    tools_dir_parser = subparsers.add_parser("tools-dir", help="print the resolved tools directory")
    tools_dir_parser.set_defaults(func=cmd_tools_dir)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command is None:
        run_tui()
        return
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
