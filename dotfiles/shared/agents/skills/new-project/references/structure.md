# Repo structure, docs and tooling

## Files in every repo

| File | Content |
|---|---|
| `AGENTS.md` | Project context for agents (see below) |
| `CLAUDE.md` | Only the line `@AGENTS.md` |
| `README.md` | What it is, install, use, develop. Long material goes to `docs/` |
| `LICENSE` | MIT, `Copyright (c) <year> Nathan Kift` |
| `.gitignore` | The GitHub template for the language, plus repo entries |
| `.gitattributes` | Line endings, and files Git must not change |
| `.pi/sandbox.json` | The pi sandbox for this repo |
| `docs/` | Long-form docs: design notes, guides, `releasing.md` |

A repo that publishes `vX.Y.Z` releases also has:

| File | Content |
|---|---|
| `CHANGELOG.md` | [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format, an `## [Unreleased]` section on top, Semantic Versioning |
| `docs/releasing.md` | How to cut a release: the version files, the release script, the Release workflow |
| `.github/workflows/release.yml` | On a `v*` tag: check the version, publish a GitHub Release with the CHANGELOG section |

Use herdboard (`~/Projects/herdboard`) as the template for the release files: `docs/releasing.md`, `bin/release.py`, `bin/release_notes.py` and `.github/workflows/release.yml`.

Add when needed:

- `.git-blame-ignore-revs`: after a commit that only reformats code. One comment line with the commit subject, then the full SHA. Run `git config blame.ignoreRevsFile .git-blame-ignore-revs` in the clone.
- `.gitleaks.toml`: only for a real gitleaks false positive. Start with `[extend] useDefault = true`, then one narrow `[[allowlists]]` entry per false positive with a `description`. See `pi-extensions/.gitleaks.toml`. Never allowlist a real secret; remove it and rotate it.

## AGENTS.md

Write what makes this repo different. Do not repeat the global `~/.agents/AGENTS.md`. The herdboard and herdr-extensions files are good models. Sections:

1. One paragraph: what the repo is and who uses it.
2. `## Layout`: the directories and the main files, with one line each.
3. `## Commands` or `## Testing`: the exact commands to lint, format, type-check and test.
4. `## Releases` (when it publishes releases): a pointer to `docs/releasing.md`.
5. `## Gotchas`: facts an agent gets wrong without help. Keep each one short and specific.

Run the `agent-md-refactor` skill when the file grows past about 150 lines.

## README.md

Sections in this order: title and one-line description, a screenshot or example when it has a UI, Install, Usage, Development (the commands from `AGENTS.md`), License. Link to `docs/` for long topics.

## .gitignore

```bash
gh api /gitignore/templates/Python --jq .source > .gitignore   # or Node, Rust
```

Then add repo entries at the end: build output, local state. Always ignore `.env`, `.claude/settings.local.json` and `.pi/` runtime state that the repo does not share (for example `.pi/workers/`, `.pi/messenger/`).

## .gitattributes

```gitattributes
# Keep LF in the repository on every OS.
* text=auto eol=lf
```

Add one line per file that Git must not convert, with a comment that says why. Examples: `tests/fixtures/**/shortcuts.vdf binary`, `tests/fixtures/convert/inbox-crlf.md -text`.

## .pi/ and .claude/

`.pi/sandbox.json` lets the pi sandbox reach the package registry of the language, and nothing else. The filesystem part is the same in every repo.

```json
{
  "network": {
    "allowedDomains": ["pypi.org", "files.pythonhosted.org"],
    "deniedDomains": []
  },
  "filesystem": {
    "denyRead": ["~", "/tmp", "/run"],
    "allowRead": [".", "~/.local/share/uv/python", "~/.local/bin/uv"],
    "allowWrite": ["."],
    "denyWrite": [".env"]
  }
}
```

- Python: the example above.
- TypeScript: `"allowedDomains": ["registry.npmjs.org", "*.npmjs.org"]` and `"allowRead": ["."]`.
- Rust: `"allowedDomains": ["crates.io", "index.crates.io", "static.crates.io"]` and `"allowRead": [".", "~/.cargo", "~/.rustup"]`.

Commit project skills for the repo in `.pi/skills/<name>/SKILL.md` or `skills/<name>/SKILL.md`.

`.claude/settings.json` is optional. Add it only for settings that every contributor needs (shared permissions or hooks). Personal settings go in `.claude/settings.local.json`, which `.gitignore` ignores.

## Python

One standard: `uv`, `pyproject.toml`, `uv.lock`, ruff for lint and format, pytest, `pre-commit`.

```bash
uv init --package <name>        # src/ layout; use --app for a single-script tool
uv add --dev ruff pytest pre-commit
uv run pre-commit install
```

`pyproject.toml` additions (from herdboard):

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--import-mode=importlib", "--strict-markers", "--strict-config", "-ra"]
filterwarnings = ["error"]
xfail_strict = true

[tool.ruff]
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "RUF100"]
```

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: ruff check
        entry: uv run --locked ruff check --fix
        language: system
        types: [python]
      - id: ruff-format
        name: ruff format
        entry: uv run --locked ruff format
        language: system
        types: [python]
```

Local checks: `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest`, `uv lock --check`.

## TypeScript

One standard: npm (`package-lock.json`), biome for lint and format, vitest, `tsc` for types, husky for the pre-commit hook.

```bash
npm init -y
npm install --save-dev @biomejs/biome typescript vitest @types/node husky lint-staged
npx biome init
npx husky init
```

`package.json` scripts:

```json
{
  "prepare": "husky || true",
  "format": "biome format --write .",
  "lint": "biome lint .",
  "test": "vitest run",
  "check": "biome check . && tsc --noEmit && vitest run",
  "check:ci": "biome ci . && tsc --noEmit && vitest run"
}
```

`tsconfig.json`: `"strict": true`, `"noUncheckedIndexedAccess": true`, `"noEmit": true`, `"module": "NodeNext"`. See `pi-extensions/tsconfig.json`.

`biome.json`: `vcs.useIgnoreFile: true`, space indent 2, line width 100, the `recommended` lint preset. See `pi-extensions/biome.json`.

`.husky/pre-commit`:

```sh
if command -v gitleaks >/dev/null 2>&1; then
  gitleaks git --staged --redact --no-banner || exit 1
else
  echo "gitleaks not installed: skipping the local secret scan (CI runs it)"
fi

npx --no-install lint-staged && npm run check
```

`lint-staged` in `package.json`: `{"*.{ts,js,mjs,json,jsonc}": "biome check --write --no-errors-on-unmatched"}`.

Local checks: `npm run check:ci`.

## Rust

One standard: cargo, `Cargo.lock` committed, `cargo fmt`, clippy with `-D warnings`, `cargo test`.

```bash
cargo init --name <name>
```

Local checks: `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`.

There is no pre-commit hook standard for Rust. CI runs the three commands.

## All languages

- gitleaks runs in CI (`ci.md`). Run `gitleaks git --redact --no-banner .` before the first push.
- Use Conventional Commits. The release tooling reads the commit types.
