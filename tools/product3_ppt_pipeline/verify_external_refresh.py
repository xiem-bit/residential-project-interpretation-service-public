#!/usr/bin/env python3
"""Compare an externally edited parent with its prior production mapping."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def image_rms(left_path: Path, right_path: Path) -> float:
    with Image.open(left_path).convert("RGB") as left, Image.open(right_path).convert("RGB") as right:
        if left.size != right.size:
            return float("inf")
        stat = ImageStat.Stat(ImageChops.difference(left, right))
        return math.sqrt(sum(value * value for value in stat.rms) / len(stat.rms))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior-mapping", required=True)
    parser.add_argument("--refreshed-mapping", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()

    prior = load_json(Path(args.prior_mapping))
    refreshed = load_json(Path(args.refreshed_mapping))
    prior_by_id = {page["page_id"]: page for page in prior["pages"]}
    refreshed_by_id = {page["page_id"]: page for page in refreshed["pages"]}
    errors: list[str] = []
    if set(prior_by_id) != set(refreshed_by_id):
        errors.append("外部父版页面集合发生新增或删除，必须回到控制台重新识别")

    changed_pages: list[str] = []
    moved_pages: list[str] = []
    rms_by_page: dict[str, float] = {}
    for page_id in sorted(set(prior_by_id) & set(refreshed_by_id)):
        before = prior_by_id[page_id]
        after = refreshed_by_id[page_id]
        rms = image_rms(Path(before["preview_path"]), Path(after["preview_path"]))
        rms_by_page[page_id] = round(rms, 6)
        if rms != 0:
            changed_pages.append(page_id)
        if before["order"] != after["order"]:
            moved_pages.append(page_id)

    status = "fail" if errors else ("pass_requires_human_reconciliation" if changed_pages else "pass")
    receipt = {
        "schema": "product3.external_parent_diff_receipt.v0.1",
        "status": status,
        "prior_pptx": prior.get("output_pptx"),
        "external_parent_pptx": refreshed.get("output_pptx"),
        "changed_pages": changed_pages,
        "moved_pages": moved_pages,
        "unchanged_page_count": len(prior_by_id) - len(changed_pages),
        "rms_by_page": rms_by_page,
        "asset_bindings_status": "requires_reconciliation" if changed_pages else "unchanged",
        "errors": errors,
    }
    receipt_path = Path(args.receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": status,
        "changed_pages": changed_pages,
        "moved_pages": moved_pages,
        "unchanged_page_count": receipt["unchanged_page_count"],
        "errors": errors,
    }, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
