#!/usr/bin/env python3
"""Shared CLI for individual production-stage validators."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import STAGE_VALIDATORS, validate_one


def run(stage: str) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    errors = validate_one(args.run_dir, stage)
    if errors:
        for error in errors:
            print("ERROR:", error)
        return 1
    print(f"PASS: {stage}结构与引用合同有效；本结果不代表战略质量盲审通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit("请使用对应阶段入口")
