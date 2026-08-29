.PHONY: install dev test lint bump-patch bump-minor bump-major build publish clean

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

# Building a release bumps the patch version first, so every artifact in
# dist/ carries a version that hasn't been published yet.
build: bump-patch
	python -m build

publish: build
	twine upload dist/*

clean:
	rm -rf dist build src/*.egg-info
