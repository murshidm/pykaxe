# CLAUDE.md

Guidance for AI assistants (and future you) working in this repo.

## What this project is

`pykaxe` is a Textual TUI that scans a **tools directory** for standalone
Python scripts following a small contract (`TOOL_NAME`, `TOOL_DESCRIPTION`,
`build_parser()`, `main()`), lets the user pick one and fill in its arguments
interactively, and runs it as a sandboxed subprocess with streaming output.

The entire product is built around one fact staying true everywhere it's
stated: **where the tools directory is, and how it's resolved.** Most past
bugs in this repo (see `CHANGELOG.md`) have been that fact drifting out of
sync between the code and the docs/prompts that describe it. Treat that
sync as the top priority whenever you touch anything related to it.

**This file governs `README.md` and `SETUP.md` as well as the code.** Both
are user-facing instructions, not just descriptions — a beginner or an AI
walking them through setup follows them literally. Whenever a change touches
anything either of them describes (commands, flags, file paths, prompts,
first-run behavior, keybindings, the tool contract), updating the doc is part
of the change, not a follow-up. Don't treat `README.md`/`SETUP.md` edits as
optional polish; a merged change that leaves them describing the old
behavior is an unfinished change. See the sync checklist below — the
"Docs" item applies to *every* change, not just the ones with their own
bullet.

## Architecture map

| File | Role |
| --- | --- |
| `src/pykaxe/config.py` | Source of truth for tools-dir resolution: `PYKAXE_TOOLS_DIR` env var → saved `~/Documents/pykaxe/config.json` → `DEFAULT_TOOLS_DIR` (`~/Documents/pykaxe/scripts`). Also seeds example tools into a new/empty tools dir. |
| `src/pykaxe/app.py` | The Textual app. `discover_tools()` globs `*.py` in the tools dir, exec's each as a module, and keeps the ones exposing `TOOL_NAME`. `_show_welcome()` is the empty-state / tool-listing UI. |
| `src/pykaxe/cli.py` | `pykaxe` entry point. No-arg → launches the TUI. Subcommands: `add` (validate + copy a script via `check_contract`, an AST-only check so untrusted scripts are never imported), `prompt`, `skill`, `tools-dir`. |
| `src/pykaxe/examples/*.py` | The example tools seeded into a fresh tools dir. Each one is also a live conformance test of the contract (see `tests/test_tools.py`). |
| `src/pykaxe/assets/PROMPT.md` | Given to AI chatbots (ChatGPT/Claude.ai/Gemini) so they know the tool contract *and* where to tell/write a tool file. Read by an LLM, not by code. |
| `src/pykaxe/assets/SKILL.md` | Same contract, packaged as a Claude Code skill via `pykaxe skill` (installs to `~/.claude/skills/pykaxe-tool/SKILL.md`). |
| `launchers/pykaxe.command`, `launchers/pykaxe.bat` | Double-click launchers (Mac/Windows) for non-technical users. Check for `python3`/`pipx`, then run `pipx run pykaxe` — always the latest PyPI release, no install step. |
| `README.md` | User-facing overview and quick start. |
| `SETUP.md` | Step-by-step setup for beginners, written to be read *by* an AI walking a human through it. Describes the tools-dir path in prose (Finder/Explorer steps), so it drifts easily — see below. |
| `pyproject.toml` | Hatchling build config. Version lives in `src/pykaxe/__init__.py` (`[tool.hatch.version] path = ...`), not in `pyproject.toml` itself. |
| `.github/workflows/ci.yml` | Runs `ruff check` + `pytest` on push/PR across Python 3.10–3.13. |
| `.github/workflows/release.yml` | On a `v*.*.*` tag: verifies the tag matches `__version__`, builds, publishes to PyPI + GitHub Releases. |
| `scripts/bump_version.py` | Bumps `__version__` in `src/pykaxe/__init__.py`. Invoked by `make bump-patch/minor/major` and by `make build` (which always bumps patch first). |

## The tools-dir path: four places it's written down

The default tools directory (`~/Documents/pykaxe/scripts`, alongside
`~/Documents/pykaxe/config.json`) and the resolution order (env var → saved
config → default) are **stated in prose in four places outside `config.py`**,
and nothing enforces they match it:

1. `src/pykaxe/assets/PROMPT.md` — the fallback path an AI chatbot writes a
   tool file to.
2. `src/pykaxe/assets/SKILL.md` — same, for Claude Code.
3. `SETUP.md` — the path a human is told to paste into Finder/Explorer.
4. `README.md` (`## Usage`) — the one-paragraph summary of first-run behavior.

If you change `DEFAULT_TOOLS_DIR`, the resolution order, or the config file
location/format in `config.py`, **grep for the old value across all four**
and update them in the same change:

```bash
grep -rn "pykaxe-scripts\|pykaxe/config\.json\|\.pykaxe\b\|PYKAXE_TOOLS_DIR" --include="*.md" --include="*.py" .
```

A stale path in `PROMPT.md`/`SKILL.md` is worse than a stale path in
`README.md`/`SETUP.md`: those two are read and *acted on* by an AI assistant
deciding where to write a tool file. If they're wrong, a generated tool gets
silently written somewhere pykaxe never scans, and it just never shows up —
no error, no traceback, nothing in the UI to explain why.

## After every change: sync checklist

This project is small enough that "it compiles" is not the same as "it
works end to end" — several of these are prose files nothing typechecks
against. Before considering a change done, walk this list and skip only
what's genuinely unaffected:

- [ ] **Docs** (`README.md`, `SETUP.md`) — for *any* change, ask whether it
      makes a sentence in either file inaccurate: a command's behavior, a
      flag, a keybinding, a file path, a prompt shown to the user, what a
      subcommand does, first-run behavior, prerequisites. If so, fix the
      doc in the same change. Don't rely on the more specific items below
      to catch this — they call out the highest-risk cases, but this item
      is the actual rule and applies even when none of them fire.
- [ ] **Tests & lint** — `make test && make lint` (or `pytest -q` /
      `ruff check src tests` directly). If `pytest` fails with
      `ModuleNotFoundError: No module named 'pykaxe'`, the package isn't
      installed editable in the active environment — run `make dev` first
      (or create a venv and `pip install -e ".[dev]"`).
- [ ] **Tool contract** — if you touched `REQUIRED_NAMES`/`REQUIRED_FUNCS` in
      `cli.py`, or the shape of the contract itself: update
      `PROMPT.md`, `SKILL.md`, the example tools in `src/pykaxe/examples/`,
      and the contract snippet in `README.md` (`## Writing a tool by hand`)
      together — they're five copies of the same example.
- [ ] **Tools-dir path/resolution** — if you touched `config.py`'s
      resolution logic or default path, run the grep above and fix every
      hit. See the section above.
- [ ] **Launchers** — if you changed the CLI's prerequisites (new runtime
      dependency, dropped Python version support, changed how the app is
      invoked), check `launchers/pykaxe.command` and `launchers/pykaxe.bat`
      still describe accurate prerequisites and still call `pipx run
      pykaxe` correctly. These are plain shell/batch scripts — nothing
      tests them automatically, so read them.
- [ ] **CLI help text** — `cmd_*` functions and `build_parser()` in
      `cli.py` should match what `README.md`'s command table says each
      subcommand does.
- [ ] **Packaging** — if you added a new bundled asset (an example tool, a
      file under `assets/`), confirm it's actually inside the built wheel:
      `python -m build && python -c "import zipfile; [print(n) for n in
      zipfile.ZipFile('dist/pykaxe-*.whl').namelist()]"`. Hatchling includes
      everything under `src/pykaxe/` by default, but it's cheap to verify
      after touching `pyproject.toml`.
- [ ] **Version & changelog** — user-facing behavior changes get a
      `CHANGELOG.md` `[Unreleased]` entry (this file has drifted before —
      check it's actually being kept up rather than assuming CI catches it,
      since nothing does). Version bumps happen via `make bump-patch` /
      `bump-minor` / `bump-major`, or automatically via `make build`; don't
      hand-edit `__version__` in `src/pykaxe/__init__.py` — `pyproject.toml`
      reads it from there and `release.yml` checks the git tag against it.
- [ ] **CI matrix** — if you bump `requires-python` in `pyproject.toml`,
      update the `python-version` matrix in `.github/workflows/ci.yml` to
      match.

## Dev workflow

```bash
make dev             # editable install + dev deps (pytest, ruff, build, twine)
make test             # pytest
make lint             # ruff check src tests
make build             # bump patch version, then build sdist+wheel into dist/
make bump-minor        # or bump-major — for non-patch releases
```

Releasing is: bump version → commit → tag `vX.Y.Z` → push tag. `release.yml`
refuses to publish if the tag doesn't match `__version__`.

## Design constraints worth knowing before you change things

- **Untrusted script safety**: `cli.py`'s `check_contract()` only ever
  `ast.parse`s a candidate tool — never imports or executes it — because
  tools are typically AI-generated and unreviewed. Don't change `cmd_add` to
  import a script to check it.
- **Tools run as subprocesses**, not imported into the TUI process
  (`python <script> --arg value ...`), and are resource-limited
  (`_limit_tool_resources` in `app.py`: memory/CPU caps, POSIX only, best
  effort). This is deliberate sandboxing — don't move tool execution in-process.
- **No `input()` in tools**: the contract requires all tool input to come
  through `argparse`, because pykaxe collects argument values by prompting
  the user in the TUI and passing them as `--flag value`, not by piping
  stdin to the child process.
