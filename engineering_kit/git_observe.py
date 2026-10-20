"""Bounded, read-only Git metadata. No hooks, filters, lazy fetch or transport."""
from __future__ import annotations

import os
from pathlib import Path
import re
import select
import shutil
import subprocess
import time

LIMIT = 128 * 1024
SECONDS = 10


class ObservationError(ValueError):
    pass


def _env() -> dict[str, str]:
    # Never allow inherited Git configuration, transport or implicit promisor
    # fetch. These are necessary even for apparently read-only Git commands.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_ALLOW_PROTOCOL": "",  # no local, ssh, http or helper transport
        "GIT_PROTOCOL_FROM_USER": "0",
        "GIT_LFS_SKIP_SMUDGE": "1",
    })
    return env


def _git(executable: str, root: Path, args: list[str], detached_ok: bool = False) -> bytes:
    """Capture at most LIMIT+1 bytes; discard stderr without buffering.

    POSIX pipe select is required here. Unsupported hosts fail closed.
    """
    if os.name != "posix":
        raise ObservationError("bounded Git observation unsupported on this platform")
    command = [executable, "--no-optional-locks",
               "-c", "core.fsmonitor=false",
               "-c", "core.untrackedCache=false",
               "-c", "maintenance.auto=false",
               "-c", "gc.auto=0",
               "-c", "core.hooksPath=" + os.devnull,
               "-C", str(root), *args]
    proc = None
    try:
        proc = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                env=_env(), close_fds=True, start_new_session=True)
        deadline = time.monotonic() + SECONDS
        data = bytearray()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ObservationError("git observation timed out")
            ready, _, _ = select.select([proc.stdout], [], [], remaining)
            if not ready:
                raise ObservationError("git observation timed out")
            chunk = os.read(proc.stdout.fileno(), min(65536, LIMIT + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > LIMIT:
                raise ObservationError("git output exceeds bounded limit")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ObservationError("git observation timed out")
        try:
            code = proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired as exc:
            raise ObservationError("git observation timed out") from exc
        if detached_ok and code == 1:
            return b""
        if code:
            raise ObservationError("git metadata command failed")
        return bytes(data)
    except (OSError, ValueError) as exc:
        if isinstance(exc, ObservationError):
            raise
        raise ObservationError("git observation unavailable") from exc
    finally:
        if proc is not None:
            if proc.poll() is None:
                proc.kill()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                raise ObservationError("git subprocess could not be reaped")
            if proc.stdout is not None:
                proc.stdout.close()


def observe(root: Path) -> dict[str, object]:
    """Observe bounded metadata only; absence of objects => controlled failure."""
    executable = shutil.which("git")
    if executable is None:
        raise ObservationError("git is unavailable; no installation attempted")
    root = Path(root).absolute()
    if not root.is_dir():
        raise ObservationError("repository directory unavailable")
    try:
        actual = _git(executable, root, ["rev-parse", "--show-toplevel"]).decode(
            "utf-8", errors="strict").strip()
        if not actual:
            raise ObservationError("unable to determine repository root")
        sha = _git(executable, root, ["rev-parse", "--verify", "HEAD"]).decode(
            "ascii", errors="strict").strip()
        if not re.fullmatch(r"[0-9a-f]{40,64}", sha):
            raise ObservationError("Git HEAD is not a complete SHA")
        branch = _git(executable, root, ["symbolic-ref", "-q", "--short", "HEAD"],
                      detached_ok=True).decode("utf-8", errors="replace").strip()
        # No status/diff-files/--modified: those may invoke clean filters.
        # No implicit fetch of missing HEAD objects is permitted.
        staged_data = _git(executable, root,
                           ["diff-index", "--cached", "--name-only", "-z", "HEAD", "--"])
        untracked_data = _git(executable, root,
                              ["ls-files", "-z", "--others", "--exclude-standard"])
    except UnicodeError as exc:
        raise ObservationError("Git metadata encoding invalid") from exc
    staged = sum(bool(item) for item in staged_data.split(b"\0"))
    untracked = sum(bool(item) for item in untracked_data.split(b"\0"))
    return {"repo_root": actual, "head_sha": sha,
            "branch": branch or None, "detached": not bool(branch),
            "staged_entry_count": staged, "untracked_entry_count": untracked,
            "known_pending_changes": bool(staged or untracked),
            "unstaged_tracked_changes": "UNVERIFIED",
            "note": "No working-tree content inspection, filter or Git transport"}
