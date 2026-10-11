import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "roles/ai_tooling/files/herdr-plus/bin/herdr_workflow.py"
spec = importlib.util.spec_from_file_location("herdr_workflow", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot load workflow launcher")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
TEMPLATE = (SCRIPT.parent.parent / "projects/implementation.toml").read_text()


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.repository = self.base / "repo with spaces"
        self.repository.mkdir()
        subprocess.run(["git", "init", "--quiet", str(self.repository)], check=True)
        self.config = self.base / "config"
        (self.config / "projects").mkdir(parents=True)
        (self.config / "projects/implementation.toml").write_text(TEMPLATE)
        self.plugin = self.base / "plugin"
        (self.plugin / "bin").mkdir(parents=True)
        (self.plugin / "bin/herdr-plus").write_text("fixture")
        self.profile = "implementation"
        self.template = TEMPLATE
        self.workspaces = []
        self.calls = []
        self.rendered = None
        self.environment = patch.dict(os.environ, {
            "HERDR_ENV": "1",
            "HERDR_BIN_PATH": "herdr",
            "HERDR_PLUS_WORKDIR": str(self.repository),
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.config_patch = patch.object(launcher, "CONFIG_DIR", self.config)
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)

    def fake_command(self, argv, env=None):
        self.calls.append((argv, env))
        if argv == ["herdr", "workspace", "list"]:
            return subprocess.CompletedProcess(argv, 0, json.dumps({"result": {"workspaces": self.workspaces}}), "")
        if argv[:3] == ["herdr", "workspace", "focus"]:
            return subprocess.CompletedProcess(argv, 0, '{"result": {}}', "")
        if argv[:3] == ["herdr", "plugin", "list"]:
            return subprocess.CompletedProcess(argv, 0, json.dumps({"result": {"plugins": [{
                "enabled": True, "plugin_root": str(self.plugin),
            }]}}), "")
        if argv[0] == str(self.plugin / "bin/herdr-plus"):
            self.rendered = Path(env["HERDR_PLUGIN_CONFIG_DIR"])
            profile = tomllib.loads((self.rendered / "projects" / f"{self.profile}.toml").read_text())
            self.assertEqual(profile["working_dir"], "$HERDR_WORKFLOW_DIRECTORY")
            self.assertEqual(env["HERDR_WORKFLOW_DIRECTORY"], str(self.repository))
            self.assertEqual(profile["name"], launcher.workspace_label(self.profile, self.repository))
            self.assertEqual(profile["tabs"], tomllib.loads(self.template)["tabs"])
            self.assertEqual(argv[1:], ["open", profile["name"]])
            return subprocess.CompletedProcess(argv, 0, "opened fixture\n", "")
        if argv[:2] == ["zoxide", "add"]:
            self.assertEqual(argv, ["zoxide", "add", "--", str(self.repository)])
            return subprocess.CompletedProcess(argv, 0, "", "")
        if argv[0] == "git":
            return subprocess.run(argv, check=True, capture_output=True, text=True)
        self.fail(f"Unexpected command: {argv}")

    def test_render_preserves_layout_and_source(self):
        rendered = launcher.render_template(TEMPLATE, "selected workflow")
        parsed = tomllib.loads(rendered)
        self.assertEqual(parsed["name"], "selected workflow")
        self.assertEqual(parsed["working_dir"], "$HERDR_WORKFLOW_DIRECTORY")
        self.assertEqual(parsed["tabs"], tomllib.loads(TEMPLATE)["tabs"])
        self.assertEqual((self.config / "projects/implementation.toml").read_text(), TEMPLATE)

    def test_render_escapes_quotes_and_preserves_comments(self):
        text = TEMPLATE.replace('name = "implementation"', 'name = "implementation" # Keep this comment')
        rendered = launcher.render_template(text, 'review "quoted"; $(touch never)')
        parsed = tomllib.loads(rendered)
        self.assertEqual(parsed["working_dir"], "$HERDR_WORKFLOW_DIRECTORY")
        self.assertEqual(parsed["name"], 'review "quoted"; $(touch never)')
        self.assertIn("# Keep this comment", rendered)

    def test_repository_root_accepts_subdirectories(self):
        child = self.repository / "src"
        child.mkdir()
        self.assertEqual(launcher.repository_root(child), self.repository)

    def test_repository_root_rejects_non_repositories(self):
        with self.assertRaises(launcher.WorkflowError):
            launcher.repository_root(self.base)

    def test_current_directory_uses_invoking_pane(self):
        self.assertEqual(launcher.current_directory(), self.repository)

    def test_missing_pane_directory_does_not_use_plugin_directory(self):
        with patch.dict(os.environ, {"HERDR_PLUS_WORKDIR": ""}):
            with self.assertRaises(launcher.WorkflowError):
                launcher.current_directory()

    def test_list_combines_current_repository_and_history(self):
        second = self.base / "another repository"
        second.mkdir()
        subprocess.run(["git", "init", "--quiet", str(second)], check=True)
        child = self.repository / "src"
        child.mkdir()
        original = launcher.command

        def fake(argv, env=None):
            if argv == ["zoxide", "query", "--list"]:
                return subprocess.CompletedProcess(argv, 0, f"{child}\n{second}\n{self.base}\n/missing\n", "")
            return original(argv, env)

        with patch.object(launcher, "command", side_effect=fake):
            self.assertEqual(launcher.list_repositories(), [self.repository, second])

    def test_empty_history_still_lists_current_repository(self):
        original = launcher.command

        def fake(argv, env=None):
            if argv == ["zoxide", "query", "--list"]:
                return subprocess.CompletedProcess(argv, 0, "", "")
            return original(argv, env)

        with patch.object(launcher, "command", side_effect=fake):
            self.assertEqual(launcher.list_repositories(), [self.repository])

    def test_open_uses_private_temporary_profile(self):
        with patch.object(launcher, "command", side_effect=self.fake_command):
            launcher.open_workflow("implementation", self.repository)
        self.assertIsNotNone(self.rendered)
        self.assertFalse(self.rendered.exists())
        self.assertEqual((self.config / "projects/implementation.toml").read_text(), TEMPLATE)
        self.assertEqual(self.calls[-1][0][0:2], ["zoxide", "add"])

    def test_open_focuses_matching_workspace_without_starting_agents(self):
        self.workspaces = [{"workspace_id": "w-test", "label": launcher.workspace_label("implementation", self.repository)}]
        with patch.object(launcher, "command", side_effect=self.fake_command):
            launcher.open_workflow("implementation", self.repository)
        self.assertIsNone(self.rendered)
        self.assertIn((["herdr", "workspace", "focus", "w-test"], None), self.calls)
        self.assertFalse(any(argv[:3] == ["herdr", "plugin", "list"] for argv, env in self.calls))

    def test_labels_distinguish_equal_repository_names(self):
        self.assertNotEqual(launcher.workspace_label("implementation", Path("/work/app")),
                            launcher.workspace_label("implementation", Path("/personal/app")))

    def test_profile_path_traversal_is_rejected(self):
        with patch.object(launcher, "command") as command:
            with self.assertRaises(launcher.WorkflowError):
                launcher.open_workflow("../implementation", self.repository)
            command.assert_not_called()

    def test_open_outside_herdr_is_rejected(self):
        with patch.dict(os.environ, {"HERDR_ENV": "0"}), patch.object(launcher, "command") as command:
            with self.assertRaises(launcher.WorkflowError):
                launcher.open_workflow("implementation", self.repository)
            command.assert_not_called()

    def test_failed_launch_does_not_record_history(self):
        def fail_launch(argv, env=None):
            if argv[0] == str(self.plugin / "bin/herdr-plus"):
                raise launcher.WorkflowError("Launch failed")
            return self.fake_command(argv, env)

        with patch.object(launcher, "command", side_effect=fail_launch):
            with self.assertRaises(launcher.WorkflowError):
                launcher.open_workflow("implementation", self.repository)
        self.assertFalse(any(argv[0] == "zoxide" for argv, env in self.calls))

    def test_invalid_template_does_not_control_herdr(self):
        (self.config / "projects/implementation.toml").write_text('name = "broken')
        with patch.object(launcher, "command") as command:
            with self.assertRaises(launcher.WorkflowError):
                launcher.open_workflow("implementation", self.repository)
            command.assert_not_called()

    def test_missing_zoxide_prevents_workspace_creation(self):
        original = launcher.shutil.which
        with patch.object(launcher.shutil, "which", side_effect=lambda name: None if name == "zoxide" else original(name)):
            with patch.object(launcher, "command") as command:
                with self.assertRaises(launcher.WorkflowError):
                    launcher.open_workflow("implementation", self.repository)
                command.assert_not_called()

    def test_control_characters_in_directory_names_are_rejected(self):
        directory = self.base / "repo\x1b[31m"
        directory.mkdir()
        subprocess.run(["git", "init", "--quiet", str(directory)], check=True)
        with self.assertRaises(launcher.WorkflowError):
            launcher.repository_root(directory)

    def test_dollar_signs_in_directory_names_stay_literal(self):
        self.repository = self.base / 'repo "$HOME"; $(touch never)'
        self.repository.mkdir()
        subprocess.run(["git", "init", "--quiet", str(self.repository)], check=True)
        with patch.object(launcher, "command", side_effect=self.fake_command):
            launcher.open_workflow("implementation", self.repository)
        self.assertFalse((self.base / "never").exists())

    def test_review_layouts_include_both_agents_and_shared_hunk(self):
        for profile in ("local-review", "pr-review"):
            with self.subTest(profile=profile):
                source = SCRIPT.parent.parent / "projects" / f"{profile}.toml"
                layout = tomllib.loads(source.read_text())
                self.assertEqual(layout["working_dir"], "{prompt}")
                self.assertEqual([tab["name"] for tab in layout["tabs"]], ["review", "claude", "shell"])
                panes = layout["tabs"][0]["panes"]
                self.assertIn(f"review-agent {profile} pi", panes[0]["command"])
                self.assertIn(f"review-hunk {profile}", panes[1]["command"])
                self.assertEqual(panes[1]["split"], "right")
                self.assertIn(f"review-agent {profile} claude", layout["tabs"][1]["command"])
                self.assertNotIn("command", layout["tabs"][2])

    def test_review_profiles_use_the_existing_launcher(self):
        for profile in ("local-review", "pr-review"):
            with self.subTest(profile=profile):
                self.profile = profile
                self.template = (SCRIPT.parent.parent / "projects" / f"{profile}.toml").read_text()
                (self.config / "projects" / f"{profile}.toml").write_text(self.template)
                with patch.object(launcher, "command", side_effect=self.fake_command):
                    launcher.open_workflow(profile, self.repository)
                self.assertFalse(self.rendered.exists())
                self.assertEqual((self.config / "projects" / f"{profile}.toml").read_text(), self.template)

    def test_pull_request_references_are_canonical(self):
        for value in ("owner/repo#123", " https://github.com/owner/repo/pull/123?diff=split#discussion "):
            with self.subTest(value=value):
                self.assertEqual(launcher.parse_pr_reference(value), ("owner/repo", "123"))

    def test_pull_request_references_reject_unsafe_and_ambiguous_input(self):
        for value in ("123", "--repo owner/repo", "owner/repo#0", "owner/repo#1; touch never",
                      "https://github.com.evil/owner/repo/pull/1", "http://github.com/owner/repo/pull/1",
                      "https://user@github.com/owner/repo/pull/1", "owner/..#1", "owner/repo#1\nother/repo#2"):
            with self.subTest(value=value), self.assertRaises(launcher.WorkflowError):
                launcher.parse_pr_reference(value)

    def test_local_hunk_has_no_pull_request_submission_target(self):
        with patch.object(launcher.os, "execvpe") as execute:
            self.assertEqual(launcher.launch_review_hunk("local-review"), 0)
        program, argv, env = execute.call_args.args
        self.assertEqual(program, "hunk")
        self.assertEqual(argv, ["hunk", "diff", "--watch"])
        self.assertEqual(env["GH_PR_NUMBER"], "")
        self.assertEqual(env["GH_PR_REPO"], "")

    def test_pull_request_hunk_pins_the_target_and_keeps_credentials_private(self):
        token = "fixture-token-not-a-real-credential"
        output = io.StringIO()
        with patch.dict(os.environ, {"GH_TOKEN": "", "GITHUB_TOKEN": "", "GH_HOST": "github.com"}):
            with patch.object(launcher, "command", return_value=subprocess.CompletedProcess([], 0, token + "\n", "")) as command:
                with patch.object(launcher.os, "execvpe") as execute, contextlib.redirect_stdout(output):
                    self.assertEqual(launcher.launch_review_hunk("pr-review", "owner/repo#123"), 0)
        command.assert_called_once_with(["gh", "auth", "token", "--hostname", "github.com"])
        program, argv, env = execute.call_args.args
        self.assertEqual(argv, ["hunk", "gh", "pr", "owner/repo#123"])
        self.assertEqual(env["GH_PR_REPO"], "owner/repo")
        self.assertEqual(env["GH_PR_NUMBER"], "123")
        self.assertEqual(env["GH_TOKEN"], token)
        self.assertNotIn(token, output.getvalue())

    def test_pull_request_cancellation_does_not_start_hunk(self):
        for value in ("", "   ", EOFError(), KeyboardInterrupt()):
            with self.subTest(value=repr(value)):
                options = {"side_effect": value} if isinstance(value, BaseException) else {"return_value": value}
                with patch("builtins.input", **options), patch.object(launcher.os, "execvpe") as execute:
                    self.assertEqual(launcher.launch_review_hunk("pr-review"), 0)
                    execute.assert_not_called()

    def test_review_agents_append_instructions_without_permission_bypass(self):
        prompts = self.config / "prompts"
        prompts.mkdir()
        (prompts / "review.md").write_text("Do not edit files. Do not publish reviews.")
        (prompts / "local-review.md").write_text("Review working-tree changes.")
        for agent in ("pi", "claude"):
            with self.subTest(agent=agent), patch.object(launcher.os, "execvp") as execute:
                self.assertEqual(launcher.launch_review_agent("local-review", agent), 0)
                program, argv = execute.call_args.args
                self.assertEqual(program, agent)
                self.assertEqual(argv[:2], [agent, "--append-system-prompt"])
                self.assertIn("Do not edit files", argv[2])
                self.assertIn("Review working-tree changes", argv[2])
                self.assertEqual(len(argv), 3)

    def test_review_startup_rejects_unknown_modes_and_agents(self):
        with patch.object(launcher.os, "execvp") as execute:
            with self.assertRaises(launcher.WorkflowError):
                launcher.launch_review_agent("../implementation", "pi")
            with self.assertRaises(launcher.WorkflowError):
                launcher.launch_review_agent("local-review", "sh")
            execute.assert_not_called()

    def test_startup_commands_resolve_managed_config_in_fish(self):
        config = self.base / 'managed config "$HOME"'
        (config / "bin").mkdir(parents=True)
        launcher.shutil.copyfile(SCRIPT, config / "bin/herdr_workflow.py")
        launcher.shutil.copytree(SCRIPT.parent.parent / "prompts", config / "prompts")
        executables = self.base / "executables"
        executables.mkdir()
        herdr = executables / "herdr"
        herdr.write_text('#!/bin/sh\nset -eu\ntest "$*" = "plugin config-dir cloudmanic.herdr-plus"\nprintf "%s\\n" "$FIXTURE_CONFIG"\n')
        herdr.chmod(0o755)
        recorder = '#!/usr/bin/env python3\nimport json, os, sys\nwith open(os.environ["FIXTURE_RECORD"], "w") as file:\n    json.dump({"argv":sys.argv[1:], "number":os.environ.get("GH_PR_NUMBER"), "repo":os.environ.get("GH_PR_REPO")}, file)\n'
        for program in ("pi", "claude", "hunk"):
            executable = executables / program
            executable.write_text(recorder)
            executable.chmod(0o755)
        record = self.base / "record.json"
        env = dict(os.environ, PATH=f"{executables}:{os.environ['PATH']}",
                   FIXTURE_CONFIG=str(config), FIXTURE_RECORD=str(record),
                   GH_TOKEN="fixture-token", GH_HOST="github.com")
        env.pop("HERDR_PLUGIN_CONFIG_DIR", None)
        for profile in ("local-review", "pr-review"):
            layout = tomllib.loads((SCRIPT.parent.parent / "projects" / f"{profile}.toml").read_text())
            commands = [pane["command"] for pane in layout["tabs"][0]["panes"]]
            commands.append(layout["tabs"][1]["command"])
            for index, command in enumerate(commands):
                with self.subTest(profile=profile, index=index):
                    result = subprocess.run(["fish", "--no-config", "-c", command],
                                            input="owner/repo#123\n", capture_output=True,
                                            text=True, env=env, cwd=self.repository)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    captured = json.loads(record.read_text())
                    if index != 1:
                        self.assertEqual(captured["argv"][0], "--append-system-prompt")
                        self.assertIn("Do not edit", captured["argv"][1])
                        self.assertEqual(len(captured["argv"]), 2)
                    elif profile == "local-review":
                        self.assertEqual(captured["argv"], ["diff", "--watch"])
                        self.assertEqual(captured["number"], "")
                    else:
                        self.assertEqual(captured["argv"], ["gh", "pr", "owner/repo#123"])
                        self.assertEqual(captured["number"], "123")
                        self.assertEqual(captured["repo"], "owner/repo")

    def test_repository_options_always_offer_directory_entry(self):
        for repositories in ([], [self.repository]):
            with self.subTest(repositories=repositories):
                output = io.StringIO()
                with patch.object(launcher, "list_repositories", return_value=repositories):
                    with contextlib.redirect_stdout(output):
                        self.assertEqual(launcher.main(["list-repositories"]), 0)
                lines = output.getvalue().splitlines()
                self.assertEqual(lines[0].split("\t", 1)[0], "Enter another directory...")
                self.assertIn("Tab", lines[0])
                self.assertEqual(len(lines), len(repositories) + 1)

    def test_directory_completion_handles_spaces_and_excludes_files(self):
        (self.base / "repo file").write_text("not a directory")
        text = str(self.base / "repo")
        self.assertEqual(launcher.directory_completions(text), [str(self.repository) + "/"])

    def test_directory_completion_uses_invoking_directory_for_relative_paths(self):
        self.assertEqual(launcher.directory_completions("../repo"), ["../repo with spaces/"])

    def test_directory_completion_preserves_tilde_and_literal_characters(self):
        with patch.dict(os.environ, {"HOME": str(self.base)}):
            self.assertEqual(launcher.directory_completions("~/repo"), ["~/repo with spaces/"])
        directory = self.base / 'repo "$HOME" [literal]'
        directory.mkdir()
        text = str(self.base / 'repo "$HOME" [')
        self.assertEqual(launcher.directory_completions(text), [str(directory) + "/"])
        self.assertEqual(launcher.directory_completions(str(self.base / "missing/")), [])

    def test_directory_prompt_accepts_a_path_without_shell_interpretation(self):
        with patch("builtins.input", return_value=str(self.repository)):
            with patch.object(launcher, "terminal_stdio", return_value=contextlib.nullcontext()):
                self.assertEqual(launcher.prompt_directory(), self.repository)

    def test_directory_prompt_configures_and_restores_completion(self):
        import readline
        original = readline.get_completer()
        delimiters = readline.get_completer_delims()
        with patch("builtins.input", return_value=""):
            with patch.object(launcher, "terminal_stdio", return_value=contextlib.nullcontext()):
                self.assertIsNone(launcher.prompt_directory())
        self.assertIs(readline.get_completer(), original)
        self.assertEqual(readline.get_completer_delims(), delimiters)

    def test_directory_entry_cancellation_does_not_open_any_workflow(self):
        for profile in ("implementation", "local-review", "pr-review"):
            for value in ("", "   ", EOFError(), KeyboardInterrupt()):
                with self.subTest(profile=profile, value=repr(value)):
                    options = {"side_effect": value} if isinstance(value, BaseException) else {"return_value": value}
                    with patch("builtins.input", **options), patch.object(launcher, "open_workflow") as open_workflow:
                        with patch.object(launcher, "terminal_stdio", return_value=contextlib.nullcontext()), contextlib.redirect_stdout(io.StringIO()):
                            self.assertEqual(launcher.main(["open", profile, "Enter another directory..."]), 0)
                        open_workflow.assert_not_called()

    def test_directory_entry_passes_the_selected_path_to_existing_launcher(self):
        with patch("builtins.input", return_value=str(self.repository)):
            with patch.object(launcher, "terminal_stdio", return_value=contextlib.nullcontext()), patch.object(launcher, "open_workflow", return_value="fixture") as open_workflow:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(launcher.main(["open", "implementation", "Enter another directory..."]), 0)
        open_workflow.assert_called_once_with("implementation", self.repository)

    def test_tab_completion_works_when_the_action_does_not_forward_stdin(self):
        record = self.base / "directory.json"
        code = '''import importlib.util, json, os, sys
spec = importlib.util.spec_from_file_location("directory_input", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with open(os.devnull) as file:
    os.dup2(file.fileno(), 0)
result = module.prompt_directory()
with open(sys.argv[2], "w") as file:
    json.dump(str(result) if result is not None else None, file)
'''
        for keys, expected in ((str(self.base / "repo").encode() + b"\t\n", str(self.repository)),
                               (b"\x03", None), (b"\x04", None)):
            with self.subTest(keys=keys):
                record.unlink(missing_ok=True)
                pid, terminal = pty.fork()
                if pid == 0:
                    os.execv(sys.executable, [sys.executable, "-c", code, str(SCRIPT), str(record)])
                try:
                    output = bytearray()
                    sent = False
                    deadline = time.monotonic() + 8
                    while time.monotonic() < deadline:
                        readable, _, _ = select.select([terminal], [], [], max(0, deadline - time.monotonic()))
                        if not readable:
                            break
                        try:
                            data = os.read(terminal, 4096)
                        except OSError:
                            break
                        if not data:
                            break
                        output.extend(data)
                        if not sent and b"empty cancels): " in output:
                            os.write(terminal, keys)
                            sent = True
                    self.assertTrue(sent, output.decode(errors="replace"))
                    self.assertTrue(record.exists(), output.decode(errors="replace"))
                    self.assertEqual(json.loads(record.read_text()), expected)
                finally:
                    os.close(terminal)
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    os.waitpid(pid, 0)

    def test_create_project_initializes_only_git_before_opening_implementation(self):
        directory = self.base / 'project with spaces "$HOME"; literal'

        def opened(profile, selected):
            self.assertEqual(profile, "implementation")
            self.assertEqual(selected, directory)
            self.assertEqual([child.name for child in directory.iterdir()], [".git"])
            self.assertEqual(launcher.repository_root(directory), directory)
            self.assertEqual(command_output(["git", "-C", str(directory), "remote"]), "")
            commits = subprocess.run(["git", "-C", str(directory), "rev-parse", "HEAD"], capture_output=True)
            self.assertNotEqual(commits.returncode, 0)
            return "created workspace"

        def command_output(argv):
            return subprocess.run(argv, check=True, capture_output=True, text=True).stdout

        with patch.object(launcher, "open_workflow", side_effect=opened) as open_workflow:
            self.assertEqual(launcher.create_project(directory), "created workspace")
        open_workflow.assert_called_once_with("implementation", directory)

    def test_create_project_respects_git_default_branch_and_relative_paths(self):
        directory = self.repository / "new local project"
        with patch.dict(os.environ, {
            "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "init.defaultBranch", "GIT_CONFIG_VALUE_0": "trunk",
        }), patch.object(launcher, "open_workflow", return_value="opened"):
            launcher.create_project(Path("new local project"))
        branch = subprocess.run(["git", "-C", str(directory), "symbolic-ref", "--short", "HEAD"],
                                check=True, capture_output=True, text=True).stdout.strip()
        self.assertEqual(branch, "trunk")

    def test_create_project_rejects_existing_paths_and_symlinks(self):
        empty = self.base / "existing empty directory"
        empty.mkdir()
        file = self.base / "existing file"
        file.write_text("preserve this")
        link = self.base / "existing link"
        link.symlink_to(empty, target_is_directory=True)
        broken = self.base / "broken link"
        broken.symlink_to(self.base / "absent target")
        for directory in (empty, file, self.repository, link, broken):
            with self.subTest(directory=directory):
                with patch.object(launcher, "open_workflow") as open_workflow:
                    with self.assertRaisesRegex(launcher.WorkflowError, "already exists"):
                        launcher.create_project(directory)
                open_workflow.assert_not_called()
        self.assertEqual(file.read_text(), "preserve this")
        self.assertEqual(list(empty.iterdir()), [])
        self.assertTrue(broken.is_symlink())
        self.assertFalse((self.base / "absent target").exists())

    def test_create_project_requires_an_existing_parent_and_safe_directory_name(self):
        for directory in (self.base / "missing parent/project", self.base / "bad\nname", self.base / "bad\tname"):
            with self.subTest(directory=directory):
                with self.assertRaises(launcher.WorkflowError):
                    launcher.create_project(directory)
                self.assertFalse(directory.exists())
        self.assertFalse((self.base / "missing parent").exists())

    def test_create_project_requires_herdr_and_git_before_creating_a_directory(self):
        directory = self.base / "not created"
        with patch.dict(os.environ, {"HERDR_ENV": ""}):
            with self.assertRaisesRegex(launcher.WorkflowError, "inside Herdr"):
                launcher.create_project(directory)
        with patch.object(launcher.shutil, "which", return_value=None):
            with self.assertRaisesRegex(launcher.WorkflowError, "Git"):
                launcher.create_project(directory)
        self.assertFalse(directory.exists())

    def test_failed_initialization_does_not_open_or_remove_the_directory(self):
        directory = self.base / "initialization failed"
        with patch.object(launcher, "command", side_effect=launcher.WorkflowError("git failed")):
            with patch.object(launcher, "open_workflow") as open_workflow:
                with self.assertRaisesRegex(launcher.WorkflowError, "initializ") as failure:
                    launcher.create_project(directory)
        self.assertIn(str(directory), str(failure.exception))
        self.assertTrue(directory.is_dir())
        open_workflow.assert_not_called()

    def test_failed_workspace_open_preserves_the_created_repository(self):
        directory = self.base / "workspace failed"
        with patch.object(launcher, "open_workflow", side_effect=launcher.WorkflowError("plugin failed")):
            with self.assertRaises(launcher.WorkflowError) as failure:
                launcher.create_project(directory)
        self.assertIn(str(directory), str(failure.exception))
        self.assertIn("plugin failed", str(failure.exception))
        self.assertEqual(launcher.repository_root(directory), directory)

    def test_create_project_action_and_cli_use_the_directory_prompt(self):
        action = tomllib.loads((SCRIPT.parent.parent / "quick-actions/create-project.toml").read_text())
        self.assertEqual(action["name"], "Create project")
        self.assertEqual(action["type"], "command")
        self.assertTrue(action["command"].endswith(" create-project"))
        directory = self.base / "selected project"
        with patch.object(launcher, "prompt_directory", return_value=directory) as prompt:
            with patch.object(launcher, "create_project", return_value="created") as create:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(launcher.main(["create-project"]), 0)
        self.assertIn("New project", prompt.call_args.args[0])
        create.assert_called_once_with(directory)

    def test_create_project_cancellation_does_not_create_any_directory(self):
        for value in ("", "   ", EOFError(), KeyboardInterrupt()):
            with self.subTest(value=repr(value)):
                options = {"side_effect": value} if isinstance(value, BaseException) else {"return_value": value}
                with patch("builtins.input", **options), patch.object(launcher, "create_project") as create:
                    with patch.object(launcher, "terminal_stdio", return_value=contextlib.nullcontext()):
                        self.assertEqual(launcher.main(["create-project"]), 0)
                create.assert_not_called()

    def test_cli_errors_are_captured_and_clear(self):
        output = io.StringIO()
        with patch.dict(os.environ, {"HERDR_ENV": "0"}), contextlib.redirect_stderr(output):
            self.assertEqual(launcher.main(["open", "implementation"]), 1)
        self.assertIn("inside Herdr", output.getvalue())


    def test_implementation_layout_opens_the_board_in_its_own_tab(self):
        layout = tomllib.loads(TEMPLATE)
        self.assertEqual([tab["name"] for tab in layout["tabs"]], ["implement", "claude", "board", "shell"])
        command = layout["tabs"][2]["command"]
        executables = self.base / "executables"
        executables.mkdir()
        root = self.base / 'plugin "$HOME"'
        herdr = executables / "herdr"
        herdr.write_text('#!/usr/bin/env python3\nimport json, os, sys\n'
                         'assert sys.argv[1:] == ["plugin", "list", "--plugin", "nulluminati.herdboard", "--json"]\n'
                         'print(json.dumps({"result": {"plugins": [{"plugin_root": os.environ["FIXTURE_ROOT"]}]}}))\n')
        uv = executables / "uv"
        uv.write_text('#!/usr/bin/env python3\nimport json, os, sys\n'
                      'json.dump(sys.argv[1:], open(os.environ["FIXTURE_RECORD"], "w"))\n')
        for executable in (herdr, uv):
            executable.chmod(0o755)
        record = self.base / "record.json"
        env = dict(os.environ, PATH=f"{executables}:{os.environ['PATH']}",
                   FIXTURE_ROOT=str(root), FIXTURE_RECORD=str(record))
        result = subprocess.run(["fish", "--no-config", "-c", command], capture_output=True,
                                text=True, env=env, cwd=self.repository)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(record.read_text()),
                         ["run", "--quiet", "--project", str(root), "herdboard", "board"])


if __name__ == "__main__":
    unittest.main()
