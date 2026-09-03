# RELEASING.md

How to build/test pykaxe locally, and separately, how to cut a real release.
These are two different lanes — follow the one you actually mean to do.
See `CLAUDE.md` for what `config.py`/version/etc. mean if you need context.

## Why there are two separate GitHub Actions workflows

| Workflow | Triggers on | Does |
| --- | --- | --- |
| `ci.yml` | every push to `main`, every PR into `main` | `ruff check` + `pytest` across Python 3.10–3.13. **Never builds or publishes anything.** |
| `release.yml` | pushing a tag matching `v*.*.*` (or manual dispatch) | Builds sdist+wheel, verifies the tag matches `__version__` (fails if not), publishes to PyPI, creates a GitHub Release. **This is the only thing that ships a release.** |

So: pushing commits to `main` only ever runs tests. Nothing gets published
until you deliberately push a version tag. That's intentional — it means
"merged to main" and "released to PyPI" are two separate decisions, and you
control the second one explicitly.

## Lane 1 — Local development & testing

Do this as often as you want. **None of it touches git, `__version__`, or
triggers any GitHub Action.**

```bash
make dev              # editable install + dev deps (once, or after pyproject changes)
make lint              # ruff check src tests
make test              # pytest
```

To sanity-check the actual packaged artifact (not just the source tree):

```bash
make local-build        # builds sdist+wheel into dist/, at whatever version
                         # __init__.py currently has — does NOT bump it
pip install dist/pykaxe-*.whl --force-reinstall   # optional: smoke-test the real wheel
```

Push to `main` (e.g. via a PR) whenever you want — that only runs `ci.yml`'s
test matrix. It does not build a release artifact and does not publish
anything, so there's no need to hold off pushing for fear of triggering a
release.

## Lane 2 — Cutting a release

Do this deliberately, once per release, when you've decided the current
`main` is what you want on PyPI.

1. **Decide the bump size** — patch/minor/major ([semver.org](https://semver.org/)).
2. **Bump the version** (the only step that changes `src/pykaxe/__init__.py`):
   ```bash
   make bump-patch     # or bump-minor / bump-major
   ```
3. **Move `[Unreleased]` in `CHANGELOG.md`** into a new
   `## [X.Y.Z] - YYYY-MM-DD` section.
4. **Commit both together:**
   ```bash
   git add src/pykaxe/__init__.py CHANGELOG.md
   git commit -m "Release vX.Y.Z"
   ```
5. **Push to `main` and wait for CI to go green:**
   ```bash
   git push origin main
   ```
   This triggers `ci.yml` only — a safety check before you tag. Don't tag a
   commit whose tests haven't passed.
6. **Tag that exact commit and push the tag:**
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
   This is the step that actually ships. `release.yml` fires, builds from
   the tagged commit, confirms the tag matches `__version__`, publishes to
   PyPI (via trusted OIDC publishing — no local credentials involved), and
   creates the GitHub Release with the built files attached.
7. **Watch the Actions tab** until the `release` job is green. Once it is,
   `pipx run --no-cache pykaxe` picks up the new version immediately — plain
   `pipx run pykaxe` (no flag) may not, since it reuses a cached ephemeral
   environment from any previous run instead of re-checking PyPI. This is
   why the launchers pass `--no-cache`.

That's exactly two workflow runs for a release: one `ci.yml` run (step 5)
and one `release.yml` run (step 6) — not one per push, not one per
`make build`.

## If something goes wrong

- **Don't force-move a tag** (`git tag -f`) to "fix" a bad release. PyPI
  already has whatever was published under that version and won't accept a
  re-upload of the same version number anyway. Instead: delete the bad tag
  and GitHub Release, bump another patch version (step 2 above), and tag
  that.
- **`make publish`** (local `twine upload`) still exists as a manual
  fallback for if PyPI's trusted-publishing/CI path is ever unavailable —
  it needs your own PyPI credentials locally (`~/.pypirc` or `TWINE_*`
  env vars) and isn't part of the normal flow. Prefer Lane 2 so the git
  tag, the GitHub Release, and the PyPI release always agree with each
  other.
