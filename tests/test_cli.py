"""CLI offline behavior, bounded Git observation and explicit GitHub GET tests."""
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from engineering_kit.cli import main
from engineering_kit.git_observe import ObservationError, observe
from engineering_kit.github_public import GithubReadError, get_public


class CliTests(unittest.TestCase):
    def test_doctor_does_not_spawn_or_network(self):
        with mock.patch("subprocess.run", side_effect=AssertionError("subprocess")), \
             mock.patch("urllib.request.build_opener",
                        side_effect=AssertionError("network")):
            self.assertEqual(main(["doctor"]), 0)

    def test_context_lists_only_existing_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("test")
            with mock.patch("subprocess.run", side_effect=AssertionError("subprocess")):
                self.assertEqual(main(["context", "--root", tmp]), 0)

    def test_checks_cannot_run_native_commands(self):
        with mock.patch("subprocess.run", side_effect=AssertionError("subprocess")):
            self.assertEqual(main(["checks", "--profile", "rustcraft"]), 0)
            self.assertEqual(main(["checks", "--profile", "unknown"]), 1)

    def test_observation_fixed_argv_and_git_environment(self):
        sha = "0" * 40
        responses = iter([sha.encode() + b"\n", b"main\n", b" M file.txt\0?? foo.txt\0"])
        calls = []
        def runner(args, **kwargs):
            calls.append((args, kwargs))
            if args[-2:] == ["rev-parse", "--show-toplevel"]:
                return subprocess.CompletedProcess(args, 0, b"/tmp\n", b"")
            return subprocess.CompletedProcess(args, 0, next(responses), b"")
        with mock.patch("shutil.which", return_value="/usr/bin/git"), \
             mock.patch("subprocess.run", side_effect=runner):
            result = observe(Path("/tmp"))
        self.assertEqual(result["dirty_entry_count"], 2)
        self.assertEqual(result["head_sha"], sha)
        self.assertEqual(len(calls), 4)
        for args, kwargs in calls:
            self.assertEqual(args[0], "/usr/bin/git")
            self.assertIn("--no-optional-locks", args)
            self.assertEqual(kwargs["env"]["GIT_OPTIONAL_LOCKS"], "0")
            self.assertFalse(kwargs["shell"] if "shell" in kwargs else False)
            self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)

    def test_unavailable_git_is_not_installed(self):
        with mock.patch("shutil.which", return_value=None):
            with self.assertRaisesRegex(ObservationError, "unavailable"):
                observe(Path("/tmp"))

    def test_invalid_github_identifiers_never_open_network(self):
        pairs = [("issue", "../secrets"), ("run", "0"),
                 ("commit", "main"), ("pr", "100000000000000000")]
        with mock.patch("urllib.request.build_opener",
                        side_effect=AssertionError("network")):
            for kind, identifier in pairs:
                with self.subTest(kind=kind, value=identifier), \
                     self.assertRaises(GithubReadError):
                    get_public("owner/repo", kind, identifier)
            with self.assertRaises(GithubReadError):
                get_public("owner/../repo", "issue", "1")

    def test_explicit_request_uses_no_proxy_or_auth(self):
        response = mock.MagicMock()
        response.status = 200
        response.headers = {"Content-Type": "application/json"}
        response.read.return_value = b'{"number":7,"state":"open","title":"sample"}'
        opener = mock.MagicMock()
        opener.open.return_value.__enter__.return_value = response
        with mock.patch("urllib.request.build_opener", return_value=opener) as factory:
            item = get_public("owner/repo", "issue", "7")
        self.assertEqual(item["number"], 7)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.full_url, "https://api.github.com/repos/owner/repo/issues/7")
        self.assertNotIn("Authorization", request.headers)
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 10)
        self.assertEqual(len(factory.call_args.args), 2)

    def test_github_identity_mismatch_rejected(self):
        response = mock.MagicMock()
        response.status = 200
        response.headers = {"Content-Type": "application/json"}
        response.read.return_value = b'{"number":8}'
        opener = mock.MagicMock()
        opener.open.return_value.__enter__.return_value = response
        with mock.patch("urllib.request.build_opener", return_value=opener):
            with self.assertRaisesRegex(GithubReadError, "mismatch"):
                get_public("owner/repo", "issue", "7")

    def test_github_response_bounded(self):
        response = mock.MagicMock()
        response.status = 200
        response.headers = {"Content-Type": "application/json"}
        response.read.return_value = b"z" * (64 * 1024 + 1)
        opener = mock.MagicMock()
        opener.open.return_value.__enter__.return_value = response
        with mock.patch("urllib.request.build_opener", return_value=opener):
            with self.assertRaisesRegex(GithubReadError, "too large"):
                get_public("owner/repo", "issue", "7")

    def test_no_redirect_is_allowed(self):
        from engineering_kit.github_public import _NoRedirect
        with self.assertRaisesRegex(GithubReadError, "redirect"):
            _NoRedirect().redirect_request(None, None, 302, "", {}, "https://elsewhere/")

    def test_git_command_failure_has_no_stderr_leak(self):
        def bad(*args, **kwargs):
            return subprocess.CompletedProcess([], 128, b"", b"SECRET TOKEN")
        with mock.patch("shutil.which", return_value="/usr/bin/git"), \
             mock.patch("subprocess.run", side_effect=bad):
            with self.assertRaisesRegex(ObservationError, "failed") as err:
                observe(Path("/tmp"))
        self.assertNotIn("SECRET", str(err.exception))


if __name__ == "__main__":
    unittest.main()
