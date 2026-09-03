# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- The TUI now gives every feedback message a distinct outcome color instead
  of rendering all of them in the same muted grey: errors (invalid input,
  failed tool start, non-zero exit, resource-limit kills) are red and
  prefixed `×`, cautions (a tool already running) are amber-yellow and
  prefixed `!`, and successful actions (a tool finishing cleanly, copying
  output) are green and prefixed `✓`. A clean tool exit previously left the
  log silent with no indication the run had finished; it now prints
  `✓ <tool> finished`. Internally, palette constants were renamed
  (`WHITE`→`FG`, `TOOL`→`ACCENT`, `RESULT`→`SUCCESS`) and two new tokens
  (`ERROR`, `WARNING`) were added, with all feedback strings routed through
  new `info()/success()/warning()/error()/cancelled()/tool_name()` helpers
  in `app.py` rather than ad-hoc inline markup.
- The footer's four buttons (`[esc] interrupt`, `[ctrl+y] copy`, etc.) are
  now built directly from `Pykaxe.BINDINGS` instead of hardcoding their own
  key/label strings — previously the footer's "interrupt" label and the
  `Interrupt` binding description could drift out of sync since they were
  two separate literals; there is now exactly one place each shortcut's key
  and text are written.
- User input echoed back into the log (e.g. an argument value you typed) is
  now shown in `FG` instead of the terminal's unstyled default, and is
  markup-escaped — previously a typed value containing `[` could be parsed
  as Rich markup instead of displayed literally.
- The welcome screen now shows the running version next to the `pykaxe`
  banner (e.g. `pykaxe v0.1.7`), so it's visible at a glance which release
  you're on.
- The default tools directory is now `~/Documents/pykaxe/scripts`, and the
  saved config moved from `~/.pykaxe/config.json` to
  `~/Documents/pykaxe/config.json` — both now live under one
  `~/Documents/pykaxe` folder instead of a separate hidden `~/.pykaxe`
  directory.

### Fixed

- A tool killed by something outside pykaxe (e.g. the OS OOM killer, a
  segfault) used to exit silently — the completion check special-cased any
  `-9`/`-15` returncode as "already explained," which was only true when
  pykaxe itself did the killing (Esc, quit, or the runtime watchdog).
  Termination is now tracked explicitly per-run (`Shell.kill_announced`), so
  pykaxe's own kills still print exactly one explanation and stay silent in
  the completion tail, while a genuinely unexpected kill now correctly
  surfaces as `× <tool> failed — exit -9`.
- `resolve_tools_dir()` now reseeds the example tools when the tools folder
  exists but is empty (previously only seeded on first creation), and the
  welcome screen tells you the resolved folder path when no tools are found
  instead of silently omitting the tool list.
- `SETUP.md`, `PROMPT.md`, and `SKILL.md` referenced a stale default tools
  path (`~/.pykaxe/tools`) left over from before the default moved to
  `~/Documents/pykaxe/scripts`. `PROMPT.md`/`SKILL.md` are read by AI
  assistants to decide where to write tool files, so the stale path could
  cause a tool to be written somewhere pykaxe never scans.

## [0.1.2] - 2026-09-03

### Changed

- Default tools directory moved from `~/.pykaxe/tools` to
  `~/Documents/pykaxe`, and tools-dir resolution was refactored into
  `resolve_tools_dir()` (replacing `ensure_tools_dir()`).
- The app's shutdown message now shows for 1 second instead of 2.
- Lowercased launcher filenames and references to `pykaxe` for naming
  consistency with the package/CLI.

### Added

- `FilePickerScreen`: a `ctrl+o` modal for browsing to a file when a tool
  argument is `Path`-typed, instead of typing the path by hand.
- Launchers for Windows (`pykaxe.bat`) and macOS (`pykaxe.command`) for
  non-technical users, running `pipx run pykaxe`.

### Docs

- Revised `README.md` and `SETUP.md` for clarity.

## [0.1.1] - 2026-08-29

### Added

- Restructured into a publishable `pykaxe` package: `src/pykaxe` layout,
  hatchling build backend, console script entry point, dynamic versioning,
  and `Makefile`/`scripts/bump_version.py` tooling.
- AI-assisted tool generation workflow: a configurable, first-run-prompted
  tools directory (`~/.pykaxe/config.json` at the time), `pykaxe
  add`/`prompt`/`skill`/`tools-dir` CLI commands, a copy-paste `PROMPT.md`
  and a Claude Code `SKILL.md` describing the tool contract, and richer
  argument prompts (choices/default/help) in the TUI.
- CI and release GitHub Actions: `ci.yml` (ruff + pytest across Python
  3.10–3.13) and `release.yml` (tag-triggered build + PyPI publish).

## [0.1.0] - 2026-08-29

### Added

- Initial release: Textual-based TUI that discovers tools in `pykaxe/tools/`
  and runs them as subprocesses with streaming output, resource limits, and
  a watchdog timeout.
- Built-in tools: `character-count`, `word-count`, `simple-calculator`,
  `sci-fi-quote-loop`.
- Packaging for PyPI with a `pykaxe` console script.
