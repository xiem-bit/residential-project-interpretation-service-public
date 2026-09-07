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


def validate_ue_production_mapping(data: dict) -> list[str]:
    """Check references inside the existing contract, not production-source rules."""
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    version = meta.get("ue_production_mapping_version")
    c3 = data.get("chapter3") if isinstance(data.get("chapter3"), dict) else {}
    modules = c3.get("system_modules") if isinstance(c3.get("system_modules"), list) else []
    has_mapping = any(isinstance(m, dict) and ("ue_pages" in m or "production_items" in m)
                      for m in modules)
    if version is None and not has_mapping:
        return []  # Historical contracts remain readable, without new-interface acceptance.
    errors: list[str] = []
    levels = {"品牌", "城市", "区域", "板块", "土地", "配套", "项目"}
    if version != 1:
        errors.append("meta.ue_production_mapping_version: 新页面制作接口须明确为1")
    basis = meta.get("production_basis")
    if not isinstance(basis, list) or not basis or any(not isinstance(x, str) or not x.strip() for x in basis):
        errors.append("meta.production_basis: 缺少当前采用的生产依据")
    common = c3.get("common_project_answer") if isinstance(c3.get("common_project_answer"), dict) else {}
    sections = common.get("super_competitiveness_sections")
    sections = sections if isinstance(sections, list) else []
    sc_ids = {s["source_ref"] for s in sections if isinstance(s, dict) and isinstance(s.get("source_ref"), str)}
    items: set[str] = set()
    pages: dict[str, tuple[str, dict]] = {}
    module_ids = {m["id"] for m in modules if isinstance(m, dict) and isinstance(m.get("id"), str)}

    def refs(value, allowed, path, required=True):
        if not isinstance(value, list) or (required and not value):
            errors.append(f"{path}: 须填写非空引用列表" if required else f"{path}: 须为引用列表")
            return
        if any(not isinstance(x, str) or x not in allowed for x in value):
            errors.append(f"{path}: 包含不存在的引用")

    def required_text(obj, fields, path):
        for field in fields:
            if not isinstance(obj.get(field), str) or not obj[field].strip():
                errors.append(f"{path}.{field}: 缺少具体内容")

    for mi, module in enumerate(modules):
        if not isinstance(module, dict):
            continue
        path = f"chapter3.system_modules[{mi}]"
        if not isinstance(module.get("production_items"), list):
            errors.append(f"{path}.production_items: 须为列表；全部引用共用制作项时可以为空")
        if not isinstance(module.get("ue_pages"), list) or not module["ue_pages"]:
            errors.append(f"{path}.ue_pages: 缺少UE页面定义")
        for item in module.get("production_items", []) if isinstance(module.get("production_items"), list) else []:
            if not isinstance(item, dict):
                errors.append(f"{path}.production_items: 制作项须为对象")
                continue
            required_text(item, ("id", "content", "basis", "status"), path + ".production_items")
            ident = item.get("id")
            if isinstance(ident, str):
                if ident in items:
                    errors.append(f"{path}.production_items: 制作项重复定义：{ident}；共用内容应引用")
                items.add(ident)
        for page in module.get("ue_pages", []) if isinstance(module.get("ue_pages"), list) else []:
            if not isinstance(page, dict):
                errors.append(f"{path}.ue_pages: 页面须为对象")
                continue
            required_text(page, ("id", "production_level", "narrative_task", "base_object",
                                 "panel_content", "interaction", "basis"), path + ".ue_pages")
            ident = page.get("id")
            if isinstance(ident, str):
                if ident in pages:
                    errors.append(f"{path}.ue_pages: UE页面重复定义：{ident}")
                pages[ident] = (module.get("id"), page)
    for ident, (_, page) in pages.items():
        if not isinstance(page.get("production_level"), str) or page["production_level"] not in levels:
            errors.append(f"{ident}.production_level: 须使用生产端七级层名")
        refs(page.get("production_item_refs"), items, f"{ident}.production_item_refs")
        refs(page.get("supports_super_competitiveness_refs", []), sc_ids,
             f"{ident}.supports_super_competitiveness_refs", required=False)
        if not page.get("supports_super_competitiveness_refs") and not str(page.get("standard_content_reason") or "").strip():
            errors.append(f"{ident}: 须说明竞争理由或基础内容职责")
    for section in sections:
        if not isinstance(section, dict):
            continue
        ident = section.get("source_ref")
        refs(section.get("ue_page_refs"), pages, f"{ident}.ue_page_refs")
        for ref in section.get("ue_page_refs", []) if isinstance(section.get("ue_page_refs"), list) else []:
            supported = pages[ref][1].get("supports_super_competitiveness_refs") if isinstance(ref, str) and ref in pages else []
            if isinstance(ref, str) and ref in pages and (not isinstance(supported, list) or ident not in supported):
                errors.append(f"{ident}.ue_page_refs: {ref}未声明承接该竞争力")
    for route in c3.get("family_routes", []) if isinstance(c3.get("family_routes"), list) else []:
        if not isinstance(route, dict):
            continue
        if not isinstance(route.get("scenes"), list) or not route["scenes"]:
            errors.append(f"{route.get('id', 'route')}.scenes: 已登记讲解路线须包含具体页面与讲稿")
        for scene in route.get("scenes", []) if isinstance(route.get("scenes"), list) else []:
            if not isinstance(scene, dict):
                continue
            path = str(scene.get("id", "route_scene"))
            refs(scene.get("ue_page_refs"), pages, path + ".ue_page_refs")
            required_text(scene, ("script", "focus", "emphasis"), path)
            for ref in scene.get("ue_page_refs", []) if isinstance(scene.get("ue_page_refs"), list) else []:
                if isinstance(ref, str) and ref in pages and pages[ref][0] not in (scene.get("module_refs") or []):
                    errors.append(f"{path}: UE页面与调用模块不一致：{ref}")
    scope = c3.get("system_scope_close") if isinstance(c3.get("system_scope_close"), dict) else {}
    decisions = scope.get("scope_decisions", [])
    seen: list[str] = []
    for decision in decisions if isinstance(decisions, list) else []:
        if not isinstance(decision, dict):
            errors.append("scope_decisions: 范围安排须为对象")
            continue
        seen.append(decision.get("level"))
        required_text(decision, ("level", "reason"), "scope_decisions")
        if decision.get("status") not in {"included", "deferred", "not_in_scope"}:
            errors.append("scope_decisions: 须区分本轮制作、后续深化和范围外")
        refs(decision.get("module_refs", []), module_ids, "scope_decisions.module_refs",
             required=decision.get("status") == "included")
    if len(seen) != 7 or any(not isinstance(x, str) for x in seen) or set(seen) != levels:
        errors.append("scope_decisions: 须说明七级内容在本轮的安排，不把售前重点当作完整系统")
    return errors


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
        if not isinstance(scenes, list):
            err(path + ".ue_scenes", "须为列表；非三维价值可为空并填写 presentation_materials")
        else:
            for scene_index, scene in enumerate(scenes):
                if isinstance(scene, dict):
                    register_scene(f"{path}.ue_scenes[{scene_index}]", scene)
                else:
                    err(f"{path}.ue_scenes[{scene_index}]", "场景必须是对象")
        materials = section.get("presentation_materials", [])
        if not isinstance(materials, list):
            err(path + ".presentation_materials", "须为列表")
        else:
            for material_index, material in enumerate(materials):
                material_path = f"{path}.presentation_materials[{material_index}]"
                if not isinstance(material, dict):
                    err(material_path, "展示材料必须是对象")
                    continue
                for field in ("type", "source_ref", "explanation"):
                    if not isinstance(material.get(field), str) or not material[field].strip():
                        err(material_path + "." + field, "须说明材料类型、真实依据及讲解作用")
        if not scenes and not materials:
            err(path + ".presentation_materials", "无 UE 场景时须提供地图、原图、对比材料或讲解依据")
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
        if not (module.get("supports_super_competitiveness_refs") or module.get("supports_route_refs")
                or str(module.get("standard_content_reason") or "").strip()):
            err(path, "模块必须说明竞争力、家庭路径或基础系统职责")
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
    if meta.get("ue_production_mapping_version") == 1:
        if not isinstance(required_labels, list) or not required_labels:
            err("chapter3.system_scope_close.required_module_labels", "须填写本轮内容标签；完整范围由七级scope_decisions说明")
    elif not isinstance(required_labels, list) or len(required_labels) < 8:
        err("chapter3.system_scope_close.required_module_labels", "历史合同至少覆盖8类系统内容")
    if not str(close.get("product5_target", "")).strip():
        err("chapter3.system_scope_close.product5_target", "缺少产物5映射")

    errors.extend(validate_ue_production_mapping(data))

    for path, text in visible_texts:
        for term in INTERNAL_VISIBLE_TERMS:
            if term in text:
                err(path, f"可见文案包含内部方法或已取消服务：{term}")

    if errors:
        for item in errors:
            print("ERROR:", item, file=sys.stderr)
        return 1

    mapping = "页面、制作项与预制脚本引用有效" if meta.get("ue_production_mapping_version") == 1 else "历史结构有效，未验收新版页面制作接口"
    print(f"PASS: 第三章合同结构与引用检查通过；{mapping}。业务判断和生产细则仍须人工复核。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
