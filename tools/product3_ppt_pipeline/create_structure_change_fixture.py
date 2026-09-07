#!/usr/bin/env python3
"""Create a non-production blueprint that tests delete, insert and semantic replacement."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    payload["assembly_version"] = "fixture-v0.3-structure-change"
    payload["fixture_only"] = True
    payload["export_status"] = "approved_for_ppt_production"
    pages = [copy.deepcopy(page) for page in payload["pages"] if page["页面ID"] != "P3F-QJ-014"]

    replacement = next(page for page in pages if page["页面ID"] == "P3F-QJ-020")
    replacement.update(
        {
            "缩略图URL": "http://127.0.0.1:8765/source/QJ-14.png",
            "页面名称": "项目价值递进证明（换语义夹具）",
            "这一页只负责": "用递进式证明结构承接项目价值判断",
            "演讲动作": "提出判断 → 展开证据 → 回收结论。",
            "转场": "进入下一项系统展示。",
            "视觉结构": "四步递进卡＋一句结论",
            "视觉变体ID": "",
            "视觉变体名称": "",
            "视觉参考页ID": "QJ-14",
            "来源页ID": "QJ-14",
            "页面语义ID": "P3-SC-PROOF",
            "装配动作": "recompose_by_semantic",
            "人工修订意见": "技术夹具：验证换语义后只替换目标页结构。",
        }
    )

    source = next(page for page in pages if page["页面ID"] == "P3F-QJ-022")
    inserted = copy.deepcopy(source)
    inserted.update(
        {
            "页面ID": "P3F-QJ-022B",
            "页面名称": "花园关系补充证明（新增页夹具）",
            "这一页只负责": "补充证明花园关系如何进入家庭体验",
            "关系来源页面ID": "P3F-QJ-022",
            "装配动作": "duplicate_page",
            "人工修订意见": "技术夹具：由既有非空白模板复制新增，不是空白页。",
        }
    )
    insert_at = pages.index(source) + 1
    pages.insert(insert_at, inserted)

    for index, page in enumerate(pages, start=1):
        page["页序"] = index
        page["装配版本"] = payload["assembly_version"]
    payload["pages"] = pages
    payload["page_count"] = len(pages)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
