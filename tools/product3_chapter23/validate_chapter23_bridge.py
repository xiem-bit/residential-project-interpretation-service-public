#!/usr/bin/env python3
"""Validate Product 3 Chapter 2 → Chapter 3 semantic continuity."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chapter2_contract", type=Path)
    parser.add_argument("chapter3_contract", type=Path)
    args = parser.parse_args()

    try:
        c2 = load(args.chapter2_contract)
        c3 = load(args.chapter3_contract)
    except Exception as exc:  # pragma: no cover - command boundary
        print(f"ERROR: 无法读取合同：{exc}", file=sys.stderr)
        return 2

    errors: list[str] = []

    def err(message: str) -> None:
        errors.append(message)

    project2 = str(c2.get("meta", {}).get("project_id", "")).strip()
    project3 = str(c3.get("meta", {}).get("project_id", "")).strip()
    if not project2 or project2 != project3:
        err(f"项目标识不一致：chapter2={project2!r}, chapter3={project3!r}")

    chapter2 = c2.get("chapter2", {})
    chapter3 = c3.get("chapter3", {})
    anchor2 = chapter2.get("value_anchor", {})
    anchor3 = chapter3.get("value_anchor", {})
    if str(anchor2.get("text", "")).strip() != str(anchor3.get("text", "")).strip():
        err("第三章价值锚点文本必须与第二章完全一致")
    if anchor3.get("usage") != "textual_recap_only":
        err("第三章价值锚点只允许文本回顾")
    if c3.get("meta", {}).get("value_anchor_visualization_service") is not False:
        err("第三章不得生成价值锚点超级IP或独立可视化服务")

    columns = chapter2.get("advantage_matrix", {}).get("columns", [])
    sc2: dict[str, dict] = {}
    for column in columns:
        if not isinstance(column, dict):
            continue
        sc = column.get("super_competitiveness")
        if isinstance(sc, dict) and str(sc.get("id", "")).strip():
            sc2[str(sc["id"]).strip()] = sc

    sections = chapter3.get("common_project_answer", {}).get("super_competitiveness_sections", [])
    sc3: dict[str, dict] = {}
    for section in sections:
        if isinstance(section, dict) and str(section.get("source_ref", "")).strip():
            sc3[str(section["source_ref"]).strip()] = section

    if not 3 <= len(sc2) <= 4:
        err(f"第二章必须形成3—4条超级竞争力，当前为{len(sc2)}条")
    if not 3 <= len(sc3) <= 4:
        err(f"第三章必须承接3—4条超级竞争力，当前为{len(sc3)}条")

    if set(sc2) != set(sc3):
        err(f"超级竞争力映射不完整：第二章={sorted(sc2)}, 第三章={sorted(sc3)}")
    for ref, source in sc2.items():
        target = sc3.get(ref)
        if not target:
            continue
        if str(source.get("text", "")).strip() != str(target.get("text", "")).strip():
            err(f"超级竞争力文本发生改写：{ref}")
        if source.get("bounded_superlative") != target.get("bounded_superlative"):
            err(f"超级竞争力的边界内唯一和最发生改写：{ref}")
        if not str(target.get("customer_gain", "")).strip():
            err(f"超级竞争力缺少客户获得：{ref}")
        if not target.get("project_fact_refs"):
            err(f"超级竞争力缺少项目事实：{ref}")
        if not target.get("ue_scenes"):
            err(f"超级竞争力缺少UE画面：{ref}")

    relation_ids = {
        str(item.get("id", "")).strip()
        for item in chapter2.get("candidate_and_substitute_relations", {}).get("relations", [])
        if isinstance(item, dict)
    }
    decision_ids = {
        str(item.get("id", "")).strip()
        for item in c2.get("customer_decision_registry", [])
        if isinstance(item, dict)
    }
    evidence_ids = {
        str(item.get("id", "")).strip()
        for item in c2.get("evidence_registry", [])
        if isinstance(item, dict)
    }
    for ref, section in sc3.items():
        missing_rel = set(section.get("competition_relation_refs") or []) - relation_ids
        missing_dec = set(section.get("customer_question_refs") or []) - decision_ids
        missing_evi = set(section.get("project_fact_refs") or []) - evidence_ids
        if missing_rel:
            err(f"{ref}引用不存在的第二章竞争关系：{sorted(missing_rel)}")
        if missing_dec:
            err(f"{ref}引用不存在的第二章客户决策机制：{sorted(missing_dec)}")
        if missing_evi:
            err(f"{ref}引用不存在的证据：{sorted(missing_evi)}")

    routes = chapter3.get("family_routes", [])
    route_scene_ids = {
        str(scene.get("id", "")).strip()
        for route in routes
        if isinstance(route, dict)
        for scene in route.get("scenes", [])
        if isinstance(scene, dict)
    }
    modules = chapter3.get("system_modules", [])
    for module in modules:
        if not isinstance(module, dict):
            continue
        if not (
            set(module.get("supports_super_competitiveness_refs") or []) & set(sc2)
            or set(module.get("supports_route_refs") or [])
        ):
            err(f"系统模块未映射第二章竞争力或第三章家庭路径：{module.get('id')}")

    if not route_scene_ids:
        err("第三章缺少家庭路径场景，无法向产物5交接")

    if errors:
        for item in errors:
            print("ERROR:", item, file=sys.stderr)
        return 1

    print(
        "PASS: 第二／三章语义连续；价值锚点保持文本承接，全部竞争力完整映射，家庭路径与系统模块可以继续交给产物5。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
