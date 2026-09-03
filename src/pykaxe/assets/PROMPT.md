# Writing a pykaxe tool

pykaxe is a terminal app that runs small Python scripts as tools. A tool is a
single `.py` file that follows this exact contract:

```python
import argparse
import sys

TOOL_NAME = "add-numbers"          # kebab-case, becomes the /add-numbers command
TOOL_DESCRIPTION = "Add two numbers together."  # one line

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=TOOL_NAME, description=TOOL_DESCRIPTION)
    parser.add_argument("--number1", type=float, required=True, help="First number.")
    parser.add_argument("--number2", type=float, required=True, help="Second number.")
    return parser

def main() -> int:
    args = build_parser().parse_args()
    try:
        print(f"Result: {args.number1 + args.number2}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## Rules

- Exactly one file, no package, no relative imports.
- Never call `input()` — every value must come from `argparse` flags, since
  pykaxe collects them by prompting the user and passing `--flag value` on
  the command line.
- Never use `shell=True` or `os.system`.
- Prefer the standard library. pykaxe runs the script with the current
  Python interpreter directly — there is no isolated environment or
  dependency installer, so a third-party import will fail unless the user
  already has it installed. If a third-party package is unavoidable, say so
  clearly at the top of your reply.
- `build_parser()` should use `choices=[...]` and `default=...` where it
  makes sense — pykaxe shows both to the user when prompting for that
  argument.
- Use `type=Path` (from `pathlib`) for any argument that takes a file path.
  pykaxe shows a "browse" hint for these and lets the user pick a file from
  a directory tree (ctrl+o) instead of typing the path by hand.
- `main()` returns `0` on success, non-zero on failure, and prints its
  result to stdout.

## Once the script is written

**If you cannot access the user's filesystem** (this is the normal case in
ChatGPT or Claude.ai chat): output the complete script, then tell the user
to save it as a `.py` file and run:

```
pykaxe add path/to/the-script.py
```

That validates and copies it into their tools folder — it will then show up
next time they type `/` in pykaxe.

**If you can write files on this machine** (a coding agent, e.g. Claude
Code): resolve the tools directory yourself instead of asking the user to
run `pykaxe add`:

1. If the `PYKAXE_TOOLS_DIR` environment variable is set, use it.
2. Otherwise read `tools_dir` from `~/.pykaxe/config.json`, if it exists.
3. Otherwise default to `~/.pykaxe/tools` (create it if missing).

Write the script directly into that directory. Filename should match
`TOOL_NAME` with a `.py` extension.
