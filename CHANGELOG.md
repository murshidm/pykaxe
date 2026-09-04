# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- A small "pykaxe" label in the bottom-right corner of the footer, muted
  and non-interactive. It sits beside the `Footer` widget in a shared
  1-row container rather than overlapping it, and hides itself below
  `FOOTER_LABEL_MIN_WIDTH` (70 columns) so it can never clip over or block
  a real keyboard shortcut on a narrow terminal.

### Changed

- The TUI registers a proper `textual.theme.Theme` (still `BG =
  "ansi_default"` — every background still blends into the user's own
  terminal, unchanged) so the status footer, now Textual's real `Footer`
  widget instead of a hand-rolled row of buttons, picks up matching colors
  automatically: amber keys, read straight from `Pykaxe.BINDINGS` (key,
  tooltip, and whether it shows all live on the `Binding` itself — no more
  separate hardcoded footer strings to keep in sync). A new violet `PRIMARY`
  color is the app's own brand/heading color (the welcome title), kept
  strictly separate from the amber `ACCENT` used for tool identity.
  **Minimum Textual version raised to 0.86** (from 0.60) — required for the
  `Theme`/`App.register_theme` API this depends on.
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
- User input echoed back into the log (e.g. an argument value you typed) is
  now shown in `FG` instead of the terminal's unstyled default, and is
  markup-escaped — previously a typed value containing `[` could be parsed
  as Rich markup instead of displayed literally.
- Argument prompts ("enter text:") and the help line that can follow them
  were previously both `MUTED`, making them hard to visually tell apart.
  The prompt itself (what requires action next) is now `FG` with a `›`
  lead-in; the help line stays `MUTED`. The prompt text is also now
  markup-escaped — a default value that happens to look like markup (e.g.
  `enter interval [2.0]:`, from the shipped `sci-fi-quote-loop` example)
  previously had its brackets silently eaten, and a default matching a real
  Rich style name (`[bold]`, `[red]`, etc.) would have actually been
  applied as styling instead of shown literally.
- The welcome title and each tool's banner are now a `rich.rule.Rule`
  (a thin horizontal divider with a colored, left-aligned title) instead
  of a plain text line — gives each new context a clear heading without
  adding a box, panel, or any new chrome. `ctrl+y` copy still gets a plain
  equivalent (e.g. `pykaxe v0.1.10`, `word-count — Count the number of
  words in text.`), it just doesn't reproduce the decorative dashes.
- The suggestion list's highlighted row no longer uses a solid color fill —
  it was a flat, low-contrast dark grey (`BORDER`), easy to miss and
  visually unrelated to what's being selected. It's now a translucent
  30%-alpha wash of the tool-identity amber, matching the same restraint
  Textual's own built-in themes use for an unfocused list cursor
  (`block-cursor-blurred-background`, confirmed in Textual's installed
  source).
- Removed the separate status badge widget that used to sit above the log
  reading `<tool> · active` / `<tool> · • running`. Several visual
  treatments for it were tried during this round (a solid amber block,
  then a translucent tint, then a flat unstyled line) but every version
  still read as a second heading competing with the `Rule`-based one that
  already appears in the log the instant a tool loads, and its own
  position/padding could never be made pixel-consistent with that heading
  the way two things sharing one widget naturally are. Tool identity now
  lives only in that one heading, plus the argument help text below it;
  the running/idle state lives only in the Input's placeholder text. A
  `Digits`-based tool-count stat bar, shown while idle, was also tried and
  removed as unnecessary.
- `SETUP.md` now covers the newer macOS Gatekeeper dialog ("pykaxe.command
  was blocked to protect your Mac") that replaces the old right-click →
  Open flow on Ventura/Sonoma and later, with the System Settings → Privacy
  & Security → Open Anyway steps needed to fix it.
- `README.md` is now end-user-only: the "Contributing" and "Building &
  releasing" sections moved to a new `CONTRIBUTING.md`. The Quick Start
  prompt in `README.md`/`SETUP.md` now explicitly tells the chatbot the
  install path is the launcher (or `pipx run pykaxe`) and not to suggest
  `git clone`, after a real chatbot session invented a git-clone step that
  isn't in `SETUP.md`.
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
