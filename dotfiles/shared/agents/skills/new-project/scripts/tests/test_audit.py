"""Tests for audit.py. Run: uv run --with pyyaml python -I -m unittest discover -s scripts/tests"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
TEMPLATES = SCRIPTS.parent / "templates"

spec = importlib.util.spec_from_file_location("audit", SCRIPTS / "audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"

GOOD_REPO = {
    "description": "A tool",
    "topics": ["cli"],
    "license": {"spdx_id": "MIT"},
    "delete_branch_on_merge": True,
    "allow_update_branch": True,
    "has_projects": False,
    "has_wiki": False,
    "allow_squash_merge": True,
    "allow_merge_commit": False,
    "allow_rebase_merge": False,
    "security_and_analysis": {
        "secret_scanning": {"status": "enabled"},
        "secret_scanning_push_protection": {"status": "enabled"},
        "dependabot_security_updates": {"status": "enabled"},
    },
}

GOOD_CI = f"""
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
    steps:
      - uses: actions/checkout@{SHA} # v7.0.1
        with:
          persist-credentials: false
      - run: uv run --locked pytest
  secrets:
    name: Secret scan (gitleaks)
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@{SHA} # v7.0.1
        with:
          fetch-depth: 0
          persist-credentials: false
"""

GOOD_DEPENDABOT = """
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule: {interval: weekly}
    groups:
      github-actions:
        patterns: ["*"]
        update-types: ["minor", "patch"]
  - package-ecosystem: "uv"
    directory: "/"
    schedule: {interval: weekly}
    groups:
      uv-root:
        patterns: ["*"]
        update-types: ["minor", "patch"]
"""


def main_ruleset(checks=("Lint, format, test", "Secret scan (gitleaks)")):
    ruleset = json.loads((TEMPLATES / "ruleset-main.json").read_text())
    ruleset["rules"].append(audit.status_checks_rule(list(checks)))
    return ruleset


def messages(findings):
    return [f.message for f in findings]


class RepoSettingsTest(unittest.TestCase):
    def test_good_repo_has_no_findings(self):
        self.assertEqual(audit.check_repo_settings(GOOD_REPO), [])

    def test_each_difference_is_a_failure(self):
        repo = dict(GOOD_REPO, description="", topics=[], allow_merge_commit=True, has_projects=True)
        repo["license"] = None
        findings = audit.check_repo_settings(repo)
        self.assertTrue(all(f.level == "FAIL" for f in findings))
        self.assertEqual(len(findings), 5)

    def test_disabled_security_feature_is_a_failure(self):
        repo = json.loads(json.dumps(GOOD_REPO))
        repo["security_and_analysis"]["secret_scanning_push_protection"]["status"] = "disabled"
        self.assertEqual(
            messages(audit.check_repo_settings(repo)),
            ["security_and_analysis.secret_scanning_push_protection is disabled, expected enabled"],
        )


class MainRulesetTest(unittest.TestCase):
    def test_template_with_checks_passes(self):
        self.assertEqual(audit.check_main_ruleset(main_ruleset()), [])

    def test_missing_ruleset_fails(self):
        self.assertEqual(messages(audit.check_main_ruleset(None)), ["no ruleset named main"])

    def test_missing_status_checks_fail(self):
        ruleset = json.loads((TEMPLATES / "ruleset-main.json").read_text())
        self.assertEqual(
            messages(audit.check_main_ruleset(ruleset)),
            ["ruleset main has no required_status_checks rule"],
        )

    def test_status_checks_without_gitleaks_fail(self):
        findings = audit.check_main_ruleset(main_ruleset(checks=["Lint, format, test"]))
        self.assertEqual(messages(findings), ["ruleset main does not require 'Secret scan (gitleaks)'"])

    def test_weaker_pull_request_rule_fails(self):
        ruleset = main_ruleset()
        pr = next(r for r in ruleset["rules"] if r["type"] == "pull_request")
        pr["parameters"]["require_last_push_approval"] = False
        self.assertEqual(
            messages(audit.check_main_ruleset(ruleset)),
            ["ruleset main pull_request.require_last_push_approval is False, expected True"],
        )

    def test_missing_bypass_fails(self):
        ruleset = main_ruleset()
        ruleset["bypass_actors"] = []
        self.assertEqual(
            messages(audit.check_main_ruleset(ruleset)),
            ["ruleset main has no admin bypass (RepositoryRole 5, always)"],
        )


class ReleaseRulesetTest(unittest.TestCase):
    def test_not_needed_without_releases(self):
        self.assertEqual(audit.check_release_ruleset(None, publishes=False), [])

    def test_missing_when_releases_fails(self):
        self.assertEqual(
            messages(audit.check_release_ruleset(None, publishes=True)),
            ["no ruleset named 'release tags'"],
        )

    def test_template_passes(self):
        ruleset = json.loads((TEMPLATES / "ruleset-release-tags.json").read_text())
        self.assertEqual(audit.check_release_ruleset(ruleset, publishes=True), [])


class CiTest(unittest.TestCase):
    def test_good_ci_passes(self):
        self.assertEqual(audit.check_ci(GOOD_CI), [])

    def test_missing_ci_fails(self):
        self.assertEqual(messages(audit.check_ci(None)), [".github/workflows/ci.yml is missing"])

    def test_unpinned_action_fails(self):
        text = GOOD_CI.replace(f"actions/checkout@{SHA} # v7.0.1", "actions/checkout@v7", 1)
        self.assertIn("action not pinned to a SHA: actions/checkout@v7", messages(audit.check_ci(text)))

    def test_pinned_action_without_comment_fails(self):
        text = GOOD_CI.replace(" # v7.0.1", "", 1)
        self.assertIn(
            f"pinned action has no '# version' comment: actions/checkout@{SHA}",
            messages(audit.check_ci(text)),
        )

    def test_checkout_without_persist_credentials_fails(self):
        text = GOOD_CI.replace("          persist-credentials: false\n", "", 1)
        self.assertEqual(
            messages(audit.check_ci(text)),
            ["job test: actions/checkout does not set persist-credentials: false"],
        )

    def test_missing_gitleaks_job_fails(self):
        text = GOOD_CI.replace("Secret scan (gitleaks)", "Secrets")
        self.assertIn("no job named 'Secret scan (gitleaks)'", messages(audit.check_ci(text)))

    def test_unnamed_job_fails(self):
        text = GOOD_CI.replace("    name: Lint, format, test\n", "")
        self.assertEqual(messages(audit.check_ci(text)), ["job test has no name (the check name)"])

    def test_extra_permissions_fail(self):
        text = GOOD_CI.replace("  contents: read\n", "  contents: read\n  pull-requests: read\n")
        self.assertEqual(
            messages(audit.check_ci(text)),
            ["top-level permissions are {'contents': 'read', 'pull-requests': 'read'}, expected contents: read"],
        )

    def test_local_actions_are_not_pinned(self):
        text = GOOD_CI.replace("      - run: uv run --locked pytest\n", "      - uses: ./.github/actions/setup\n")
        self.assertEqual(audit.check_ci(text), [])


class DependabotTest(unittest.TestCase):
    def test_good_config_passes(self):
        self.assertEqual(audit.check_dependabot(GOOD_DEPENDABOT, ["uv"]), [])

    def test_missing_config_fails(self):
        self.assertEqual(messages(audit.check_dependabot(None, ["uv"])), [".github/dependabot.yml is missing"])

    def test_missing_ecosystem_fails(self):
        self.assertEqual(
            messages(audit.check_dependabot(GOOD_DEPENDABOT, ["uv", "npm"])),
            ["dependabot has no npm entry"],
        )

    def test_entry_without_minor_patch_group_fails(self):
        text = GOOD_DEPENDABOT.replace('update-types: ["minor", "patch"]', 'update-types: ["patch"]', 1)
        self.assertEqual(
            messages(audit.check_dependabot(text, ["uv"])),
            ["dependabot github-actions has no group for minor and patch updates"],
        )


class FilesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for name, text in {
            "AGENTS.md": "# AGENTS.md\n",
            "CLAUDE.md": "@AGENTS.md\n",
            "README.md": "# x\n",
            "LICENSE": "MIT License\n",
            ".gitignore": "x\n",
            ".gitattributes": "* text=auto\n",
            ".pi/sandbox.json": "{}\n",
            "pyproject.toml": '[dependency-groups]\ndev = ["pre-commit", "pytest", "ruff"]\n',
            "uv.lock": "",
            ".pre-commit-config.yaml": "repos: []\n",
        }.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)

    def tearDown(self):
        self.tmp.cleanup()

    def test_detects_python(self):
        self.assertEqual(audit.detect_ecosystems(self.root), ["uv"])

    def test_complete_python_repo_passes(self):
        self.assertEqual(audit.check_files(self.root, ["uv"], publishes=False), [])

    def test_claude_md_with_more_than_the_import_fails(self):
        (self.root / "CLAUDE.md").write_text("@AGENTS.md\nmore\n")
        self.assertEqual(
            messages(audit.check_files(self.root, ["uv"], publishes=False)),
            ["CLAUDE.md holds more than '@AGENTS.md'"],
        )

    def test_release_files_needed_when_publishing(self):
        self.assertEqual(
            messages(audit.check_files(self.root, ["uv"], publishes=True)),
            ["CHANGELOG.md is missing", "docs/releasing.md is missing"],
        )

    def test_recommended_files_are_warnings(self):
        (self.root / ".gitattributes").unlink()
        findings = audit.check_files(self.root, ["uv"], publishes=False)
        self.assertEqual([(f.level, f.message) for f in findings], [("WARN", ".gitattributes is missing")])

    def test_python_tooling_differences(self):
        (self.root / "uv.lock").unlink()
        (self.root / "pyproject.toml").write_text('[dependency-groups]\ndev = ["pytest"]\n')
        self.assertEqual(
            messages(audit.check_files(self.root, ["uv"], publishes=False)),
            ["uv.lock is missing", "pyproject.toml has no ruff dev dependency", "pyproject.toml has no pre-commit dev dependency"],
        )

    def test_rust_ci_commands(self):
        ci = "cargo fmt --check\ncargo clippy --all-targets -- -D warnings\n"
        self.assertEqual(
            messages(audit.check_rust_ci(ci)),
            ["ci.yml does not run 'cargo test'"],
        )


if __name__ == "__main__":
    unittest.main()
