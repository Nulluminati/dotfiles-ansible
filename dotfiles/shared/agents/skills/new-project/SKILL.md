---
name: new-project
description: "Set up a new repository, or bring an existing one up to standard, so that it matches the user's public repos (herdboard, herdr-extensions, pi-extensions, steam-asset-manager): local Git repo, herdboard board, GitHub repo with the standard settings, security, rulesets, CI with a gitleaks job, Dependabot, docs layout and one tooling standard per language (Python, TypeScript, Rust). Also audits an existing repo against the standard and lists what differs, without changes. Use when the user starts a new project or repo, asks to create or publish a repository, asks to make a repo match the others, or asks to audit or check a repo's GitHub settings, rulesets, CI or tooling."
---

# New project

One standard for every public repository. The live template is `Nulluminati/steam-asset-manager`. This skill copies its settings as commands and files, so a new repository does not drift.

Files next to this `SKILL.md`:

| File | Content |
|---|---|
| `references/github.md` | `gh` commands for the repo settings, security, rulesets and required checks |
| `references/ci.md` | `ci.yml` per language, the gitleaks job, action pinning, `dependabot.yml` |
| `references/structure.md` | Files and docs every repo has, `.pi/` and `.claude/`, tooling per language |
| `templates/ruleset-main.json` | The `main` ruleset, without the status checks |
| `templates/ruleset-release-tags.json` | The `release tags` ruleset |
| `scripts/audit.py` | Read-only audit of a repo against the standard |

`SKILL_DIR` below is the folder of this file. Run `readlink -f` on it if you need the real path.

## Choose the mode

- **Create**: the repository does not exist yet. Do all the steps in "Create a repository".
- **Audit**: the user asks what differs. Run the audit, report the result, and change nothing.
- **Bring up to standard**: the repository exists. Run the audit first. Then do only the steps that fix its FAIL lines. Do the WARN lines when the user agrees.

## Ask first

Before you create anything, get these answers from the user. Do not guess them.

1. Repository name and owner. The default owner is `Nulluminati`.
2. One-line description and 3 to 6 topics.
3. Visibility. The standard repos are public. Secret scanning and push protection need a public repo (or GitHub Advanced Security).
4. Language: Python, TypeScript or Rust. One language per repo.
5. Does it publish releases (`vX.Y.Z` tags)? This adds `CHANGELOG.md`, `docs/releasing.md` and the `release tags` ruleset.
6. Local path. The default is `~/Projects/<name>`.

## Create a repository

Each step is safe to run again. Each step says how to check that it is already done.

1. **Local repo.** `git init -b main <path>` (a second run reports "Reinitialized" and changes nothing). Add the remote now, because herdboard names the board from it: `git -C <path> remote get-url origin || git -C <path> remote add origin git@github.com:<owner>/<name>.git`.
2. **Structure and tooling.** Write the files in `references/structure.md` for the language: `AGENTS.md`, `CLAUDE.md`, `README.md`, `LICENSE`, `.gitignore`, `.gitattributes`, `.pi/sandbox.json`, and the tooling config. Do not overwrite a file that exists; compare it with the standard instead.
3. **CI and Dependabot.** Write `.github/workflows/ci.yml` and `.github/dependabot.yml` from `references/ci.md`. Resolve each action SHA at that moment; do not copy old SHAs.
4. **Check locally.** Run the language's lint, format, type and test commands from `references/structure.md`. Run `gitleaks git --redact --no-banner .`. Fix every failure before the first commit.
5. **First commit.** `git add -A && git commit -m "chore: initial commit"` when `git rev-parse HEAD` fails (no commit yet). Never use `--no-verify`.
6. **herdboard board.** Run `herdboard -C <path> --json init`. The error "already has a board" means the step is done.
7. **GitHub repo.** `gh repo view <owner>/<name>` succeeds when it exists. Otherwise run `gh repo create <owner>/<name> --public --description "<description>" --source <path> --remote origin --push`. When `origin` exists already, run `gh repo create <owner>/<name> --public --description "<description>"`, then `git -C <path> push -u origin main`.
8. **Repo settings and security.** Run the commands in `references/github.md` sections 1 and 2.
9. **Rulesets.** Create or update the `main` ruleset (section 3). Add `release tags` when the repo publishes releases (section 4).
10. **Wait for CI on main.** `gh run list -R <owner>/<name> -b main -w CI -L 1` must show a completed, successful run. A check name can only be required after it ran once.
11. **Required status checks.** Add the CI job names to the `main` ruleset (section 5).
12. **Verify.** Run the audit. Every FAIL line is a step that is not done. Fix it, then run the audit again.

Then tell the user what now works: the repo URL, the board name, and the audit result.

## Audit

```bash
SKILL_DIR/scripts/audit.py <path>            # GitHub repo from the origin remote
SKILL_DIR/scripts/audit.py <path> --repo <owner>/<name>
```

- The script needs `uv` and an authenticated `gh`. It reads the GitHub API and the files in `<path>`. It changes nothing.
- Check out an up-to-date `main` in `<path>` first. The script reads the working tree, not `origin/main`.
- FAIL is a difference from the standard. WARN is a recommended file that is missing. The exit status is 1 when there is a FAIL line.
- The audit does not check everything in this skill: it does not read the README content, docs quality, or the `.gitignore` entries. Read those yourself when you bring a repo up to standard.

Report the result per repo. For each FAIL line, say which step or reference section fixes it. When an open herdboard card already covers a difference, name the card instead of a new fix. Do not file cards or change the repo unless the user asks.

Tests for the script: `uv run --with pyyaml python -I -m unittest discover -s SKILL_DIR/scripts/tests`.

## Rules

- Change one repo at a time. Get the user's approval before you change the settings or rulesets of an existing repo: they affect every open PR.
- Never weaken a ruleset to make a step pass. Admin bypass exists for the owner, not for agents. Do not push to `main` of an existing repo; open a PR.
- Keep a repo-specific difference when it has a reason, and write the reason in `AGENTS.md`. Example: steam-asset-manager pins `dtolnay/rust-toolchain` with `# master`, because that action has no release tags.
- When the standard changes, change this skill and `scripts/audit.py` together, and run the audit on the four public repos.
