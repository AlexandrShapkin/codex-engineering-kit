"""Offline Engineering Kit CLI. Explicit bundle/sync writes; no native check execution."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

from engineering_kit.sync import SyncError, export, plan, write, PROFILES
from engineering_kit.distribution import generate
from engineering_kit.source_update import plan_source, write_source
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
    bundle = subs.add_parser("bundle")
    bundle.add_argument("--channel", choices=("kit", "admin"), default="kit")
    bundle.add_argument("--source", type=Path, default=Path.cwd())
    bundle.add_argument("--revision", required=True)
    bundle.add_argument("--profile", choices=(*PROFILES, "administrative"), required=True)
    bundle.add_argument("--output", type=Path, required=True)
    distribution = subs.add_parser("distribution", description="Generate private candidate; never publish")
    distribution.add_argument("--channel", choices=("kit", "admin"), required=True)
    distribution.add_argument("--source", type=Path, required=True)
    distribution.add_argument("--revision", required=True)
    distribution.add_argument("--profile", choices=(*PROFILES, "administrative"), required=True)
    distribution.add_argument("--output", type=Path, required=True)
    distribution.add_argument("--review", type=Path, required=True)
    distribution.add_argument("--review-sha256", required=True)
    distribution.add_argument("--generator-revision", required=True)
    sync = subs.add_parser("sync")
    sync_subs = sync.add_subparsers(dest="operation", required=True)
    for operation in ("plan", "write"):
        command = sync_subs.add_parser(operation)
        command.add_argument("--channel", choices=("kit", "admin"), default="kit")
        command.add_argument("--root", type=Path, required=True)
        command.add_argument("--bundle", type=Path, required=True)
        command.add_argument("--public-bundle-sha256",
                             help="Full digest of named bytes separately approved by owner")
        if operation == "write":
            command.add_argument("--allow", action="append", default=[])
            command.add_argument("--plan-sha256", required=True)
    source_update = subs.add_parser("source-update", description="Offline reviewed source proposals")
    source_subs = source_update.add_subparsers(dest="operation", required=True)
    for operation in ("plan", "write"):
        command = source_subs.add_parser(operation)
        command.add_argument("--channel", choices=("kit", "admin"), required=True)
        command.add_argument("--root", type=Path, required=True)
        command.add_argument("--source", type=Path, required=True)
        command.add_argument("--revision", required=True)
        if operation == "write":
            command.add_argument("--allow", action="append", default=[])
            command.add_argument("--plan-sha256", required=True)
    args = p.parse_args(argv)
    try:
        if args.command == "source-update":
            if args.operation == "plan":
                result, _ = plan_source(args.root, args.source, args.revision, args.channel)
            else:
                result = write_source(args.root, args.source, args.revision, args.channel,
                                      args.allow, args.plan_sha256)
        elif args.command == "distribution":
            result = generate(args.source, args.revision, args.profile, args.output,
                              args.channel, args.review, args.review_sha256,
                              args.generator_revision)
        elif args.command == "bundle":
            result = export(args.source, args.revision, args.profile, args.output, args.channel)
        elif args.command == "sync":
            if args.operation == "plan":
                result, _ = plan(args.root, args.bundle, args.channel, args.public_bundle_sha256)
            else:
                result = write(args.root, args.bundle, args.allow, args.plan_sha256,
                               args.channel, args.public_bundle_sha256)
        elif args.command == "status":
            result = observe(args.root)
        elif args.command == "context":
            result = _context(args.root)
        elif args.command == "doctor":
            result = _doctor()
        else:
            result = _checks(args.profile)
    except (ContractError, ObservationError, SyncError, OSError, UnicodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "data": result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
