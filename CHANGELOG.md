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

## [0.1.0] - 2026-08-29

### Added

- Initial release: Textual-based TUI that discovers tools in `pykaxe/tools/`
  and runs them as subprocesses with streaming output, resource limits, and
  a watchdog timeout.
- Built-in tools: `character-count`, `word-count`, `simple-calculator`,
  `sci-fi-quote-loop`.
- Packaging for PyPI with a `pykaxe` console script.
