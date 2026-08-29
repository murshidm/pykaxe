# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-08-29

### Added

- Initial release: Textual-based TUI that discovers tools in `pykaxe/tools/`
  and runs them as subprocesses with streaming output, resource limits, and
  a watchdog timeout.
- Built-in tools: `character-count`, `word-count`, `simple-calculator`,
  `sci-fi-quote-loop`.
- Packaging for PyPI with a `pykaxe` console script.
