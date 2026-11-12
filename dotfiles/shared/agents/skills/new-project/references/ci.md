# CI and Dependabot

## Rules for every workflow

- File: `.github/workflows/ci.yml`, workflow `name: CI`.
- Triggers: `push` to `main` and every `pull_request`. Quote `"on":` so yamllint does not read it as a boolean.
- Top-level `permissions: contents: read`, and nothing more. A job that needs more (a release job) asks for it in its own `permissions:`.
- Every job has a `name:`. The name is the check name that the `main` ruleset requires. Without it, the check name is the job ID.
- Every job has a `timeout-minutes:`.
- Two jobs: the language check job, and `secrets` with the name `Secret scan (gitleaks)`.
- Every `uses:` is pinned to a full commit SHA with a version comment: `uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`. A tag can move; a SHA cannot. Dependabot updates the SHA and the comment together.
- Every `actions/checkout` sets `persist-credentials: false`, so later steps cannot use the token in `.git/config`.
- Do not use `gitleaks/gitleaks-action`. The standard job downloads a pinned gitleaks release and checks its SHA-256, and needs no extra token permission.

## Pin an action

Resolve the SHA when you write the workflow. Do not copy a SHA from this file without a check; it can be old.

```bash
a=actions/checkout
tag=$(gh api "repos/$a/releases/latest" --jq .tag_name)
sha=$(gh api "repos/$a/commits/$tag" --jq .sha)
echo "uses: $a@$sha # $tag"
```

An action with no releases (for example `dtolnay/rust-toolchain`) is pinned to the SHA of its default branch, with `# master` and a comment that says why.

SHAs on 2026-11-12:

| Action | Version | SHA |
|---|---|---|
| `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `actions/setup-python` | v7.1.0 | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` |
| `astral-sh/setup-uv` | v10.3.3 | `68559e99cc807c1eb7e9238fd43a15bba460eec2` |
| `actions/setup-node` | v7.1.0 | `949feb2413d6458794dcd2491c4babbbce0c15c1` |
| `dtolnay/rust-toolchain` | master | `683b588c487a69d01f6c6ddf40f036ff682cc2c8` |
| `Swatinem/rust-cache` | v2.9.3 | `d1527c8f67ef9af357290475d4af4b0fab8f12e0` |

## The gitleaks job (all languages)

Copy it as it is. To update gitleaks, change the version and the checksum together, from `gitleaks_<version>_checksums.txt` on the release page.

```yaml
  secrets:
    name: Secret scan (gitleaks)
    runs-on: ubuntu-latest
    timeout-minutes: 5
    env:
      # Dependabot does not track this download. Update the version and the
      # checksum together, from gitleaks_<version>_checksums.txt.
      GITLEAKS_VERSION: "8.30.1"
      GITLEAKS_SHA256: "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"
    steps:
      - name: Check out repository
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          # Gitleaks needs the full history to find past leaks.
          fetch-depth: 0
          persist-credentials: false
      - name: Install gitleaks
        run: |
          set -euo pipefail
          archive="gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz"
          curl -sSfL -o "$RUNNER_TEMP/$archive" \
            "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/$archive"
          echo "$GITLEAKS_SHA256  $RUNNER_TEMP/$archive" | sha256sum -c -
          tar -xzf "$RUNNER_TEMP/$archive" -C "$RUNNER_TEMP" gitleaks
      - name: Scan the history
        run: '"$RUNNER_TEMP/gitleaks" git --redact --no-banner --log-opts="--all" .'
```

gitleaks reads `.gitleaks.toml` from the repo root when it exists. Add that file only for a real false positive (see `structure.md`).

## Python check job

```yaml
name: CI

"on":
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  test:
    name: Lint, format, test
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Check out repository
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - name: Install Python
        uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0
        with:
          python-version: "3.x"
      - name: Install uv
        uses: astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2 # v10.3.3
      - name: Lint
        run: uv run --locked ruff check .
      - name: Check the format
        run: uv run --locked ruff format --check .
      - name: Run tests
        run: uv run --locked pytest
      - name: Check the lock file
        run: uv lock --check

  # secrets: the gitleaks job above
```

## TypeScript check job

The check job runs the `check:ci` npm script (see `structure.md`), so CI and the local hook run the same commands.

```yaml
name: CI

"on":
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  check:
    name: Lint, typecheck, test
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Check out repository
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - name: Install Node.js
        uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
        with:
          node-version: "lts/*"
          cache: "npm"
      - name: Install dependencies
        run: npm ci
      - name: Run the checks
        run: npm run check:ci

  # secrets: the gitleaks job above
```

## Rust check job

Add a matrix only when the program ships for more than one OS. Then the check names are the matrix values.

```yaml
name: CI

"on":
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

env:
  CARGO_TERM_COLOR: always

jobs:
  check:
    name: Format, lint, test
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Check out repository
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - name: Install Rust
        # The action has no release tags; the toolchain input picks stable.
        uses: dtolnay/rust-toolchain@683b588c487a69d01f6c6ddf40f036ff682cc2c8 # master
        with:
          toolchain: stable
          components: rustfmt, clippy
      - uses: Swatinem/rust-cache@d1527c8f67ef9af357290475d4af4b0fab8f12e0 # v2.9.3
      - name: Format
        run: cargo fmt --check
      - name: Lint
        run: cargo clippy --all-targets -- -D warnings
      - name: Test
        run: cargo test

  # secrets: the gitleaks job above
```

## Dependabot

`.github/dependabot.yml` has one entry for `github-actions` and one for the language. Each entry is weekly, uses the `chore(deps)` commit prefix, and groups minor and patch updates into one PR. Major updates come as one PR each.

The language entry uses `uv` (Python), `npm` (TypeScript) or `cargo` (Rust).

```yaml
version: 2
updates:
  # The workflows pin each action by commit SHA with a version comment.
  # Dependabot moves both the SHA and the comment.
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    commit-message:
      prefix: "chore(deps)"
    groups:
      github-actions:
        patterns:
          - "*"
        update-types:
          - "minor"
          - "patch"

  - package-ecosystem: "uv"
    directory: "/"
    schedule:
      interval: "weekly"
    commit-message:
      prefix: "chore(deps)"
    groups:
      uv:
        patterns:
          - "*"
        update-types:
          - "minor"
          - "patch"
```
