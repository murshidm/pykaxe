# pykaxe

A terminal UI for discovering and running small Python CLI tools.

`pykaxe` scans a `tools/` directory for standalone Python scripts, lets you
fuzzy-search and launch them from a single prompt, and streams their output
live — with sandboxing (memory/CPU/runtime limits, output caps) so a runaway
tool can't take the terminal down with it.

## Install

```bash
pip install pykaxe
```

Or with [pipx](https://pipx.pypa.io/) (recommended for CLI tools):

```bash
pipx install pykaxe
```

## Usage

```bash
pykaxe
```

Type `/` to see available tools, fuzzy-filter by typing part of a name, and
press Enter to select. If a tool declares arguments, pykaxe prompts for each
one in turn before running it.

| Key      | Action               |
| -------- | -------------------- |
| `/`      | List / filter tools   |
| `esc`    | Interrupt running tool |
| `ctrl+y` | Copy output to clipboard |
| `ctrl+s` | Re-scan tools directory |
| `ctrl+c` | Quit                  |

## Writing a tool

A tool is a Python script placed in `src/pykaxe/tools/` (or contributed via
a PR) that exposes this contract:

```python
import argparse
import sys

TOOL_NAME = "my-tool"
TOOL_DESCRIPTION = "One-line description shown in the tool list."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=TOOL_NAME, description=TOOL_DESCRIPTION)
    parser.add_argument("--text", required=True, help="Text to process.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print(f"you said: {args.text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Each tool runs as its own subprocess (`python <script> --arg value ...`), so
it must be runnable standalone and communicate purely through stdout/stderr
and its exit code.

## Contributing

1. Fork the repo and create a virtualenv.
2. Install in editable mode with dev dependencies:

   ```bash
   make dev
   ```

3. Add or edit a tool under `src/pykaxe/tools/`, or make changes to the app
   in `src/pykaxe/app.py`.
4. Run the tests and linter:

   ```bash
   make test
   make lint
   ```

5. Open a pull request.

## Building & releasing

This project uses [hatchling](https://hatch.pypa.io/) as its build backend.
The version lives in `src/pykaxe/__init__.py`.

```bash
make build      # bumps the patch version, then builds sdist + wheel into dist/
make publish    # builds, then uploads dist/* to PyPI via twine
```

To bump a minor or major version instead of a patch:

```bash
make bump-minor
make bump-major
```

## License

MIT — see [LICENSE](LICENSE).
