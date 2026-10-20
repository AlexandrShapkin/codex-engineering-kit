"""Offline Engineering Kit observation CLI. No network or native check execution."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

from engineering_kit.contract import ContractError, requirements
from engineering_kit.git_observe import ObservationError, observe


def _context(root: Path) -> dict[str, object]:
    """Paths only; never read file contents or execute project commands."""
    root = root.absolute()
    if not root.is_dir():
        raise ObservationError("context root unavailable")
    paths = [
        "AGENTS.md", ".github/DEVELOPMENT_INTERFACE.md", "README.md",
        "docs/workflow.md", "docs/WORKFLOW.md", "docs/INDEX.md",
        "docs/development-without-rdc.md",
    ]
    found = []
    for p in paths:
        path = root / p
        if path.is_file() and not path.is_symlink():
            found.append(p)
    return {"root": str(root), "entrypoints": found,
            "note": "Source names only; product context not automatically loaded"}


def _doctor() -> dict[str, object]:
    return {"python": ".".join(map(str, sys.version_info[:3])),
            "available": {tool: shutil.which(tool) is not None
                          for tool in ("git", "just", "python3")},
            "note": "Availability only: never installed or executed"}


def _checks(profile_name: str) -> dict[str, object]:
    items = requirements()
    if profile_name not in items:
        raise ContractError("unknown native product profile")
    return {"profile": profile_name, "required_markers": list(items[profile_name]),
            "executed": False,
            "note": "Markers are evidence requirements, not executable recipes"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ek", description=__doc__)
    subs = p.add_subparsers(dest="command", required=True)
    status = subs.add_parser("status")
    status.add_argument("--root", type=Path, default=Path.cwd())
    context = subs.add_parser("context")
    context.add_argument("--root", type=Path, default=Path.cwd())
    subs.add_parser("doctor")
    checks = subs.add_parser("checks")
    checks.add_argument("--profile", required=True)
    args = p.parse_args(argv)
    try:
        if args.command == "status":
            result = observe(args.root)
        elif args.command == "context":
            result = _context(args.root)
        elif args.command == "doctor":
            result = _doctor()
        else:
            result = _checks(args.profile)
    except (ContractError, ObservationError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "data": result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
