#!/usr/bin/env python3
"""Read-only offline checker. Native product verification is separate."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engineering_kit.contract import ContractError, check, self_check


def main():
    p = argparse.ArgumentParser()
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-check", action="store_true")
    mode.add_argument("--profile")
    p.add_argument("--root", type=Path)
    args = p.parse_args()
    try:
        if args.self_check:
            if args.root is not None:
                raise ContractError("--root is only valid with --profile")
            self_check()
        elif args.root is None:
            raise ContractError("--profile requires --root")
        else:
            check(args.root, args.profile)
    except ContractError as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1
    print("PASS: offline contract validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
