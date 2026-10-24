---
name: harness-triage
description: "File a bug or improvement for the user's agent harness as a herdboard card in the Triage column of the board that owns the fix. The harness is pi and its extensions (pi-extensions), the Herdr plugins (herdr-extensions, including herdboard), and the dotfiles that configure Claude Code, pi, Codex, Herdr, skills, hooks and AGENTS.md (dotfiles-ansible). Use when a harness tool, hook, skill, extension, plugin or agent instruction fails, misleads you, or slows the work, when you find a missing capability or a workaround the harness should not need, or when the user asks you to file harness feedback. Not for bugs in the project you were asked to work on."
---

# Harness triage

You run inside a harness that the user builds. When the harness gets in your way, file a card so the user can fix it. The card goes to the Triage column of the board that owns the fix. The user sorts Triage later.

Filing a Triage card does not need the user's permission. Triage exists for reports like this. Do not stop your current task to fix the harness. File the card, then continue.

Read the `herdboard` skill for the full CLI. This skill covers one job: route a harness report to the correct board and write a card that the user can act on.

## When to file

- A skill, hook, extension or plugin fails, gives wrong output, or has wrong instructions.
- An AGENTS.md, CLAUDE.md or skill rule conflicts with another rule, or with the real tool behavior.
- A herdboard brief, command or error message misleads you.
- You need a workaround that the harness could remove, for example a repeated manual step.
- A capability is missing and blocks a reasonable request.
- The user asks you to file harness feedback.

## When not to file

- The bug is in the project code that your task is about. Fix it or tell the user, as the task requires.
- The cause is your own mistake, and the harness did nothing wrong.
- The problem is a one-time network or service failure that a retry fixed.
- An open card already covers it. Add a `log` entry to that card instead (Step 3).

## Step 1: Find the owner

Use the component that must change, not the place where you saw the symptom.

| Component | Where it lives | Board |
|---|---|---|
| pi extensions (workers, todos, messenger, status-bar, web-search, goal, and the others in `extensions/`) | `~/Projects/pi-extensions` | `nulluminati-pi-extensions` |
| pi-extensions repository skills (`.pi/skills/`) | `~/Projects/pi-extensions/.pi/skills` | `nulluminati-pi-extensions` |
| Herdr plugins: herdboard, peer-review, agent-icons, auto-title | `~/Projects/herdr-extensions/plugins/<name>` | `nulluminati-herdr-extensions` |
| Skills that a plugin ships (`herdboard`, `peer-review`) | `~/Projects/herdr-extensions/plugins/<name>/skills` | `nulluminati-herdr-extensions` |
| herdboard briefs, card commands, columns, review and merge flow | `~/Projects/herdr-extensions/plugins/herdboard` | `nulluminati-herdr-extensions` |
| Global agent instructions (`~/.agents/AGENTS.md`, `~/.claude/CLAUDE.md`, `~/.pi/agent/AGENTS.md`) | `dotfiles/shared/agents/AGENTS.md` | `nulluminati-dotfiles-ansible` |
| Skills in this repository (`herdr`, `show-docs`, `quick-wins`, `speak`, `harness-triage`) | `dotfiles/shared/agents/skills/<name>` | `nulluminati-dotfiles-ansible` |
| Skills from the skills CLI (`.skill-lock.json`, `agent_skills` in the `ai_tooling` role) | upstream repositories | `nulluminati-dotfiles-ansible`, for the choice or the version |
| Claude Code settings, hooks, status line | `dotfiles/fedora/claude/.claude/`, `dotfiles/shared/claude/` | `nulluminati-dotfiles-ansible` |
| pi settings, models, small-model and worker-model files | `dotfiles/fedora/pi/.pi/agent/` | `nulluminati-dotfiles-ansible` |
| Herdr configuration (`~/.config/herdr/config.toml`) | `dotfiles/fedora/herdr/` | `nulluminati-dotfiles-ansible` |
| Installation of Claude Code, pi, Codex, Herdr, Herdr plugins, bun tools | `roles/ai_tooling/` | `nulluminati-dotfiles-ansible` |
| Codex configuration (`~/.codex/config.toml`, `~/.codex/hooks.json`) | not managed by the dotfiles | `nulluminati-dotfiles-ansible`, to bring it under management |
| Herdr integration hooks (`herdr-agent-state.sh`, `~/.pi/agent/extensions/herdr-agent-state.ts`) | written by Herdr; do not edit | `inbox`, tagged `#upstream` |
| Herdr itself, Claude Code, pi core, Codex, third-party Herdr plugins (`herdr-plus`, `hunkdiff`) | upstream projects | `inbox`, tagged `#upstream` |

Paths that start with `dotfiles/` or `roles/` are in `~/Projects/dotfiles-ansible`. The live files in `~/.agents`, `~/.claude` and `~/.pi/agent` are symbolic links into that repository. Run `readlink -f <path>` to find the source of a file you are not sure about.

If two components could own the fix, use the one that must change first. Name the other one in the card details.

If no row fits, use the `inbox` board. Do not guess a board name. Run `herdboard --json list --view all` to see the boards that exist.

## Step 2: Collect the evidence

Collect the facts before you write. Do not write what you did not see.

- The exact command or tool call, and its exact error text. Keep long output short: the first error line and the lines around it.
- The expected result, and the source of that expectation (a skill line, a README, a help text).
- The versions, when they matter: `herdr --version`, `pi --version`, `claude --version`, `codex --version`.
- The file and line that cause the problem, when you found them: `path/to/file:42`.
- The workaround you used, if any.

Do not include secrets, API keys, tokens, or the content of `auth.json` and `secrets.yml`.

## Step 3: Check for a duplicate

```bash
herdboard --json list --view all | jq -r '.cards[] | "\(.ref)\t\(.board)\t\(.column)\t\(.title)"' | grep -i "<keyword>"
```

Try two or three keywords. If an open card covers the problem, do not add a card. Add your evidence to it:

```bash
herdboard --json log <ref> "Seen again: <one-line summary>. Evidence: <command and error>."
```

## Step 4: File the card

Write the details to a file first. A card with more than one line of details needs `--body-file`.

```markdown
What happened: <the observed behavior, with the exact error text>
Expected: <the expected behavior, and where that expectation comes from>
Repro: <the smallest steps that show it>
Evidence: <file:line, versions, log paths>
Workaround: <what you did instead, or "none">
Found by: <your agent kind, for example claude or pi> while working on <card ref or task>
```

Then add the card:

```bash
herdboard --json add "<short title> #harness" --type bug --column Triage --board <board> --body-file <file>
```

- Use `--type bug` for a defect. Use `--type feature` for a missing capability. Use `--type docs` for wrong or missing skill or AGENTS.md text. Use `--type chore` for clean-up.
- Always add the `#harness` tag. Add `#upstream` for an upstream project. Add a component tag when it helps the user sort, for example `#skills`, `#hooks` or `#herdboard`.
- Write the title as a short statement of the problem: `herdboard brief omits the base branch`, not `Bug found`.
- `--column Triage` creates the Triage column on a board that has none. A plain `add` does not use Triage.
- Write the body file in your scratchpad directory, not in a repository.

## Step 5: Report the card

Tell the user in one sentence: the card reference, the board and the title. For example:

> Filed `tlu4` on `nulluminati-pi-extensions` (Triage): workers extension drops the model flag.

If you work on a handed-over herdboard card, also record the new card in its activity log:

```bash
herdboard --json log <your card> "Filed harness card <ref> on <board>: <title>."
```

Then continue with your task.

## Rules

- Use only the herdboard CLI. Never edit the board files in `~/todos`.
- File to the Triage column only. Do not move the card out of Triage, and do not start, plan or promote it.
- Do not create Linear issues (`add --linear` or `promote`).
- Do not fix the harness in the same session unless the user asks. The current task comes first.
- File one card for each problem. Do not combine unrelated problems.
- Do not file more than three cards in one session without asking the user first.
