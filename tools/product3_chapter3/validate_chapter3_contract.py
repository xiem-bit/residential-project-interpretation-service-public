#!/usr/bin/env python3
"""Validate a Product 3 Chapter 3 production-consumption contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ALLOWED_LAYERS = {"data_judgment", "product_understanding", "family_life"}
INTERNAL_VISIBLE_TERMS = {
    "客户分流",
    "客户待办任务",
    "角色—关系—空间",
    "判断坐标",
    "停止线",
    "业务语义",
    "消费合同",
    "辅助驾驶",
    "Gate",
    "状态机",
    "超级IP",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path)
    args = parser.parse_args()

    try:
        data = json.loads(args.contract.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - command boundary
        print(f"ERROR: 无法读取合同：{exc}", file=sys.stderr)
        return 2

    errors: list[str] = []

    def err(path: str, message: str) -> None:
        errors.append(f"{path}: {message}")

    meta = data.get("meta")
    if not isinstance(meta, dict):
        err("meta", "缺少元数据")
        meta = {}
    if not str(meta.get("project_id", "")).strip():
        err("meta.project_id", "缺少项目标识")
    if meta.get("value_anchor_visualization_service") is not False:
        err("meta.value_anchor_visualization_service", "价值锚点可视化服务必须明确为 false")

    chapter3 = data.get("chapter3")
    if not isinstance(chapter3, dict):
        err("chapter3", "缺少第三章合同")
        chapter3 = {}

    anchor = chapter3.get("value_anchor")
    if not isinstance(anchor, dict):
        err("chapter3.value_anchor", "缺少价值锚点承接")
        anchor = {}
    if anchor.get("usage") != "textual_recap_only":
        err("chapter3.value_anchor.usage", "价值锚点只允许 textual_recap_only")
    if not str(anchor.get("text", "")).strip():
        err("chapter3.value_anchor.text", "缺少价值锚点文本")

    common = chapter3.get("common_project_answer")
    if not isinstance(common, dict):
        err("chapter3.common_project_answer", "缺少项目共同答案")
        common = {}
    sections = common.get("super_competitiveness_sections")
    if not isinstance(sections, list) or not 3 <= len(sections) <= 4:
        err("chapter3.common_project_answer.super_competitiveness_sections", "必须登记3—4条超级竞争力，三条是统一下限")
        sections = []

    scene_ids: set[str] = set()
    sc_refs: set[str] = set()
    visible_texts: list[tuple[str, str]] = []

    def register_scene(path: str, scene: dict) -> None:
        scene_id = str(scene.get("id", "")).strip()
        if not scene_id:
            err(path + ".id", "缺少场景编号")
        elif scene_id in scene_ids:
            err(path + ".id", f"场景编号重复：{scene_id}")
        else:
            scene_ids.add(scene_id)
        if not str(scene.get("product5_target", "")).strip():
            err(path + ".product5_target", "缺少产物5页面、交互或待实现状态")
        title = str(scene.get("visible_title", "")).strip()
        if title:
            visible_texts.append((path + ".visible_title", title))

    for index, section in enumerate(sections):
        path = f"chapter3.common_project_answer.super_competitiveness_sections[{index}]"
        if not isinstance(section, dict):
            err(path, "条目必须是对象")
            continue
        source_ref = str(section.get("source_ref", "")).strip()
        if not source_ref:
            err(path + ".source_ref", "缺少第二章超级竞争力引用")
        elif source_ref in sc_refs:
            err(path + ".source_ref", f"超级竞争力重复：{source_ref}")
        else:
            sc_refs.add(source_ref)
        for field in ("text", "customer_gain"):
            if not str(section.get(field, "")).strip():
                err(path + "." + field, "不能为空")
        bounded = section.get("bounded_superlative")
        if not isinstance(bounded, dict):
            err(
                path + ".bounded_superlative",
                "必须承接第二章的比较对象、购买任务与边界内唯一和最结论",
            )
        else:
            for field in ("comparison_set", "purchase_task", "claim"):
                if not str(bounded.get(field, "")).strip():
                    err(path + ".bounded_superlative." + field, "不能为空")
        for field in ("project_fact_refs", "competition_relation_refs", "customer_question_refs"):
            if not isinstance(section.get(field), list) or not section[field]:
                err(path + "." + field, "至少需要一项引用")
        scenes = section.get("ue_scenes")
        if not isinstance(scenes, list) or not scenes:
            err(path + ".ue_scenes", "至少需要一个 UE 场景")
        else:
            for scene_index, scene in enumerate(scenes):
                if isinstance(scene, dict):
                    register_scene(f"{path}.ue_scenes[{scene_index}]", scene)
                else:
                    err(f"{path}.ue_scenes[{scene_index}]", "场景必须是对象")
        case_slots = section.get("case_slots")
        if not isinstance(case_slots, list) or len(case_slots) < 2:
            err(path + ".case_slots", "每条超级竞争力至少保留两个案例版位")

    routes = chapter3.get("family_routes")
    if not isinstance(routes, list) or not routes:
        err("chapter3.family_routes", "至少需要一条家庭任务路径")
        routes = []
    route_ids: set[str] = set()
    for index, route in enumerate(routes):
        path = f"chapter3.family_routes[{index}]"
        if not isinstance(route, dict):
            err(path, "路径必须是对象")
            continue
        route_id = str(route.get("id", "")).strip()
        if not route_id:
            err(path + ".id", "缺少路径编号")
        elif route_id in route_ids:
            err(path + ".id", f"路径编号重复：{route_id}")
        else:
            route_ids.add(route_id)
        for field in (
            "visible_name",
            "source_product2_task_ref",
            "circumstance",
            "trigger",
            "desired_progress",
            "project_answer",
        ):
            if not str(route.get(field, "")).strip():
                err(path + "." + field, "不能为空")
        visible_name = str(route.get("visible_name", "")).strip()
        if visible_name:
            visible_texts.append((path + ".visible_name", visible_name))
        for field in ("alternative_choices", "decision_conditions", "product_matches"):
            if not isinstance(route.get(field), list) or not route[field]:
                err(path + "." + field, "至少需要一项")
        layers = set(route.get("required_layers") or [])
        if layers != ALLOWED_LAYERS:
            err(path + ".required_layers", "必须完整覆盖 data_judgment、product_understanding、family_life")
        scenes = route.get("scenes")
        if not isinstance(scenes, list) or not 3 <= len(scenes) <= 6:
            err(path + ".scenes", "每条家庭路径需要3—6个连续场景")
            scenes = []
        scene_layers: set[str] = set()
        for scene_index, scene in enumerate(scenes):
            scene_path = f"{path}.scenes[{scene_index}]"
            if not isinstance(scene, dict):
                err(scene_path, "场景必须是对象")
                continue
            register_scene(scene_path, scene)
            layer = scene.get("layer")
            if layer not in ALLOWED_LAYERS:
                err(scene_path + ".layer", "场景层级不合法")
            else:
                scene_layers.add(layer)
            if not isinstance(scene.get("module_refs"), list) or not scene["module_refs"]:
                err(scene_path + ".module_refs", "至少调用一个系统模块")
        if scene_layers != ALLOWED_LAYERS:
            err(path + ".scenes", "实际场景必须覆盖数据判断、产品理解和家庭生活")

    modules = chapter3.get("system_modules")
    if not isinstance(modules, list) or not modules:
        err("chapter3.system_modules", "缺少系统内容模块")
        modules = []
    module_ids: set[str] = set()
    for index, module in enumerate(modules):
        path = f"chapter3.system_modules[{index}]"
        if not isinstance(module, dict):
            err(path, "模块必须是对象")
            continue
        module_id = str(module.get("id", "")).strip()
        if not module_id:
            err(path + ".id", "缺少模块编号")
        elif module_id in module_ids:
            err(path + ".id", f"模块编号重复：{module_id}")
        else:
            module_ids.add(module_id)
        for field in ("label", "visible_value_claim"):
            if not str(module.get(field, "")).strip():
                err(path + "." + field, "不能为空")
        visible_claim = str(module.get("visible_value_claim", "")).strip()
        if visible_claim:
            visible_texts.append((path + ".visible_value_claim", visible_claim))
        if not (module.get("supports_super_competitiveness_refs") or module.get("supports_route_refs")):
            err(path, "模块必须支撑一条超级竞争力或家庭路径")
        if not isinstance(module.get("product5_targets"), list) or not module["product5_targets"]:
            err(path + ".product5_targets", "缺少产物5映射")

    for index, route in enumerate(routes):
        for scene_index, scene in enumerate(route.get("scenes") or []):
            for module_ref in scene.get("module_refs") or []:
                if module_ref not in module_ids:
                    err(
                        f"chapter3.family_routes[{index}].scenes[{scene_index}].module_refs",
                        f"引用了不存在的模块：{module_ref}",
                    )

    close = chapter3.get("system_scope_close")
    if not isinstance(close, dict):
        err("chapter3.system_scope_close", "缺少系统内容全貌收口")
        close = {}
    required_labels = close.get("required_module_labels")
    if not isinstance(required_labels, list) or len(required_labels) < 8:
        err("chapter3.system_scope_close.required_module_labels", "至少覆盖8类系统内容")
    if not str(close.get("product5_target", "")).strip():
        err("chapter3.system_scope_close.product5_target", "缺少产物5映射")

    for path, text in visible_texts:
        for term in INTERNAL_VISIBLE_TERMS:
            if term in text:
                err(path, f"可见文案包含内部方法或已取消服务：{term}")

    if errors:
        for item in errors:
            print("ERROR:", item, file=sys.stderr)
        return 1

    print(
        "PASS: 第三章生产消费合同结构有效；价值锚点仅文本承接，全部竞争力、家庭路径、系统模块与产物5映射完整。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
