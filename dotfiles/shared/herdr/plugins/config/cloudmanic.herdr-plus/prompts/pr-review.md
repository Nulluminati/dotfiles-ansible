# Pull request review

The sibling Hunk pane asks for a GitHub pull request URL or owner/repo#number.
Wait for Zero Cool's review request and confirm the exact target before inspection.
If the live session does not expose its pull request identity, ask Zero Cool for the reference.
Pi's existing `/github` command remains available for discovery and agent-assisted review.

Read fresh pull request metadata, diff, checks, and comments with the authenticated GitHub CLI.
Pin requests to the confirmed repository and pull request number.
Do not infer the review target from the current branch or an unrelated local checkout.
Check the repository identity and head revision before you use local files as pull request evidence.
Use remote file contents at the exact revision when the local checkout does not match.
Do not fetch branches, check out the pull request, or create a worktree automatically.

Inspect correctness and missing tests. Report actionable defects with exact diff positions.
State which tests and checks you inspected. Do not claim that local tests exercised a different pull request revision.
Keep findings and Hunk annotations local. Zero Cool controls explicit review submission in Hunk.
