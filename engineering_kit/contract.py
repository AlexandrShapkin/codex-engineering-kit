"""Portable offline agent-contract validation. No subprocess, network or writes."""
from __future__ import annotations

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


def read(root: Path, rel: str) -> str:
    pathbits = Path(rel)
    if not rel or pathbits.is_absolute() or ".." in pathbits.parts:
        raise ContractError("unsafe relative path")
    try:
        path = root
        if stat.S_ISLNK(path.lstat().st_mode):
            raise ContractError("symlinked root")
        for p in pathbits.parts:
            path = path / p
            if stat.S_ISLNK(path.lstat().st_mode):
                raise ContractError("symlinked contract path")
        meta = path.stat()
        if not stat.S_ISREG(meta.st_mode) or meta.st_size > LIMIT:
            raise ContractError("invalid or oversized file")
        data = path.read_bytes()
        if len(data) > LIMIT:
            raise ContractError("oversized file")
        return data.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise ContractError("unavailable contract file") from exc


def block(text: str) -> tuple[str, str]:
    if text.count(START) != 1 or text.count(END) != 1:
        raise ContractError("missing or duplicated shared markers")
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


def self_check() -> None:
    canonical()
    requirements()
    for name in ("ek-context", "ek-verify", "ek-pr-closeout"):
        skill = read(ROOT, "skills/" + name + "/SKILL.md")
        if not skill.startswith("---\n") or "\nname: " + name + "\n" not in skill:
            raise ContractError("missing instruction-only skill: " + name)
