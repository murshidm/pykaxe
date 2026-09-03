.PHONY: install dev test lint bump-patch bump-minor bump-major local-build build publish clean

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check src tests

bump-patch:
	python scripts/bump_version.py patch

bump-minor:
	python scripts/bump_version.py minor

bump-major:
	python scripts/bump_version.py major

# Local testing only: builds sdist+wheel from whatever version is currently
# in src/pykaxe/__init__.py. Never bumps the version or touches git — safe
# to run as many times as you want. See RELEASING.md.
local-build:
	python -m build

# Release prep for the `publish` fallback below. Bumps the patch version
# first, so every artifact in dist/ carries a version that hasn't been
# published yet. Normal releases don't need this — CI builds from the
# tagged commit; see RELEASING.md.
build: bump-patch
	python -m build

# Manual/emergency fallback only (needs local PyPI credentials). The normal
# release path is: bump version, commit, tag, push the tag — release.yml
# then builds and publishes via PyPI trusted publishing. See RELEASING.md.
publish: build
	twine upload dist/*

clean:
	rm -rf dist build src/*.egg-info
