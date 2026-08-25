#!/usr/bin/env python3
"""Validate a native Product 4 XMind against the single-business-tree contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable


FORBIDDEN_TOP_TITLES = {"甲方确认层", "内部生产层", "客户版", "制作版"}
VISIBLE_ID_PREFIX = re.compile(r"^\s*[\[【(（]?\s*(?:P4|VALUE|SC|COMMON|ROUTE|MODULE)[-_]", re.I)


def children(node: dict[str, Any]) -> list[dict[str, Any]]:
    value = node.get("children", {}).get("attached", [])
    return [item for item in value if isinstance(item, dict)]


def walk(node: dict[str, Any], depth: int = 1) -> Iterable[tuple[dict[str, Any], int]]:
    yield node, depth
    for child in children(node):
        yield from walk(child, depth + 1)


def descendants(node: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for child in children(node):
        yield child
        yield from descendants(child)


def load_root(path: Path) -> tuple[dict[str, Any], list[str]]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        required = {"content.json", "metadata.json", "manifest.json"}
        missing = required - set(names)
        if missing:
            raise ValueError("XMind缺少必要文件: " + ", ".join(sorted(missing)))
        content = json.loads(archive.read("content.json"))
        if not isinstance(content, list) or len(content) != 1:
            raise ValueError("产物4必须只有一个XMind工作表")
        root = content[0].get("rootTopic")
        if not isinstance(root, dict):
            raise ValueError("XMind缺少根主题")
        return root, names


def validate(
    path: Path,
    *,
    min_topics: int,
    min_images: int,
    min_depth: int,
    expected_top_branches: int,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    root, names = load_root(path)
    all_nodes = list(walk(root))
    top = children(root)
    image_nodes = [node for node, _ in all_nodes if isinstance(node.get("image"), dict)]
    resources = [name for name in names if name.startswith("resources/") and not name.endswith("/")]
    folded = [node for node, _ in all_nodes if node.get("branch") == "folded"]
    depth = max((item_depth for _, item_depth in all_nodes), default=0)

    if len(all_nodes) < min_topics:
        errors.append(f"主题数量不足: {len(all_nodes)} < {min_topics}")
    if len(image_nodes) < min_images:
        errors.append(f"嵌入图像节点不足: {len(image_nodes)} < {min_images}")
    if depth < min_depth:
        errors.append(f"思维导图深度不足: {depth} < {min_depth}")
    if len(top) != expected_top_branches:
        errors.append(f"一级业务分支数量错误: {len(top)} != {expected_top_branches}")
    if not resources:
        errors.append("XMind未打包任何实际图片资源")

    for branch in top:
        title = str(branch.get("title", "")).strip()
        if title in FORBIDDEN_TOP_TITLES:
            errors.append(f"禁止受众分树作为一级分支: {title}")
        if VISIBLE_ID_PREFIX.search(title):
            errors.append(f"一级业务标题不得展示后台编号: {title}")
        branch_nodes = list(descendants(branch))
        if not any(isinstance(item.get("image"), dict) for item in branch_nodes):
            errors.append(f"一级业务分支缺少实际嵌入图证: {title}")
        if not any(
            item.get("title") == "页面与制作展开" and item.get("branch") == "folded"
            for item in branch_nodes
        ):
            errors.append(f"一级业务分支缺少同树折叠生产展开: {title}")

    for node, node_depth in all_nodes:
        title = str(node.get("title", ""))
        image = node.get("image")
        if isinstance(image, dict):
            src = str(image.get("src", ""))
            if not src.startswith("xap:resources/"):
                errors.append(f"图片节点未使用XMind内嵌资源: {title}")
            elif src.removeprefix("xap:") not in names:
                errors.append(f"图片节点引用的资源不存在: {title} -> {src}")
        if node_depth <= 3 and VISIBLE_ID_PREFIX.search(title):
            errors.append(f"甲方确认深度内不得展示后台编号: {title}")

    inventory = {
        "file": str(path),
        "topics": len(all_nodes),
        "max_depth": depth,
        "image_topics": len(image_nodes),
        "resource_files": len(resources),
        "folded_topics": len(folded),
        "top_branch_count": len(top),
        "top_branch_titles": [str(item.get("title", "")) for item in top],
        "single_business_tree": True,
    }
    return errors, inventory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xmind", type=Path)
    parser.add_argument("--min-topics", type=int, default=100)
    parser.add_argument("--min-images", type=int, default=6)
    parser.add_argument("--min-depth", type=int, default=5)
    parser.add_argument("--expected-top-branches", type=int, default=6)
    parser.add_argument("--inventory-output", type=Path)
    args = parser.parse_args()

    try:
        errors, inventory = validate(
            args.xmind,
            min_topics=args.min_topics,
            min_images=args.min_images,
            min_depth=args.min_depth,
            expected_top_branches=args.expected_top_branches,
        )
    except (OSError, ValueError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    if args.inventory_output:
        args.inventory_output.write_text(
            json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: Product 4 native XMind single-business-tree validation succeeded")
    print(json.dumps(inventory, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
