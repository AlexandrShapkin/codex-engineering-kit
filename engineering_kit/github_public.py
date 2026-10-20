"""Explicit anonymous HTTPS GET for public GitHub metadata. Fixed host only."""
from __future__ import annotations

import http.client
import json
import re
import os
import signal
import threading
from contextlib import contextmanager
import time

MAX_BYTES = 64 * 1024
MAX_SECONDS = 10
HOST = "api.github.com"
REPO_RE = re.compile(r"[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}\Z")
SHA_RE = re.compile(r"[0-9a-fA-F]{40,64}\Z")


class GithubReadError(ValueError):
    pass


def _remaining(deadline: float) -> float:
    seconds = deadline - time.monotonic()
    if seconds <= 0:
        raise GithubReadError("GitHub request exceeded overall deadline")
    return seconds



@contextmanager
def _hard_deadline(seconds: float):
    """Interrupt HTTP internals, including readline() for chunk sizes/headers.

    SIGALRM is process-global, so this bounded CLI transport only works in the
    POSIX main thread and refuses to disturb any existing application alarm.
    Never silently fall back to per-socket idle timeouts.
    """
    if (os.name != "posix" or not hasattr(signal, "setitimer")
            or threading.current_thread() is not threading.main_thread()):
        raise GithubReadError("hard HTTPS deadline unsupported on this platform/thread")
    try:
        current = signal.getitimer(signal.ITIMER_REAL)
        previous = signal.getsignal(signal.SIGALRM)
    except (OSError, ValueError) as exc:
        raise GithubReadError("cannot establish hard HTTPS deadline") from exc
    if current != (0.0, 0.0):
        raise GithubReadError("existing process alarm prevents safe HTTPS deadline")

    def interrupt(signum, frame):
        raise GithubReadError("GitHub request exceeded overall deadline")

    signal.signal(signal.SIGALRM, interrupt)
    try:
        signal.setitimer(signal.ITIMER_REAL, max(0.000001, seconds))
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)

def _read_json(path: str) -> dict[str, object]:
    """Hard POSIX timer interrupts header/chunk parsing at one shared deadline.

    http.client uses a fixed TLS host, no env proxies, redirects, cookies or
    automatic credentials. Non-main-thread/non-POSIX callers fail closed.
    """
    deadline = time.monotonic() + MAX_SECONDS
    with _hard_deadline(MAX_SECONDS):
        conn = None
        try:
            conn = http.client.HTTPSConnection(HOST, timeout=_remaining(deadline))
            conn.request("GET", path, headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "codex-engineering-kit/0.1",
            })
            _remaining(deadline)
            response = conn.getresponse()
            _remaining(deadline)
            if response.status != 200:
                if 300 <= response.status < 400:
                    raise GithubReadError("GitHub redirect refused")
                raise GithubReadError("GitHub request unsuccessful")
            if "json" not in response.getheader("Content-Type", "").lower():
                raise GithubReadError("non-JSON GitHub response")
            content_length = response.getheader("Content-Length")
            if content_length is not None and content_length.isdecimal() and int(content_length) > MAX_BYTES:
                raise GithubReadError("GitHub response too large")
            body = bytearray()
            # HTTPResponse may own the socket after will_close; refreshing its
            # timeout before each read stops slow-drip responses at the deadline.
            socket = conn.sock
            if socket is None:
                stream = response.fp
                socket = getattr(getattr(stream, "raw", None), "_sock", None)
            if socket is None or not hasattr(socket, "settimeout"):
                raise GithubReadError("cannot enforce socket deadline safely")
            while True:
                socket.settimeout(_remaining(deadline))
                chunk = response.read1(min(8192, MAX_BYTES + 1 - len(body)))
                _remaining(deadline)
                if not chunk:
                    break
                body.extend(chunk)
                if len(body) > MAX_BYTES:
                    raise GithubReadError("GitHub response too large")
            try:
                item = json.loads(body)
            except (ValueError, UnicodeError, RecursionError) as exc:
                raise GithubReadError("invalid or excessively nested GitHub JSON") from exc
            if not isinstance(item, dict):
                raise GithubReadError("unexpected GitHub response shape")
            return item
        except GithubReadError:
            raise
        except (http.client.HTTPException, OSError, ValueError, RecursionError) as exc:
            raise GithubReadError("public GitHub GET failed or response malformed") from exc
        finally:
            if conn is not None:
                conn.close()


def get_public(repo: str, resource: str, identifier: str) -> dict[str, object]:
    if not REPO_RE.fullmatch(repo) or ".." in repo.split("/"):
        raise GithubReadError("invalid repository name")
    if resource not in ("issue", "pr", "run", "commit"):
        raise GithubReadError("unsupported GitHub resource")
    if resource == "commit":
        if not SHA_RE.fullmatch(identifier):
            raise GithubReadError("expected complete Git commit SHA")
        fragment = "commits/" + identifier.lower()
    else:
        if not re.fullmatch(r"[1-9][0-9]{0,11}", identifier):
            raise GithubReadError("expected bounded positive numeric identifier")
        fragment = {"issue": "issues/", "pr": "pulls/",
                    "run": "actions/runs/"}[resource] + identifier
    item = _read_json("/repos/" + repo + "/" + fragment)
    public_link = "https://github.com/" + repo
    if resource in ("issue", "pr"):
        expected = int(identifier)
        if item.get("number") != expected:
            raise GithubReadError("GitHub identity mismatch")
        return {"resource": resource, "repo": repo, "number": expected,
                "state": str(item.get("state", ""))[:32],
                "title": str(item.get("title", ""))[:300],
                "url": public_link + ("/issues/" if resource == "issue"
                                      else "/pull/") + identifier}
    if resource == "run":
        if item.get("id") != int(identifier):
            raise GithubReadError("GitHub identity mismatch")
        return {"resource": resource, "repo": repo, "id": int(identifier),
                "status": str(item.get("status", ""))[:32],
                "conclusion": str(item.get("conclusion", ""))[:32],
                "head_sha": str(item.get("head_sha", ""))[:64],
                "url": public_link + "/actions/runs/" + identifier}
    actual = str(item.get("sha", ""))
    if actual.lower() != identifier.lower():
        raise GithubReadError("GitHub identity mismatch")
    return {"resource": resource, "repo": repo, "sha": actual.lower(),
            "url": public_link + "/commit/" + actual.lower()}
