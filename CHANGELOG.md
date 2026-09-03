# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- The welcome screen now shows the running version next to the `pykaxe`
  banner (e.g. `pykaxe v0.1.7`), so it's visible at a glance which release
  you're on.
- The default tools directory is now `~/Documents/pykaxe/scripts`, and the
  saved config moved from `~/.pykaxe/config.json` to
  `~/Documents/pykaxe/config.json` — both now live under one
  `~/Documents/pykaxe` folder instead of a separate hidden `~/.pykaxe`
  directory.

### Fixed

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
