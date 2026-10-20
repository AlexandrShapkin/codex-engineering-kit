"""Offline adversarial tests for Git observation and fixed-host GitHub GET."""
import http.client
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

from engineering_kit.cli import main
from engineering_kit.git_observe import ObservationError, _env, observe
from engineering_kit.github_public import GithubReadError, get_public


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

    def test_git_error_never_logs_stderr(self):
        marker = self.root / "fake-git.sh"
        marker.write_text("#!/bin/sh\necho 'PRIVATE_TOKEN' >&2\nexit 1\n")
        marker.chmod(0o700)
        with mock.patch("shutil.which", return_value=str(marker)):
            with self.assertRaises(ObservationError) as error:
                observe(self.root)
        self.assertNotIn("PRIVATE_TOKEN", str(error.exception))


class CliTests(unittest.TestCase):
    def test_offline_commands_never_spawn_or_open_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "README.md").write_text("synthetic")
            with mock.patch("subprocess.Popen", side_effect=AssertionError("spawn")), \
                 mock.patch("http.client.HTTPSConnection", side_effect=AssertionError("network")):
                self.assertEqual(main(["doctor"]), 0)
                self.assertEqual(main(["context", "--root", tmp]), 0)
                self.assertEqual(main(["checks", "--profile", "rustcraft"]), 0)
                self.assertEqual(main(["checks", "--profile", "unknown"]), 1)

    def test_unavailable_git_is_not_installed(self):
        with mock.patch("shutil.which", return_value=None):
            with self.assertRaisesRegex(ObservationError, "unavailable"):
                observe(Path("/tmp"))

    def test_invalid_github_identifiers_do_not_contact_network(self):
        bad = [("issue", "../secrets"), ("run", "0"),
               ("commit", "main"), ("pr", "100000000000000000")]
        with mock.patch("http.client.HTTPSConnection", side_effect=AssertionError("network")):
            for resource, identifier in bad:
                with self.subTest(resource=resource, identifier=identifier):
                    with self.assertRaises(GithubReadError):
                        get_public("owner/repo", resource, identifier)
            with self.assertRaises(GithubReadError):
                get_public("owner/../repo", "issue", "1")


class HttpTests(unittest.TestCase):
    def fake_connection(self, body=b'{"number":7,"state":"open","title":"example"}',
                        status=200, content_type="application/json"):
        response = mock.Mock()
        response.status = status
        response.getheader.side_effect = lambda n, d=None: (
            content_type if n == "Content-Type" else d)
        response.read1.side_effect = [body, b""]
        connection = mock.Mock()
        connection.sock = mock.Mock()
        connection.getresponse.return_value = response
        return connection, response

    def test_exact_host_get_no_auth_proxy_redirect(self):
        conn, resp = self.fake_connection()
        with mock.patch("http.client.HTTPSConnection", return_value=conn) as ctor:
            item = get_public("owner/repo", "issue", "7")
        self.assertEqual(item["number"], 7)
        self.assertEqual(ctor.call_args.args[0], "api.github.com")
        self.assertLessEqual(ctor.call_args.kwargs["timeout"], 10)
        self.assertEqual(conn.request.call_args.args[:2],
                         ("GET", "/repos/owner/repo/issues/7"))
        self.assertNotIn("Authorization", conn.request.call_args.kwargs["headers"])
        conn.close.assert_called_once()

    def test_identity_mismatch_rejected(self):
        conn, _ = self.fake_connection(body=b'{"number":8}')
        with mock.patch("http.client.HTTPSConnection", return_value=conn):
            with self.assertRaisesRegex(GithubReadError, "mismatch"):
                get_public("owner/repo", "issue", "7")

    def test_redirect_rejected(self):
        conn, _ = self.fake_connection(status=302)
        with mock.patch("http.client.HTTPSConnection", return_value=conn):
            with self.assertRaisesRegex(GithubReadError, "redirect"):
                get_public("owner/repo", "issue", "7")

    def test_oversize_response_rejected(self):
        conn, _ = self.fake_connection(body=b"a" * (64 * 1024 + 1))
        with mock.patch("http.client.HTTPSConnection", return_value=conn):
            with self.assertRaisesRegex(GithubReadError, "too large"):
                get_public("owner/repo", "issue", "7")

    def test_slow_chunk_overall_deadline_not_individual_socket_timeout(self):
        conn, resp = self.fake_connection()
        def slow_read(*args):
            time.sleep(0.055)
            return b'{"number":7}'
        resp.read1.side_effect = slow_read
        with mock.patch("engineering_kit.github_public.MAX_SECONDS", 0.03), \
             mock.patch("http.client.HTTPSConnection", return_value=conn):
            with self.assertRaisesRegex(GithubReadError, "deadline"):
                get_public("owner/repo", "issue", "7")
        conn.close.assert_called_once()

    def test_real_truncated_chunked_http_response_converted(self):
        left, right = socket.socketpair()
        self.addCleanup(left.close)
        self.addCleanup(right.close)
        right.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                      b"Transfer-Encoding: chunked\r\n\r\n"
                      b"20\r\n{\"number\":7}")
        right.shutdown(socket.SHUT_WR)
        response = http.client.HTTPResponse(left)
        response.begin()
        conn = mock.Mock(sock=left)
        conn.getresponse.return_value = response
        with mock.patch("http.client.HTTPSConnection", return_value=conn):
            with self.assertRaises(GithubReadError):
                get_public("owner/repo", "issue", "7")

    def test_extremely_deep_json_caught(self):
        deep = b'{"number":7,"data":' + b"[" * 10000 + b"0" + b"]" * 10000 + b"}"
        conn, resp = self.fake_connection(body=deep)
        with mock.patch("http.client.HTTPSConnection", return_value=conn):
            with self.assertRaisesRegex(GithubReadError, "nested"):
                get_public("owner/repo", "issue", "7")

    def test_unsupported_response_socket_refused(self):
        conn, resp = self.fake_connection()
        conn.sock = None
        resp.fp = None
        with mock.patch("http.client.HTTPSConnection", return_value=conn):
            with self.assertRaisesRegex(GithubReadError, "enforce socket"):
                get_public("owner/repo", "issue", "7")


if __name__ == "__main__":
    unittest.main()
