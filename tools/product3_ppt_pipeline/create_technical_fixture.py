#!/usr/bin/env python3
"""从历史来源页标注生成只供技术验证的非业务裁定夹具。"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEMANTICS = PROJECT_ROOT / "references/product3/assets/产物3页面模板库/datasets/page_semantic_dataset.v0.3.json"
SOURCES = PROJECT_ROOT / "references/product3/assets/产物3页面模板库/datasets/source_page_semantic_annotations.v0.3.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck-id", choices=["QJ", "B10", "GT"], default="QJ")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    semantic_dataset = json.loads(SEMANTICS.read_text(encoding="utf-8"))
    source_dataset = json.loads(SOURCES.read_text(encoding="utf-8"))
    semantic_by_id = {item["semanticId"]: item for item in semantic_dataset["semantics"]}
    source_pages = [item for item in source_dataset["pages"] if item["deckId"] == args.deck_id]
    source_pages.sort(key=lambda item: item["sourceSlide"])
    pages = []
    for source in source_pages:
        semantic = semantic_by_id[source["primarySemanticId"]]
        source_id = source["sourcePageId"]
        pages.append({
            "页序": source["sourceSlide"],
            "缩略图URL": source["thumbnailUrl"],
            "页面名称": source["pagePurpose"],
            "这一页只负责": source["pagePurpose"],
            "演讲动作": semantic["speakingAction"],
            "转场": semantic["transition"],
            "视觉结构": source["visualStructure"],
            "视觉变体ID": source.get("visualVariantId") or "",
            "视觉变体名称": next((item["name"] for item in semantic_dataset.get("visualVariants", []) if item["visualVariantId"] == source.get("visualVariantId")), ""),
            "视觉参考页ID": source_id if source.get("visualVariantId") else "",
            "章节": "技术夹具",
            "关系来源页面ID": "",
            "来源页ID": source_id,
            "页面语义ID": source["primarySemanticId"],
            "素材编号": "",
            "人工修订意见": "技术夹具：只验证生产管道，不代表真人业务裁定。",
            "裁定状态": "approved",
            "进入PPT生产": 1,
            "项目ID": f"P3-TECHNICAL-FIXTURE-{args.deck_id}",
            "项目名称": f"{source['sourceProject']}｜单一来源技术夹具",
            "装配版本": "fixture-v0.1",
            "上游冻结状态": "technical_fixture_frozen",
            "页面ID": f"P3F-{args.deck_id}-{source['sourceSlide']:03d}",
            "装配动作": "duplicate-slide",
            "有效": 1,
            "可修改范围": "technical_fixture_only",
        })
    payload = {
        "schema": "product3.assembly_blueprint.v0.1",
        "export_status": "approved_for_ppt_production",
        "fixture_only": True,
        "fixture_warning": "仅供技术验证，不代表真人已裁定、正式项目可生产或业务内容被接受。",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "project_id": f"P3-TECHNICAL-FIXTURE-{args.deck_id}",
        "project_name": f"{source_pages[0]['sourceProject']}｜单一来源技术夹具",
        "assembly_version": "fixture-v0.1",
        "page_count": len(pages),
        "pages": pages,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
