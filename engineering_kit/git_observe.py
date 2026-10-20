"""Bounded, read-only Git metadata. Never runs repo-supplied commands."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess

LIMIT = 128 * 1024


class ObservationError(ValueError):
    pass


def _env() -> dict[str, str]:
    # Drop Git's externally injected options/config/working-tree overrides.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_LFS_SKIP_SMUDGE": "1",
    })
    return env


def _git(executable: str, root: Path, args: list[str], detached_ok: bool = False) -> bytes:
    command = [executable, "--no-optional-locks",
               "-c", "core.fsmonitor=false",
               "-c", "core.untrackedCache=false",
               "-c", "maintenance.auto=false",
               "-c", "gc.auto=0",
               "-c", "core.hooksPath=" + os.devnull,
               "-C", str(root), *args]
    try:
        proc = subprocess.run(command, stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=10, env=_env(), check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ObservationError("git observation unavailable") from exc
    if detached_ok and proc.returncode == 1:
        return b""
    if proc.returncode != 0:
        raise ObservationError("git metadata command failed")
    if len(proc.stdout) > LIMIT or len(proc.stderr) > LIMIT:
        raise ObservationError("git output exceeds bounded limit")
    return proc.stdout


def observe(root: Path) -> dict[str, object]:
    """Explicit status only: no fetch, hooks, checkout or index write."""
    executable = shutil.which("git")
    if executable is None:
        raise ObservationError("git is unavailable; no installation attempted")
    root = Path(root).absolute()
    if not root.is_dir():
        raise ObservationError("repository directory unavailable")
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

    # Deliberately never call git status, diff-files, ls-files --modified,
    # or any content-comparing working-tree command. Those can invoke
    # repository-controlled filter.*.clean commands despite disabled hooks.
    # The staged comparison uses HEAD/index only; untracked listing only
    # reads paths and ignores. Unstaged tracked changes are UNVERIFIED.
    staged_data = _git(executable, root,
                       ["diff-index", "--cached", "--name-only", "-z", "HEAD", "--"])
    untracked_data = _git(executable, root,
                          ["ls-files", "-z", "--others", "--exclude-standard"])
    staged = sum(bool(item) for item in staged_data.split(b"\0"))
    untracked = sum(bool(item) for item in untracked_data.split(b"\0"))
    return {
        "repo_root": actual,
        "head_sha": sha,
        "branch": branch or None,
        "detached": not bool(branch),
        "staged_entry_count": staged,
        "untracked_entry_count": untracked,
        "known_pending_changes": bool(staged or untracked),
        "unstaged_tracked_changes": "UNVERIFIED",
        "note": "No working-tree content inspection or repository filter execution",
    }
