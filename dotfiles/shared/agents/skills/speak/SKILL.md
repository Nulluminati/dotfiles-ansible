---
name: speak
description: Speak a summary of what you just did out loud using the macOS `say` command. Use when the user asks you to "talk", "speak", "say it out loud", "read it back", "voice the summary", or wants an audible recap of a completed task. macOS only.
---

# Speak

Read a short summary aloud through the Mac's speakers with the built-in `say` command.

## When to use

- The user asks you to speak, talk, or read something back out loud.
- The user wants an audible recap after a task finishes.

## How to use

After finishing the work, write a spoken-style summary of what you did and pipe it to `say`:

```bash
say "Your summary text here."
```

Use the **default system voice** — do not pass a `-v` flag.

## Writing the summary for the ear, not the eye

Speech is not the same as a written report. Before calling `say`:

- **Keep it to a few sentences.** Two to four is the target. Lead with the outcome ("Done — tests pass and it's committed"), then the one or two details that matter.
- **Going longer is fine when the content is genuinely long** — a real discussion, multiple findings, or a walkthrough the user asked for. Length should follow substance, not padding.
- **Strip anything that doesn't read aloud well.** No markdown, no code blocks, no file paths, no bullet symbols, no URLs. If a path or symbol is essential, describe it in words.
- **Write conversationally.** Full sentences, plain phrasing, the way you'd actually say it to a colleague.
- **Spell out or simplify** awkward tokens — say "version one point two" not "v1.2", "the auth module" not `auth.py`.

## Mechanics

- Pass the text as a single quoted argument. Escape any embedded double quotes, or use a here-string / `-f` file for long passages:

  ```bash
  say <<'EOF'
  Longer summary text goes here.
  It can span multiple lines.
  EOF
  ```

- `say` blocks until it finishes speaking, then returns. That's expected.
- This is macOS only. If `say` isn't found, tell the user the skill needs macOS and stop.

## Notes

- This is one-way (text to speech). It does not listen for a spoken reply.
- To change rate or voice later, `say -r 200 "..."` sets words-per-minute and `say -v Name "..."` picks a voice. The default voice is intentionally used here unless the user asks otherwise.
