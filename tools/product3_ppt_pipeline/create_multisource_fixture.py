#!/usr/bin/env python3
"""Create a three-page non-production blueprint using all three approved source decks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SELECTIONS = [
    ("QJ-22", "P3-SC-PROOF", "花园关系证明结构"),
    ("B10-13", "P3-SC-PROOF", "产品竞争力证明结构"),
    ("GT-17", "P3-FAMILY-PATH", "家庭路径结构"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dataset", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    dataset = json.loads(Path(args.source_dataset).read_text(encoding="utf-8"))
    sources = {page["sourcePageId"]: page for page in dataset["pages"]}
    pages = []
    for order, (source_id, semantic_id, name) in enumerate(SELECTIONS, start=1):
        source = sources[source_id]
        pages.append(
            {
                "页序": order,
                "缩略图URL": source["thumbnailUrl"],
                "页面名称": name,
                "这一页只负责": name,
                "演讲动作": source["speakingAction"],
                "转场": source["transition"],
                "视觉结构": source["visualStructure"],
                "视觉变体ID": source.get("visualVariantId") or ("MAP-OSM-STANDARD" if semantic_id == "P3-COMPETITION-MAP" else ""),
                "视觉变体名称": "OSM真实标准地图" if semantic_id == "P3-COMPETITION-MAP" else "",
                "视觉参考页ID": source_id,
                "章节": "多来源技术夹具",
                "关系来源页面ID": "",
                "来源页ID": source_id,
                "页面语义ID": semantic_id,
                "素材编号": "",
                "人工修订意见": "技术夹具：只验证三份历史PPT原生页汇入同一starter。",
                "裁定状态": "approved",
                "进入PPT生产": 1,
                "项目ID": "P3-TECHNICAL-FIXTURE-MULTISOURCE",
                "项目名称": "三份成功产物3｜多来源原生页技术夹具",
                "装配版本": "fixture-v0.4-multisource",
                "上游冻结状态": "technical_fixture_frozen",
                "页面ID": f"P3F-MULTI-{order:03d}",
                "装配动作": "replace_source_template",
                "有效": 1,
                "可修改范围": "technical_fixture_only",
            }
        )
    payload = {
        "schema": "product3.assembly_blueprint.v0.1",
        "project_id": "P3-TECHNICAL-FIXTURE-MULTISOURCE",
        "project_name": "三份成功产物3｜多来源原生页技术夹具",
        "assembly_version": "fixture-v0.4-multisource",
        "fixture_only": True,
        "export_status": "approved_for_ppt_production",
        "page_count": len(pages),
        "pages": pages,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
