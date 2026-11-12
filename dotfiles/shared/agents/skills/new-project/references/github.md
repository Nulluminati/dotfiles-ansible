# GitHub configuration

Copied from the live `Nulluminati/steam-asset-manager` settings (2026-11-12). Read them again with:

```bash
gh api repos/Nulluminati/steam-asset-manager --jq '{description,topics,delete_branch_on_merge,allow_update_branch,has_projects,has_wiki,allow_squash_merge,allow_merge_commit,allow_rebase_merge,security_and_analysis}'
gh api repos/Nulluminati/steam-asset-manager/rulesets/27096820   # main
gh api repos/Nulluminati/steam-asset-manager/rulesets/27096824   # release tags
```

Set `R=<owner>/<name>` and `SKILL_DIR` (the folder of `SKILL.md`) first. Every command below is safe to run again.

## 1. Repo settings

```bash
gh repo edit "$R" \
  --description "<one-line description>" \
  --add-topic "<topic1>,<topic2>,<topic3>" \
  --delete-branch-on-merge \
  --allow-update-branch \
  --enable-projects=false \
  --enable-wiki=false \
  --enable-squash-merge \
  --enable-merge-commit=false \
  --enable-rebase-merge=false
```

- Squash merges keep the defaults: title `COMMIT_OR_PR_TITLE`, message `COMMIT_MESSAGES`.
- Issues stay on. Discussions stay off.
- The license comes from the `LICENSE` file (MIT, see `structure.md`). GitHub shows it after the push.

## 2. Security

```bash
gh api -X PATCH "repos/$R" --input - <<'EOF'
{"security_and_analysis": {
  "secret_scanning": {"status": "enabled"},
  "secret_scanning_push_protection": {"status": "enabled"}
}}
EOF
gh api -X PUT "repos/$R/vulnerability-alerts"       # Dependabot alerts, needed for security updates
gh api -X PUT "repos/$R/automated-security-fixes"   # Dependabot security updates
```

Check: `gh api "repos/$R" --jq .security_and_analysis`. `secret_scanning`, `secret_scanning_push_protection` and `dependabot_security_updates` are `enabled`. The standard keeps `secret_scanning_non_provider_patterns` and `secret_scanning_validity_checks` disabled.

## 3. Ruleset `main`

The template blocks deletion, force push, creation and direct update of `main`. It requires a PR with 1 approval, last-push approval, stale-review dismissal, resolved threads and squash merges. The repository admin role (`RepositoryRole` 5) can bypass it.

Create it, or update it to the template when it exists:

```bash
id=$(gh api "repos/$R/rulesets" --jq '.[] | select(.name == "main") | .id')
if [ -z "$id" ]; then
  gh api -X POST "repos/$R/rulesets" --input "$SKILL_DIR/templates/ruleset-main.json"
else
  checks=$(gh api "repos/$R/rulesets/$id" --jq '[.rules[] | select(.type == "required_status_checks")]')
  jq --argjson checks "$checks" '.rules += $checks' "$SKILL_DIR/templates/ruleset-main.json" \
    | gh api -X PUT "repos/$R/rulesets/$id" --input -
fi
```

The update keeps the existing `required_status_checks` rule, because the template has none.

## 4. Ruleset `release tags`

Only for a repo that publishes `vX.Y.Z` releases. It blocks deletion, force push and update of `refs/tags/v*`, with the same admin bypass. Creation stays allowed, so the release script can push a new tag.

```bash
id=$(gh api "repos/$R/rulesets" --jq '.[] | select(.name == "release tags") | .id')
if [ -z "$id" ]; then
  gh api -X POST "repos/$R/rulesets" --input "$SKILL_DIR/templates/ruleset-release-tags.json"
else
  gh api -X PUT "repos/$R/rulesets/$id" --input "$SKILL_DIR/templates/ruleset-release-tags.json"
fi
```

## 5. Required status checks

Do this only after CI ran once on `main`: GitHub matches a required check by its name, and an unknown name blocks every PR.

The check names are the `name:` values of the CI jobs. A matrix job reports one check per matrix value (steam-asset-manager: `ubuntu-latest`, `windows-latest`). Read the names from the last run on `main`:

```bash
run=$(gh run list -R "$R" -b main -w CI -L 1 --json databaseId --jq '.[0].databaseId')
gh run view "$run" -R "$R" --json jobs --jq '.jobs[].name'
```

Then add them with a strict policy (the branch must be up to date with `main`). `integration_id` 15368 is GitHub Actions.

```bash
id=$(gh api "repos/$R/rulesets" --jq '.[] | select(.name == "main") | .id')
gh api "repos/$R/rulesets/$id" \
  | jq --argjson names '["Lint, format, test", "Secret scan (gitleaks)"]' '
      {name, target, enforcement, conditions, bypass_actors,
       rules: ([.rules[] | select(.type != "required_status_checks")] + [{
         type: "required_status_checks",
         parameters: {
           strict_required_status_checks_policy: true,
           do_not_enforce_on_create: false,
           required_status_checks: [$names[] | {context: ., integration_id: 15368}]
         }}])}' \
  | gh api -X PUT "repos/$R/rulesets/$id" --input -
```

Replace the names with the job names of the repo. Check: open a PR and confirm that each check shows as Required.
