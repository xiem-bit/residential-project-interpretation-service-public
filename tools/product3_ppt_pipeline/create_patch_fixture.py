#!/usr/bin/env python3
"""Create a clearly marked non-production patch request for the QJ technical fixture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-pptx", required=True)
    parser.add_argument("--parent-mapping", required=True)
    parser.add_argument("--asset", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = {
        "schema": "product3.patch_request.v0.1",
        "project_id": "P3-TECHNICAL-FIXTURE-QJ",
        "assembly_version": "fixture-v0.2-image-and-order",
        "fixture_only": True,
        "status": "technical_fixture_only",
        "parent_pptx": str(Path(args.parent_pptx).resolve()),
        "parent_mapping": str(Path(args.parent_mapping).resolve()),
        "operations": [
            {
                "op": "replace_image",
                "page_id": "P3F-QJ-013",
                "role": "main_image",
                "asset_id": "CASE-043",
                "asset_path": str(Path(args.asset).resolve()),
                "alt": "案例图 CASE-043，花园关系与总平展示",
                "expected_semantic_ids": ["P3-SC-PROOF"],
                "fit": "cover",
            },
            {
                "op": "move_page",
                "page_id": "P3F-QJ-008",
                "target_order": 7,
            },
            {
                "op": "replace_text",
                "page_id": "P3F-QJ-011",
                "role": "title",
                "find": "今天",
                "replace": "当下",
            },
        ],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
