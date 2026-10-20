"""Offline adversarial tests for the local-only CLI and Git observation."""
import os
from contextlib import redirect_stderr, redirect_stdout
import io
import signal
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

from engineering_kit.cli import main
from engineering_kit.git_observe import ObservationError, _env, observe, _git


def local_git(directory, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
    p = subprocess.run(["git", "-C", str(directory), *args],
                       env=env, check=True, capture_output=True)
    return p.stdout.decode().strip()


class GitFixture(unittest.TestCase):
    def setUp(self):
        if os.name != "posix" or not shutil.which("git"):
            self.skipTest("Git observation requires POSIX and Git")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        local_git(self.root, "init", "-q")
        local_git(self.root, "config", "user.email", "synthetic@example.test")
        local_git(self.root, "config", "user.name", "Synthetic")
        (self.root / "data").write_text("old\n")
        local_git(self.root, "add", "data")
        local_git(self.root, "commit", "-qm", "fixture")

    def test_git_result_and_environment_read_only(self):
        (self.root / "untracked.txt").write_text("new\n")
        local_git(self.root, "config", "filter.untrusted.clean",
                  "sh -c 'echo called > FILTER_WAS_RUN; cat'")
        (self.root / ".gitattributes").write_text("data filter=untrusted\n")
        local_git(self.root, "add", ".gitattributes")
        (self.root / "data").write_text("edited\n")
        # Fixture setup may itself run its benign clean filter during git add;
        # remove setup evidence before the call under test.
        (self.root / "FILTER_WAS_RUN").unlink(missing_ok=True)
        with mock.patch("subprocess.Popen", wraps=subprocess.Popen) as popen:
            result = observe(self.root)
        self.assertEqual(result["staged_entry_count"], 1)
        self.assertGreaterEqual(result["untracked_entry_count"], 1)
        self.assertEqual(result["unstaged_tracked_changes"], "UNVERIFIED")
        self.assertFalse((self.root / "FILTER_WAS_RUN").exists())
        self.assertEqual(len(popen.call_args_list), 5)
        for call in popen.call_args_list:
            args = call.args[0]
            opts = call.kwargs
            self.assertEqual(opts["stderr"], subprocess.DEVNULL)
            self.assertTrue(opts["start_new_session"])
            self.assertEqual(opts["env"]["GIT_NO_LAZY_FETCH"], "1")
            self.assertEqual(opts["env"]["GIT_ALLOW_PROTOCOL"], "")
            self.assertEqual(opts["env"]["GIT_OPTIONAL_LOCKS"], "0")
            self.assertNotIn("status", args)
            self.assertNotIn("diff-files", args)
        self.assertNotIn("GIT_CONFIG_COUNT", _env())

    def test_missing_promisor_tree_cannot_lazy_fetch_or_run_uploadpack(self):
        tree = local_git(self.root, "rev-parse", "HEAD^{tree}")
        marker = self.root / "UPLOADPACK_EXECUTED"
        script = self.root / "uploadpack-fixture.sh"
        script.write_text("#!/bin/sh\nprintf executed > " + str(marker) + "\nexit 1\n")
        script.chmod(0o700)
        local_git(self.root, "config", "remote.origin.url", str(self.root))
        local_git(self.root, "config", "remote.origin.promisor", "true")
        local_git(self.root, "config", "remote.origin.partialclonefilter", "blob:none")
        local_git(self.root, "config", "extensions.partialClone", "origin")
        local_git(self.root, "config", "remote.origin.uploadpack", str(script))
        obj = self.root / ".git" / "objects" / tree[:2] / tree[2:]
        self.assertTrue(obj.is_file())
        obj.unlink()
        with self.assertRaises(ObservationError):
            observe(self.root)
        self.assertFalse(marker.exists(), "Git ran untrusted uploadpack")

    def test_large_untracked_output_aborts_with_bounded_reads(self):
        for i in range(1800):
            (self.root / ("test_" + str(i) + "_" + ("a" * 80))).write_text("")
        with self.assertRaisesRegex(ObservationError, "bounded limit"):
            observe(self.root)

    def test_timeout_kills_git_process_group_and_child(self):
        # A fake fixed Git executable creates a descendant that holds stdout.
        # The descendant must not survive when the bounded call times out.
        parent = self.root / "fakegit.py"
        spawned = self.root / "spawned.pid"
        marker = self.root / "CHILD_SURVIVED"
        child_code = "import time,pathlib;time.sleep(0.65);pathlib.Path(" + repr(str(marker)) + ").write_text('unsafe')"
        parent.write_text(
            "#!" + sys.executable + "\n"
            "import subprocess,sys,time,pathlib\n"
            "p=subprocess.Popen([sys.executable,'-c'," + repr(child_code) + "],stdout=sys.stdout)\n"
            "pathlib.Path(" + repr(str(spawned)) + ").write_text(str(p.pid))\n"
            "time.sleep(60)\n")
        parent.chmod(0o700)
        try:
            with mock.patch("engineering_kit.git_observe.SECONDS", 0.16):
                with self.assertRaisesRegex(ObservationError, "timed out"):
                    _git(str(parent), self.root, ["rev-parse", "--show-toplevel"])
            self.assertTrue(spawned.is_file(), "fixture did not spawn child")
            child_pid = int(spawned.read_text())
            # Linux may keep a dead process as an orphan zombie briefly.
            # Alive running/sleeping descendants are unacceptable.
            def is_live(pid):
                path = Path("/proc") / str(pid) / "stat"
                if path.is_file():
                    return path.read_text().split(") ", 1)[1][0] != "Z"
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    return False
                return True
            time.sleep(0.04)
            self.assertFalse(is_live(child_pid), "Git descendant is still running")
            time.sleep(0.7)
            self.assertFalse(marker.exists(), "Git descendant performed post-timeout work")
        finally:
            if spawned.exists():
                try:
                    os.kill(int(spawned.read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_git_error_never_logs_stderr(self):
        marker = self.root / "fake-git.sh"
        marker.write_text("#!/bin/sh\necho 'PRIVATE_TOKEN' >&2\nexit 1\n")
        marker.chmod(0o700)
        with mock.patch("shutil.which", return_value=str(marker)):
            with self.assertRaises(ObservationError) as error:
                observe(self.root)
        self.assertNotIn("PRIVATE_TOKEN", str(error.exception))

    def test_non_repository_returns_controlled_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ObservationError, "metadata command failed"):
                observe(Path(directory))


class CliTests(unittest.TestCase):
    def test_offline_commands_never_spawn_or_open_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "README.md").write_text("synthetic")
            with mock.patch("subprocess.Popen", side_effect=AssertionError("spawn")), \
                 mock.patch("socket.socket", side_effect=AssertionError("network")), \
                 mock.patch("socket.create_connection", side_effect=AssertionError("network")), \
                 mock.patch("signal.signal", side_effect=AssertionError("handler mutation")), \
                 mock.patch("signal.setitimer", create=True, side_effect=AssertionError("timer mutation")):
                self.assertEqual(main(["doctor"]), 0)
                self.assertEqual(main(["context", "--root", tmp]), 0)
                self.assertEqual(main(["checks", "--profile", "rustcraft"]), 0)
                self.assertEqual(main(["checks", "--profile", "unknown"]), 1)

    def test_unavailable_git_is_not_installed(self):
        with mock.patch("shutil.which", return_value=None):
            with self.assertRaisesRegex(ObservationError, "unavailable"):
                observe(Path("/tmp"))

    def test_removed_github_get_is_rejected_without_side_effects(self):
        for resource, identifier in (("issue", "7"), ("commit", "a" * 40),
                                     ("pr", "../secret"), ("run", "0")):
            with self.subTest(resource=resource), \
                 mock.patch("subprocess.Popen", side_effect=AssertionError("spawn")), \
                 mock.patch("socket.socket", side_effect=AssertionError("network")), \
                 mock.patch("signal.signal", side_effect=AssertionError("handler mutation")), \
                 mock.patch("signal.setitimer", create=True, side_effect=AssertionError("timer mutation")), \
                 redirect_stdout(io.StringIO()) as output, \
                 redirect_stderr(io.StringIO()) as errors:
                with self.assertRaises(SystemExit) as result:
                    main(["github-get", resource, "owner/repo", identifier])
                self.assertEqual(result.exception.code, 2)
                self.assertEqual(output.getvalue(), "")
                self.assertIn("invalid choice", errors.getvalue())

    def test_help_exposes_only_local_commands(self):
        with redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(SystemExit) as result:
                main(["--help"])
        self.assertEqual(result.exception.code, 0)
        self.assertIn("{status,context,doctor,checks,bundle,sync}", output.getvalue())
        self.assertNotIn("github-get", output.getvalue())


if __name__ == "__main__":
    unittest.main()
