#!/usr/bin/env python3
"""按当前页面业务语义先检索共享案例图；无命中时返回新生产缺口。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from business_gates import rank_portrait_assets, asset_semantic_text, _semantic_bigrams
from validate_production_input import load_current_inventory


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ASSETS = PROJECT_ROOT / "references/product3/assets/产物3案例截图素材库/case_asset_inventory.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True, help="本页观看对象、机位、空间关系与购买意义")
    parser.add_argument("--asset-class", choices=["case_reference", "audience_portrait"], default="case_reference")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--asset-inventory", type=Path, default=DEFAULT_ASSETS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    inventory = load_current_inventory(args.asset_inventory)
    page = {
        "页面语义ID": "P3-FAMILY-SEGMENT",
        "页面名称": args.query,
        "页面文案": args.query,
        "这一页只负责": args.query,
        "视觉结构": f"{args.count}类家庭肖像与任务卡",
    }
    if args.asset_class == "audience_portrait":
        candidates = rank_portrait_assets(page, inventory, limit=max(args.count * 2, 6))
    else:
        query = _semantic_bigrams(args.query)
        candidates = []
        for asset in inventory:
            if asset.get("asset_class") != args.asset_class:
                continue
            score = len(query & _semantic_bigrams(asset_semantic_text(asset)))
            if score:
                candidates.append({key: asset.get(key, "") for key in (
                    "asset_id", "original_asset", "effective_business_semantic", "product3_recommended_use", "status"
                )} | {"score": score})
        candidates.sort(key=lambda item: (-item["score"], item["asset_id"]))
        candidates = candidates[:max(args.count * 2, 6)]
    reviewed = [
        item
        for item in candidates
        if "待用户复核" not in item["status"] and "待复核" not in item["status"]
    ]
    selected = reviewed[: args.count]
    result = {
        "schema": "product3.case_asset_selection_receipt.v0.1",
        "query": args.query,
        "asset_class": args.asset_class,
        "requested_count": args.count,
        "result": "reuse_match" if len(selected) == args.count else "generation_required",
        "selected": selected,
        "candidate_count": len(candidates),
        "shortfall": max(args.count - len(selected), 0),
        "next_action": (
            "打开候选原图，确认观看对象、尺度、机位与页面职责吻合后，再绑定CASE编号；词语匹配不代表语义验收"
            if len(selected) == args.count
            else "按缺口语义新生产图片，完成业务语义复核并登记CASE编号后再进入正式生产"
        ),
    }
    raw = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if result["result"] == "reuse_match" else 3


if __name__ == "__main__":
    raise SystemExit(main())
