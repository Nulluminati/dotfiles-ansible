---
name: show-docs
description: "Show a documentation file to the user in a labelled Yazi pane inside Herdr instead of sending only a file path. Use when documentation needs the user's eyes: a README, guide, design note, spec, changelog, or long report the user must read. Requires HERDR_ENV=1; outside Herdr, give the file path and a short summary."
---

# Show documentation

Open documentation in a Yazi pane so the user reads it in the terminal. A file path alone is not enough.

Read the `herdr` skill for full CLI detail. This skill covers one job: put a document on screen without disturbing the user's layout or focus.

## When to use

- You finished a document and the user should read it.
- You reference a README, guide, spec, or long report as the answer.
- The user asks to see a file.
- The detail is long enough that a chat reply would bury it.

## When not to use

- The user asked only for a command, a patch, or a short answer.
- The file is code the user is already editing in a visible pane.
- You are not inside Herdr. Give the path and a two-sentence summary instead.

## Step 1: Confirm that Herdr owns this pane

```bash
test "${HERDR_ENV:-}" = 1
```

If the check fails, say that you are not running inside Herdr. Give the absolute file path. Do not inspect or control another session.

## Step 2: Read the caller context

```bash
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
herdr pane layout --pane "$HERDR_PANE_ID"
```

Use the layout to choose the split direction. Split to the right for a wide pane. Split down for a narrow or tall pane. Do not stack same-direction splits until a pane becomes unusable.

## Step 3: Create a sibling pane

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
```

- `--current` keeps the new pane in the caller's workspace and tab.
- `--cwd "$PWD"` preserves the working directory, so relative paths still resolve.
- `--no-focus` keeps the user's focus where it is. Add `--focus` only when the user asked to switch.

Read the new pane ID from the JSON response:

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus | jq -r '.result.pane.pane_id'
```

Do not guess the pane ID from sidebar order or from this document.

## Step 4: Run yazi with the file

```bash
herdr pane run <pane-id> "yazi <file>"
```

Yazi needs a real terminal. Run it through `herdr pane run`, which writes into the pane's terminal. Do not run `yazi --help` or any yazi command through a command that has no terminal; it fails.

Quote paths that contain spaces. Use an absolute path when the document lives outside the pane's working directory.

## Step 5: Label the pane

```bash
herdr pane rename <pane-id> "Worker routing guide"
```

Use a short name that says what the document is. Two to five words is enough. The label is how the user finds the pane later.

## Step 6: Verify the display

```bash
herdr pane read <pane-id> --source visible --lines 40
```

Confirm that yazi shows the intended file before you report success. The Yazi status bar shows the file name, size, and mode. If the pane shows a directory listing instead of the file, the path was wrong or relative; fix the path and run yazi again in the same pane.

Do not edit the document to make it display.

## Step 7: Report the result

State the pane label and the pane location. For example:

> `Worker routing guide` in the right pane of `w1:t1`.

Add the file path for reference. Keep the report to one or two sentences.

## Safety rules

- Do not replace a process that already runs in a pane. Create a new pane instead.
- Do not close a pane that you did not create.
- Do not close the documentation pane after the user reads it, unless the user asks.
- Do not focus, zoom, or move the user's panes.
- Do not control panes in another workspace or another machine unless the user asked.
