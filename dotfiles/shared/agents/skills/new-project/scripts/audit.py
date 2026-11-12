#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Compare a repository with the new-project standard. Read-only: it changes nothing.

Usage: audit.py [PATH] [--repo OWNER/NAME]

PATH is a local clone (default: the current directory), checked out on an up-to-date main.
The GitHub repository comes from the `origin` remote unless --repo names it.
Each line is FAIL (differs from the standard) or WARN (a recommended file is missing).
The exit status is 1 when there is a FAIL line.
"""

import argparse
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

import yaml

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
GITLEAKS_JOB = "Secret scan (gitleaks)"
ADMIN_BYPASS = {"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass
class Finding:
    level: str
    area: str
    message: str


def fail(area, message):
    return Finding("FAIL", area, message)


def warn(area, message):
    return Finding("WARN", area, message)


def status_checks_rule(contexts):
    """The required_status_checks rule for the main ruleset, as the GitHub API takes it."""
    return {
        "type": "required_status_checks",
        "parameters": {
            "strict_required_status_checks_policy": True,
            "do_not_enforce_on_create": False,
            "required_status_checks": [{"context": c, "integration_id": 15368} for c in contexts],
        },
    }


# --- GitHub settings -------------------------------------------------------------------------

REPO_EXPECTED = {
    "delete_branch_on_merge": True,
    "allow_update_branch": True,
    "has_projects": False,
    "has_wiki": False,
    "allow_squash_merge": True,
    "allow_merge_commit": False,
    "allow_rebase_merge": False,
}
SECURITY_FEATURES = ["secret_scanning", "secret_scanning_push_protection", "dependabot_security_updates"]


def check_repo_settings(repo):
    findings = []
    if not repo.get("description"):
        findings.append(fail("github", "description is empty"))
    if not repo.get("topics"):
        findings.append(fail("github", "topics are empty"))
    license_id = (repo.get("license") or {}).get("spdx_id")
    if license_id != "MIT":
        findings.append(fail("github", f"license is {license_id}, expected MIT"))
    for key, expected in REPO_EXPECTED.items():
        if repo.get(key) != expected:
            findings.append(fail("github", f"{key} is {repo.get(key)}, expected {expected}"))
    security = repo.get("security_and_analysis") or {}
    for feature in SECURITY_FEATURES:
        status = (security.get(feature) or {}).get("status")
        if status != "enabled":
            findings.append(fail("github", f"security_and_analysis.{feature} is {status}, expected enabled"))
    return findings


def _template(name):
    return json.loads((TEMPLATES / name).read_text())


def _compare_ruleset(ruleset, template, label):
    findings = []
    if ruleset.get("enforcement") != "active":
        findings.append(fail("ruleset", f"{label} enforcement is {ruleset.get('enforcement')}, expected active"))
    include = ruleset.get("conditions", {}).get("ref_name", {}).get("include", [])
    for ref in template["conditions"]["ref_name"]["include"]:
        if ref not in include:
            findings.append(fail("ruleset", f"{label} does not target {ref}"))
    bypass = [{k: a.get(k) for k in ADMIN_BYPASS} for a in ruleset.get("bypass_actors", [])]
    if ADMIN_BYPASS not in bypass:
        findings.append(fail("ruleset", f"{label} has no admin bypass (RepositoryRole 5, always)"))
    rules = {r["type"]: r for r in ruleset.get("rules", [])}
    for want in template["rules"]:
        have = rules.get(want["type"])
        if have is None:
            findings.append(fail("ruleset", f"{label} has no {want['type']} rule"))
            continue
        for key, value in want.get("parameters", {}).items():
            if have.get("parameters", {}).get(key) != value:
                actual = have.get("parameters", {}).get(key)
                findings.append(fail("ruleset", f"{label} {want['type']}.{key} is {actual}, expected {value}"))
    return findings


def check_main_ruleset(ruleset):
    if ruleset is None:
        return [fail("ruleset", "no ruleset named main")]
    findings = _compare_ruleset(ruleset, _template("ruleset-main.json"), "ruleset main")
    checks = next((r for r in ruleset.get("rules", []) if r["type"] == "required_status_checks"), None)
    if checks is None:
        findings.append(fail("ruleset", "ruleset main has no required_status_checks rule"))
        return findings
    params = checks.get("parameters", {})
    if params.get("strict_required_status_checks_policy") is not True:
        findings.append(fail("ruleset", "ruleset main status checks are not strict"))
    contexts = [c["context"] for c in params.get("required_status_checks", [])]
    if GITLEAKS_JOB not in contexts:
        findings.append(fail("ruleset", f"ruleset main does not require '{GITLEAKS_JOB}'"))
    if not [c for c in contexts if c != GITLEAKS_JOB]:
        findings.append(fail("ruleset", "ruleset main requires no CI check job"))
    return findings


def check_release_ruleset(ruleset, publishes):
    if not publishes:
        return []
    if ruleset is None:
        return [fail("ruleset", "no ruleset named 'release tags'")]
    return _compare_ruleset(ruleset, _template("ruleset-release-tags.json"), "ruleset 'release tags'")


# --- CI ----------------------------------------------------------------------------------------


def check_ci(text):
    area = "ci"
    if text is None:
        return [fail(area, ".github/workflows/ci.yml is missing")]
    findings = []
    workflow = yaml.safe_load(text) or {}
    permissions = workflow.get("permissions")
    if permissions != {"contents": "read"}:
        findings.append(fail(area, f"top-level permissions are {permissions}, expected contents: read"))

    jobs = workflow.get("jobs") or {}
    names = []
    for job_id, job in jobs.items():
        if "name" not in job:
            findings.append(fail(area, f"job {job_id} has no name (the check name)"))
        names.append(job.get("name", job_id))
        for step in job.get("steps") or []:
            uses = step.get("uses", "")
            if uses.startswith("actions/checkout@") and (step.get("with") or {}).get("persist-credentials") is not False:
                findings.append(fail(area, f"job {job_id}: actions/checkout does not set persist-credentials: false"))
    if GITLEAKS_JOB not in names:
        findings.append(fail(area, f"no job named '{GITLEAKS_JOB}'"))

    # The version comment is not in the parsed YAML, so read the uses: lines as text.
    for match in re.finditer(r"^\s*(?:-\s+)?uses:\s*(\S+)(.*)$", text, re.MULTILINE):
        action, rest = match.group(1).strip("'\""), match.group(2)
        if action.startswith(("./", "docker://")):
            continue
        ref = action.rpartition("@")[2]
        if not SHA_RE.match(ref):
            findings.append(fail(area, f"action not pinned to a SHA: {action}"))
        elif not re.match(r"\s*#\s*\S", rest):
            findings.append(fail(area, f"pinned action has no '# version' comment: {action}"))
    return findings


def check_rust_ci(text):
    findings = []
    for command, pattern in [
        ("cargo fmt --check", r"cargo fmt\b.*--check"),
        ("cargo clippy ... -D warnings", r"cargo clippy\b.*-D warnings"),
        ("cargo test", r"cargo test\b"),
    ]:
        if not re.search(pattern, text or ""):
            findings.append(fail("tooling", f"ci.yml does not run '{command}'"))
    return findings


# --- Dependabot -------------------------------------------------------------------------------


def check_dependabot(text, ecosystems):
    area = "dependabot"
    if text is None:
        return [fail(area, ".github/dependabot.yml is missing")]
    findings = []
    updates = {u.get("package-ecosystem"): u for u in (yaml.safe_load(text) or {}).get("updates", [])}
    for ecosystem in ["github-actions", *ecosystems]:
        entry = updates.get(ecosystem)
        if entry is None:
            findings.append(fail(area, f"dependabot has no {ecosystem} entry"))
            continue
        groups = (entry.get("groups") or {}).values()
        if not any({"minor", "patch"} <= set(g.get("update-types", [])) for g in groups):
            findings.append(fail(area, f"dependabot {ecosystem} has no group for minor and patch updates"))
    return findings


# --- Files and tooling ------------------------------------------------------------------------


def detect_ecosystems(root):
    """The Dependabot ecosystem names of the languages in the repository."""
    found = []
    if (root / "pyproject.toml").exists():
        found.append("uv")
    if (root / "package.json").exists():
        found.append("npm")
    if (root / "Cargo.toml").exists():
        found.append("cargo")
    return found


def _python_dev_dependencies(root):
    data = tomllib.loads((root / "pyproject.toml").read_text())
    deps = [d for group in data.get("dependency-groups", {}).values() for d in group if isinstance(d, str)]
    deps += data.get("tool", {}).get("uv", {}).get("dev-dependencies", [])
    return {re.split(r"[\s<>=!~;\[]", d, maxsplit=1)[0].lower() for d in deps}


def _npm_dependencies(root):
    data = json.loads((root / "package.json").read_text())
    return set(data.get("devDependencies", {})) | set(data.get("dependencies", {}))


def check_files(root, ecosystems, publishes):
    findings = []
    for name in ["AGENTS.md", "CLAUDE.md", "README.md", "LICENSE", ".gitignore"]:
        if not (root / name).exists():
            findings.append(fail("files", f"{name} is missing"))
    claude = root / "CLAUDE.md"
    if claude.exists() and claude.read_text().strip() != "@AGENTS.md":
        findings.append(fail("files", "CLAUDE.md holds more than '@AGENTS.md'"))
    license_file = root / "LICENSE"
    if license_file.exists() and "MIT License" not in license_file.read_text():
        findings.append(fail("files", "LICENSE is not the MIT license"))
    if publishes:
        for name in ["CHANGELOG.md", "docs/releasing.md"]:
            if not (root / name).exists():
                findings.append(fail("files", f"{name} is missing"))
    for name in [".gitattributes", ".pi/sandbox.json"]:
        if not (root / name).exists():
            findings.append(warn("files", f"{name} is missing"))

    if "uv" in ecosystems:
        if not (root / "uv.lock").exists():
            findings.append(fail("tooling", "uv.lock is missing"))
        deps = _python_dev_dependencies(root)
        for tool in ["ruff", "pytest", "pre-commit"]:
            if tool not in deps:
                findings.append(fail("tooling", f"pyproject.toml has no {tool} dev dependency"))
        if not (root / ".pre-commit-config.yaml").exists():
            findings.append(warn("tooling", ".pre-commit-config.yaml is missing"))
    if "npm" in ecosystems:
        for name in ["package-lock.json", "biome.json", "tsconfig.json"]:
            if not (root / name).exists():
                findings.append(fail("tooling", f"{name} is missing"))
        deps = _npm_dependencies(root)
        for tool in ["@biomejs/biome", "vitest", "typescript", "husky"]:
            if tool not in deps:
                findings.append(fail("tooling", f"package.json has no {tool} dependency"))
        if not (root / ".husky/pre-commit").exists():
            findings.append(warn("tooling", ".husky/pre-commit is missing"))
    if "cargo" in ecosystems and not (root / "Cargo.lock").exists():
        findings.append(fail("tooling", "Cargo.lock is missing"))
    return findings


# --- Collection -------------------------------------------------------------------------------


def gh_api(path):
    result = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gh api {path}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def origin_repo(root):
    url = subprocess.run(
        ["git", "-C", str(root), "remote", "get-url", "origin"], capture_output=True, text=True, check=True
    ).stdout.strip()
    match = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$", url)
    if not match:
        raise RuntimeError(f"origin is not a GitHub URL: {url}")
    return match.group(1)


def read(root, name):
    path = root / name
    return path.read_text() if path.exists() else None


def audit(root, repo_name):
    repo = gh_api(f"repos/{repo_name}")
    rulesets = {r["name"]: r for r in gh_api(f"repos/{repo_name}/rulesets")}
    full = {name: gh_api(f"repos/{repo_name}/rulesets/{r['id']}") for name, r in rulesets.items()}
    releases = gh_api(f"repos/{repo_name}/releases?per_page=1")
    publishes = bool(releases) or (root / ".github/workflows/release.yml").exists()
    ecosystems = detect_ecosystems(root)
    ci = read(root, ".github/workflows/ci.yml")

    findings = check_repo_settings(repo)
    findings += check_main_ruleset(full.get("main"))
    findings += check_release_ruleset(full.get("release tags"), publishes)
    findings += check_ci(ci)
    findings += check_dependabot(read(root, ".github/dependabot.yml"), ecosystems)
    findings += check_files(root, ecosystems, publishes)
    if "cargo" in ecosystems:
        findings += check_rust_ci(ci)
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", nargs="?", default=".", type=Path)
    parser.add_argument("--repo", help="OWNER/NAME on GitHub (default: from the origin remote)")
    args = parser.parse_args(argv)
    root = args.path.resolve()
    repo_name = args.repo or origin_repo(root)

    findings = audit(root, repo_name)
    print(f"{repo_name} ({root})")
    if not findings:
        print("  OK: matches the standard")
    for f in findings:
        print(f"  {f.level} {f.area}: {f.message}")
    return 1 if any(f.level == "FAIL" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
