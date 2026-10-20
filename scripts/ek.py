#!/usr/bin/env python3
"""Engineering Kit read-only CLI entrypoint; no install required."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engineering_kit.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
