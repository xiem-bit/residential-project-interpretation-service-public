#!/usr/bin/env python3
"""Verify a complete public production-path run without judging strategy quality."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "production_core"))

from common import validate_all  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--mode", choices=["normal", "tutorial"], default="normal")
    args = parser.parse_args()
    _, errors = validate_all(args.run_dir, mode=args.mode)
    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        print(f"PRODUCTION PATH MACHINE CONTRACT: FAIL ({len(errors)} errors)", file=sys.stderr)
        return 1
    print("PRODUCTION PATH MACHINE CONTRACT: PASS")
    print("Boundary: structure, references and honest states only; strategic quality and business acceptance remain human judgments.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
