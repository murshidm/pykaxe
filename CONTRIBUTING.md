# Contributing to pykaxe

This file is for people modifying pykaxe itself. If you just want to *use*
pykaxe, see [README.md](README.md) and [SETUP.md](SETUP.md) instead — you
don't need anything on this page, and in particular you don't need to clone
this repository.

## Development setup

1. Fork the repo and create a virtualenv.
2. Install in editable mode with dev dependencies:

   ```bash
   make dev
   ```

3. Add or edit a bundled example tool under `src/pykaxe/examples/`, or make
   changes to the app in `src/pykaxe/app.py`.
4. Run the tests and linter:

   ```bash
   make test
   make lint
   ```

5. Open a pull request.

See [CLAUDE.md](CLAUDE.md) for the architecture map, the tool contract, and
the sync checklist to walk through before considering a change done — it
covers cases like keeping `PROMPT.md`/`SKILL.md`/`README.md`/the example
tools in sync, and keeping the tools-directory path consistent across the
docs that describe it.

## Building & releasing

This project uses [hatchling](https://hatch.pypa.io/) as its build backend.
The version lives in `src/pykaxe/__init__.py`, not in `pyproject.toml`. For
local test builds vs. cutting an actual release (bump → tag → CI publishes
to PyPI), see [RELEASING.md](RELEASING.md).

## License

MIT — see [LICENSE](LICENSE).
