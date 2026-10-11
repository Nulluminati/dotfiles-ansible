# Hunk pull request review

The `ai_tooling` role installs [Hunk](https://github.com/modem-dev/hunk) through Bun and installs
[phl28/hunk-gh-review](https://github.com/phl28/hunk-gh-review) through Hunk's extension manager.
Repeat runs keep existing installations. The CLI role supplies GitHub CLI (`gh`) on Fedora and macOS.

## Install

Run the full bootstrap on a fresh machine. The focused installation requires Bun and Node.js 22 or newer.

From the repository root:

```sh
./bin/setup -t hunk
```

Check the installed tools:

```sh
hunk --version
hunk extension list
```

The extension runs with your account's permissions. The Ansible task installs it with `--yes`, without an interactive confirmation.

## Review a pull request

Authenticate GitHub CLI before you submit a review:

```sh
gh auth login
```

To inspect a pull request's diff:

```sh
hunk gh pr 'owner/repo#123'
```

To review and submit comments without a local branch checkout, use the extension's documented workflow.
Replace `owner/repo` and `123` with the intended repository and pull request:

```sh
gh pr diff 123 --repo owner/repo | env GH_PR_NUMBER=123 GH_PR_REPO=owner/repo hunk patch -
```

1. Press `T` to open existing review threads.
2. Press `c` on a line to add a note.
3. Press `S` to confirm the pull request and submit your review.

The extension supports Comment, Approve, and Request changes. It requires Hunk 0.19 or newer.

For agent-assisted review, ask Pi or Claude Code to load the skill returned by `hunk skill path`.
The skill lets the agent inspect the live review, add notes, and navigate to relevant code.

## Review agent changes in Herdr

The `ai_tooling` role installs [herdr-hunk-diff](https://github.com/jhochenbaum/herdr-hunk-diff) as a Herdr plugin.
It opens an agent's local changes in Hunk and sends your inline comments back to that agent.
The plugin installs its own pinned Hunk and requires Node.js 22.12 or newer.

1. Focus the agent pane whose changes you want to review.
2. Press `prefix+shift+h` to open the review.
3. Press `c` on a line to add a comment.
4. Press `prefix+shift+s` to send all unsent comments to the agent as one prompt.

The plugin sends to the focused pane when it runs an agent.
Otherwise, it sends to the agent that was focused when you opened the review of that worktree.

| Key              | Action                 |
| ---------------- | ---------------------- |
| `prefix+shift+h` | Review changes         |
| `prefix+shift+s` | Send review to agent   |
| `prefix+shift+c` | Review the last commit |
| `prefix+shift+a` | Review staged changes  |

`dotfiles/shared/herdr/config.toml` declares these keys.
Do not run the plugin's `setup-keys` action, because it edits the stowed configuration and writes a backup file beside it.
