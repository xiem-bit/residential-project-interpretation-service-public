#!/usr/bin/env python3
"""Verify a focused Product 3 patch and prove unrelated pages did not drift."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_rms(left_path: Path, right_path: Path) -> float:
    with Image.open(left_path).convert("RGB") as left, Image.open(right_path).convert("RGB") as right:
        if left.size != right.size:
            return float("inf")
        stat = ImageStat.Stat(ImageChops.difference(left, right))
        return math.sqrt(sum(value * value for value in stat.rms) / len(stat.rms))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--parent-mapping", required=True)
    parser.add_argument("--patched-mapping", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()

    request = load_json(Path(args.request))
    parent = load_json(Path(args.parent_mapping))
    patched = load_json(Path(args.patched_mapping))
    parent_by_id = {page["page_id"]: page for page in parent["pages"]}
    patched_by_id = {page["page_id"]: page for page in patched["pages"]}
    changed_pages = {
        operation["page_id"]
        for operation in request.get("operations", [])
        if operation["op"] in {"replace_image", "replace_text"}
    }
    moved_pages = {
        operation["page_id"]
        for operation in request.get("operations", [])
        if operation["op"] == "move_page"
    }
    errors: list[str] = []
    if set(parent_by_id) != set(patched_by_id):
        errors.append("修订前后页面ID集合发生变化")
    if patched.get("parent_deck_sha256") != parent.get("output_deck_sha256"):
        errors.append("修订版记录的父版哈希与父版映射不一致")
    if sha256_file(Path(patched["output_pptx"])) != patched.get("output_deck_sha256"):
        errors.append("修订版PPTX哈希与修订映射不一致")

    rms_by_page: dict[str, float] = {}
    for page_id in sorted(set(parent_by_id) & set(patched_by_id)):
        rms = image_rms(
            Path(parent_by_id[page_id]["preview_path"]),
            Path(patched_by_id[page_id]["preview_path"]),
        )
        rms_by_page[page_id] = round(rms, 6)
        if page_id not in changed_pages and rms != 0:
            errors.append(f"未授权变化：{page_id}渲染RMS={rms:.6f}")
        if page_id in changed_pages and rms == 0:
            errors.append(f"预期变化未发生：{page_id}")

    for operation in request.get("operations", []):
        if operation["op"] == "move_page":
            actual = patched_by_id[operation["page_id"]]["order"]
            if actual != operation["target_order"]:
                errors.append(f"调序未生效：{operation['page_id']}期望{operation['target_order']}，实际{actual}")
        if operation["op"] == "replace_image":
            page = patched_by_id[operation["page_id"]]
            binding = page.get("asset_bindings", {}).get(operation.get("role", "main_image"), {})
            if binding.get("asset_id") != operation.get("asset_id"):
                errors.append(f"换图绑定未写入：{operation['page_id']}")

    receipt = {
        "schema": "product3.patch_receipt.v0.1",
        "status": "pass" if not errors else "fail",
        "fixture_only": bool(request.get("fixture_only")),
        "project_id": request.get("project_id"),
        "assembly_version": request.get("assembly_version"),
        "parent_pptx": request.get("parent_pptx"),
        "output_pptx": patched.get("output_pptx"),
        "operations": request.get("operations", []),
        "changed_pages": sorted(changed_pages),
        "moved_pages": sorted(moved_pages),
        "unaffected_page_count": len(parent_by_id) - len(changed_pages),
        "unaffected_pages_unchanged": not any(
            page_id not in changed_pages and rms != 0 for page_id, rms in rms_by_page.items()
        ),
        "rms_by_page": rms_by_page,
        "errors": errors,
    }
    receipt_path = Path(args.receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "changed_pages": receipt["changed_pages"],
        "moved_pages": receipt["moved_pages"],
        "unaffected_pages_unchanged": receipt["unaffected_pages_unchanged"],
        "errors": errors,
    }, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
