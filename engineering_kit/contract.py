"""Portable offline agent-contract validation. No subprocess, network or writes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat

ROOT = Path(__file__).absolute().parent.parent
START = "<!-- shared-agent:start -->\n"
END = "<!-- shared-agent:end -->"
LIMIT = 256 * 1024
SECTIONS = (
    "1. Purpose and authority", "2. Repository start (START)",
    "3. GitHub task (TASK)", "4. Necessary context (CONTEXT)",
    "5. Planning and implementation (IMPLEMENT)",
    "6. Verification and quality (VERIFY)",
    "7. PR, CI, review and acceptance (PR / REVIEW)",
    "8. Temporary resources (CLEANUP)", "9. Final evidence (REPORT)",
    "10. Product-specific rules",
)


class ContractError(ValueError):
    pass


# Review-pinned SHA-256 of the four Draft consumers' baseline product gates.
# Updating the data file requires a deliberate new pin and independent review.
PROFILE_BASELINE_SHA256 = "46a354e82dda850cd874b9c92f4dd76687b8071b110bd6cb652af6ed69189504"

# Exact approved restrictions are separate from changeable profile keywords.
# They cannot be satisfied by merely mentioning the PR number or native command.
CRITICAL_INVARIANTS = {
    "codex-smart": (
        "PR #125 is prohibited from merge; PR #164 remains\n"
        "experimental and must not be activated.",
    ),
    "relayforge": (
        "Do not change runtime, grants, services,\nlauncher or binaries.",
        "All permitted local Cargo checks require explicit isolated\n"
        "`CARGO_TARGET_DIR`.",
    ),
    "assistant-hub": (
        "The current task authorizes Draft PRs only; historical standing merge language\n"
        "below does not authorize merging these changes or any runtime operation.",
    ),
    "rustcraft": (
        "Full native gate: `just ci`,\n"
        "plus mandatory GitHub CI on Ubuntu and Windows. Smoke alone is insufficient.",
    ),
}


def read(root: Path, rel: str) -> str:
    """Bounded file read via pinned no-follow descriptors for every component.

    Fail closed on unsupported platforms. No stat(path) / reopen race is used.
    """
    import os

    target = Path(rel)
    directory = Path(root)
    if (not rel or target.is_absolute() or ".." in target.parts
            or ".." in directory.parts):
        raise ContractError("unsafe relative path or root")
    if not directory.is_absolute():
        directory = Path.cwd() / directory
    if (os.name != "posix" or directory.anchor != "/"
            or not all(hasattr(os, name)
                       for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK"))
            or os.open not in os.supports_dir_fd):
        raise ContractError("no-follow descriptor reads unsupported on this platform")

    parts = (directory / target).parts[1:]
    directory_fd = None
    file_fd = None
    try:
        directory_fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        for part in parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                              dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                          dir_fd=directory_fd)
        initial = os.fstat(file_fd)
        if not stat.S_ISREG(initial.st_mode) or initial.st_size > LIMIT:
            raise ContractError("invalid or oversized file")
        chunks = []
        length = 0
        while length <= LIMIT:
            chunk = os.read(file_fd, min(65536, LIMIT + 1 - length))
            if not chunk:
                break
            chunks.append(chunk)
            length += len(chunk)
        if length > LIMIT:
            raise ContractError("oversized file")
        final = os.fstat(file_fd)
        if ((initial.st_size, initial.st_mtime_ns, initial.st_ctime_ns)
                != (final.st_size, final.st_mtime_ns, final.st_ctime_ns)):
            raise ContractError("contract file changed during read")
        return b"".join(chunks).decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise ContractError("unsafe, symlinked or unavailable contract file") from exc
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if directory_fd is not None:
            os.close(directory_fd)


def block(text: str) -> tuple[str, str]:
    if text.count(START) != 1 or text.count(END) != 1:
        raise ContractError("missing or duplicated shared markers")
    if text.index(END) < text.index(START) + len(START):
        raise ContractError("shared markers in wrong order")
    value = text.split(START, 1)[1]
    body, tail = value.split(END, 1)
    if not body.startswith("# Agent engineering contract\n"):
        raise ContractError("unexpected shared header")
    return body, tail


def canonical() -> tuple[str, str]:
    source = read(ROOT, "contract/AGENT_COMMON.md")
    interface = read(ROOT, "contract/DEVELOPMENT_INTERFACE.md")
    if not source.startswith(START) or not source.endswith(END + "\n"):
        raise ContractError("canonical boundaries changed")
    agent, tail = block(source)
    documented, _ = block(interface)
    if agent != documented or tail != "\n":
        raise ContractError("canonical fragment/interface drift")
    headings = tuple(line[3:] for line in agent.splitlines() if line.startswith("## "))
    if headings != SECTIONS:
        raise ContractError("required shared headings changed")
    if "[.github/DEVELOPMENT_INTERFACE.md](.github/DEVELOPMENT_INTERFACE.md)" not in agent:
        raise ContractError("missing interface link")
    return agent, interface


def requirements() -> dict[str, tuple[str, ...]]:
    text = read(ROOT, "profiles/products.json")
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != PROFILE_BASELINE_SHA256:
        raise ContractError("review-pinned baseline profile drift")
    try:
        def unique(pairs):
            obj = {}
            for key, value in pairs:
                if key in obj:
                    raise ContractError("duplicate profile key")
                obj[key] = value
            return obj
        obj = json.loads(text, object_pairs_hook=unique)
    except (ValueError, TypeError) as exc:
        raise ContractError("invalid profile JSON") from exc
    if (not isinstance(obj, dict) or set(obj) != {"schema_version", "required"}
            or type(obj["schema_version"]) is not int or obj["schema_version"] != 1
            or not isinstance(obj["required"], dict)):
        raise ContractError("invalid profile format")
    profiles = {}
    for name, items in obj["required"].items():
        if (not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", name)
                or not isinstance(items, list) or not 1 <= len(items) <= 40
                or any(not isinstance(s, str) or not 1 <= len(s) <= 180 for s in items)
                or len(set(items)) != len(items)):
            raise ContractError("invalid native product markers")
        profiles[name] = tuple(items)
    if not set(CRITICAL_INVARIANTS).issubset(profiles):
        raise ContractError("review-pinned critical profile missing")
    return profiles


def check(root: Path, name: str) -> None:
    profiles = requirements()
    if name not in profiles:
        raise ContractError("unrecognized product profile")
    agent, interface = canonical()
    actual, local = block(read(root, "AGENTS.md"))
    if actual != agent or read(root, ".github/DEVELOPMENT_INTERFACE.md") != interface:
        raise ContractError("consumer contract drift")
    if local.count("<!-- agent-project: " + name + " -->") != 1:
        raise ContractError("project identity missing or wrong")
    if any(marker not in local for marker in profiles[name]):
        raise ContractError("mandatory native requirements missing")
    if any(rule not in local for rule in CRITICAL_INVARIANTS.get(name, ())):
        raise ContractError("critical product prohibition changed or missing")


def self_check() -> None:
    canonical()
    requirements()
    for name in ("ek-context", "ek-verify", "ek-pr-closeout"):
        skill = read(ROOT, "skills/" + name + "/SKILL.md")
        if not skill.startswith("---\n") or "\nname: " + name + "\n" not in skill:
            raise ContractError("missing instruction-only skill: " + name)
