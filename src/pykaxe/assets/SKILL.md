---
name: pykaxe-tool
description: >-
  Create a runnable tool for the user's pykaxe toolbox. Use when the user
  asks for a small automation script — adding numbers, converting units,
  counting words, reversing a string, and similar small utilities — and
  wants to keep it as a pykaxe tool rather than run it once.
---

# pykaxe tool contract

A pykaxe tool is a single `.py` file that defines:

```python
import argparse
import sys

TOOL_NAME = "kebab-case-name"      # becomes the /kebab-case-name command
TOOL_DESCRIPTION = "One-line description."

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=TOOL_NAME, description=TOOL_DESCRIPTION)
    # parser.add_argument(...)
    return parser

def main() -> int:
    args = build_parser().parse_args()
    ...
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Rules:
- One file, no package, no relative imports.
- Never call `input()` — all values come from `argparse` flags; pykaxe
  prompts for each one and passes it as `--flag value`.
- Never use `shell=True` or `os.system`.
- Prefer the standard library — pykaxe runs the script with the current
  Python interpreter directly, no isolated environment or dependency
  installer. Only reach for a third-party package if it's already something
  this project depends on, and say so if you do.
- Use `choices=[...]` and `default=...` on arguments where it makes sense —
  pykaxe surfaces both when prompting the user.

## Where to write it

Resolve the tools directory in this order, and write the file there
directly (filename = `TOOL_NAME` + `.py`) — no confirmation step needed:

1. `PYKAXE_TOOLS_DIR` environment variable, if set.
2. The `tools_dir` value in `~/.pykaxe/config.json`, if that file exists.
3. Otherwise `~/.pykaxe/tools` (create it if it doesn't exist yet).

Do not run the script yourself to test it end-to-end unless the user asks —
just make sure it parses and follows the contract above. It will appear in
pykaxe next time the user types `/` or scans tools (`ctrl+s`).
