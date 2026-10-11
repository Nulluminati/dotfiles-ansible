# Herdr Plus

The `ai_tooling` role installs [herdr-plus](https://github.com/cloudmanic/herdr-plus) through Herdr's plugin manager.
It supplies the Projects workspace picker and the Quick Actions command picker.
Repeat runs preserve an existing installation. The focused tag also installs Herdr if it is absent.

## Install

From the repository root:

```sh
./bin/setup -t herdr-plus
```

The plugin requires Herdr 0.7.0 or newer. On Fedora and macOS, its build script uses Go when available.
Otherwise, it downloads a prebuilt binary. The installation requires network access.

The Ansible task uses `--yes`. The plugin runs with your account's permissions.

Check its installation and registered actions:

```sh
herdr plugin list --plugin cloudmanic.herdr-plus
herdr plugin action list --plugin cloudmanic.herdr-plus
```

## Open the pickers

The shared Herdr configuration binds Projects to `Ctrl+B`, then `Up`.
Quick Actions uses `Ctrl+B`, then `Down`.

1. Press `Ctrl+B`.
2. Release the keys.
3. Press `Up`.

Ansible deploys the shared configuration through Stow. After changing this binding, reload Herdr:

```sh
herdr server reload-config
```

These commands also open the pickers from a shell pane inside Herdr:

```sh
herdr plugin action invoke projects --plugin cloudmanic.herdr-plus
herdr plugin action invoke quick-actions --plugin cloudmanic.herdr-plus
```

This setup installs `implementation`, `local-review`, and `pr-review` templates.
Each template has Quick Actions for the current repository and another repository.
The repository picker combines recent directories with direct directory entry.
It does not add worktree layouts.
Find the plugin's managed configuration directory with:

```sh
herdr plugin config-dir cloudmanic.herdr-plus
```

Put additional project templates in its `projects/` directory. Use the plugin's project-template guide for the TOML format.

## Implementation layout

1. Open the Projects picker inside Herdr.
2. Select `implementation`.
3. Enter the repository directory.

The layout opens Pi beside `hunk diff --watch` in the `implement` tab.
Claude Code opens in a separate `claude` tab. The `shell` tab opens an empty shell.
Both agents start in the selected repository. Use one agent at a time to edit shared files.
The template does not bypass agent permission checks.

Ansible copies templates from `roles/ai_tooling/files/herdr-plus/projects/` to the plugin's managed `projects/` directory.
Repeat runs update managed templates without deleting other project files.
Edit the repository's `implementation.toml` to change this layout. Ansible replaces edits made to the deployed copy.

The template needs `pi`, `claude`, and `hunk` on your shell's `PATH`.
The `herdr-plus` tag deploys the template; it does not install these commands.

## Directory history

The `cli` role installs [zoxide](https://github.com/ajeetdsouza/zoxide) through DNF on Fedora and Homebrew on macOS.
The Fish and Zsh configurations initialize it with `--cmd zx`, which supplies `zx` and `zxi`.
The existing Fish `z` plugin remains installed and unchanged.

From the repository root, install the program with:

```sh
ansible-playbook bootstrap.yml -i hosts --tags zoxide --ask-become-pass
```

The focused tag installs the program. Stow manages the shell configuration during the normal dotfiles deployment.
On a machine with existing Stow links, open a new shell after installation to load the initialization.

`zx name` jumps to a matching directory. `zxi` opens the interactive directory selector through fzf.
Zoxide learns from shell directory changes. It does not require a fixed repository location.
Its history stays in its local data directory, outside the managed dotfiles.
This setup does not import the existing Fish `z` history.

## Implementation Quick Actions

1. Press `Ctrl+B`.
2. Release the keys.
3. Press `Down`.

Select one of these actions:

- `Implementation here` uses the repository containing the invoking pane's directory.
- `Implementation in a repository` offers recent repositories and directory entry with Tab completion.

Type part of a repository name to filter the directory list. You do not need to enter the complete path.
The list removes duplicate repository roots and skips missing directories or directories outside Git repositories.
It follows zoxide's ranking after the current repository. It does not scan a fixed projects directory.

For a repository outside the history, select `Enter another directory...` at the top of the list.
This entry remains available when the history is empty. All three repository-selection actions use it.

1. Type a directory path, such as `~/` or an absolute path.
2. Press `Tab` to complete directory names.
3. Press `Enter` to open the selected repository.

Directory completion includes spaces and supports relative paths from the invoking pane's directory.
You can paste a complete path without shell quotes. The launcher does not execute path text as a command.
An empty entry, `Ctrl+C`, or end-of-input cancels before the launcher creates a workspace or starts agents.
The entry prompt uses the existing Herdr pane. It does not require a fixed project folder or a filesystem scan.

The fuzzy search only filters existing recent entries. It is not the path input.
Successful launches add the selected repository to zoxide history for later selection.
Open a new shell after zoxide installation to enable directory tracking.

The shared launcher uses `projects/implementation.toml`; it does not maintain a permanent template for each repository.
It creates a private temporary copy with the selected directory and workflow label, then removes that copy.
The original template remains unchanged. The launcher records successful selections in local zoxide history.

Workspace labels include the workflow name and repository path. The launcher focuses an existing workspace with the same label.
It leaves other workspaces unchanged. Renamed workspaces and workspaces opened through Projects do not match these launcher labels.
Existing workspaces retain their current layout; template changes apply when the launcher creates a workspace.

The launcher requires `uv`, Python 3.11 or newer, Git, zoxide, and an enabled Herdr Plus plugin.
Ansible deploys its script and action files with the `herdr-plus` tag. It preserves other Quick Actions files.
The launcher adds no Python dependencies. It starts the configured programs but sends no agent task prompts.

## Review layouts

Both review layouts open Pi beside Hunk, Claude Code in a separate tab, and an empty shell tab.
Both agents start idle. Ask one agent to review the displayed changes.
The startup instructions request review without code changes or remote writes.
These instructions are not a permission enforcement system. Existing agent permission settings remain active.

Review startup calls the installed `pi`, `claude`, and `hunk` executables directly. It does not apply shell aliases.
The launcher appends review instructions instead of replacing the default system prompt or changing agent settings.
It asks agents to identify the correct Hunk session before they add local annotations.
It preserves existing human notes and uses the existing workers and Messenger for requested independent checks.

### Local changes

1. Open Quick Actions with `Ctrl+B`, then `Down`.
2. Select `Local review here` or `Local review in a repository`.
3. Ask Pi or Claude Code to review the working-tree changes.

Hunk watches staged, unstaged, and untracked changes. The review does not compare committed branches by default.
The launcher clears Hunk's pull request target to prevent submission against a branch's unrelated pull request.

### Pull requests

1. Open Quick Actions with `Ctrl+B`, then `Down`.
2. Select `Pull request review here` or `Pull request review in a repository`.
3. Enter a GitHub pull request URL or `owner/repo#number` in the Hunk pane.
4. Ask Pi or Claude Code to review that target.

The directory supplies the review workspace, not the pull request identity. The target can belong to another repository.
The launcher does not check out the pull request, fetch branches, or create a worktree.
Agent instructions require matching repository and revision evidence before agents rely on local source files.
Pi's `/github` picker remains available for discovery. This setup does not add another pull request list.

An empty entry, `Ctrl+C`, or end-of-input cancels the Hunk launch. The review workspace remains open.
The launcher accepts `https://github.com/owner/repo/pull/123` and `owner/repo#123`.
It rejects bare numbers, command options, and other hosts. GitHub Enterprise is not supported by this launcher.

Sign in with `gh auth login` before review. The launcher uses an existing `GH_TOKEN` or `GITHUB_TOKEN` when available.
Otherwise, it passes the GitHub CLI credential to Hunk without printing it.
It pins `GH_PR_REPO` and `GH_PR_NUMBER` so the review extension does not infer a different target from the local branch.

In Hunk, `T` shows review threads and `c` adds a note. `S` starts explicit review submission and confirmation.
Neither the launcher nor the agent startup instructions publish a review automatically.
To review another target in the same workspace, quit Hunk and rerun the previous launch command from its shell.

The Projects picker also offers both review templates with its existing directory prompt.
Ansible manages instructions under `roles/ai_tooling/files/herdr-plus/prompts/`.

## Test the workflow launcher

```sh
uv run python -m unittest tests/test_herdr_workflow.py
```

The tests check directory selection, temporary templates, workspace reuse, safe path handling, and error messages.
They also check review instructions, pull request identity, cancellation, credential handling, and startup commands with fake agents.
A real terminal test verifies Tab completion with spaces and cancellation when the action does not forward standard input.
