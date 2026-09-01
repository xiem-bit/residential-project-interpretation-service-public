#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import load_run, validate_cross_product_consistency, validate_no_placeholders_or_local_paths

parser = argparse.ArgumentParser()
parser.add_argument("run_dir", type=Path)
parser.add_argument("--mode", choices=["normal", "tutorial"], default="normal")
args = parser.parse_args()
data, errors = load_run(args.run_dir)
if not errors:
    validate_no_placeholders_or_local_paths(data, errors)
    validate_cross_product_consistency(data, errors, args.mode)
if errors:
    for error in errors:
        print("ERROR:", error)
    raise SystemExit(1)
print("PASS: 跨产物项目、语义版本与状态一致；本结果不代表战略质量或真人业务接受。")
