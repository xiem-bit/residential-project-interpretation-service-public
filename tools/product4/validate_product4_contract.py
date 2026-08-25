#!/usr/bin/env python3
"""Validate the Product 4 single-business-tree production contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


REQUIRED_AUDIENCES = {"client_decision_maker", "internal_delivery_team"}
REQUIRED_P5_DEPTHS = {"presales_focus", "delivery_full"}
VISIBLE_ID_PREFIX = re.compile(r"^\s*[\[【(（]?\s*(?:P4|VALUE|SC|COMMON|ROUTE|MODULE)[-_]", re.I)
FORBIDDEN_VISIBLE_TERMS = {
    "甲方确认层",
    "内部生产层",
    "客户版",
    "制作版",
    "client_confirmation",
    "internal_production",
    "source_refs",
    "production_expansion",
}
REQUIRED_PRODUCTION_FIELDS = (
    "layout_zones",
    "visual_and_data_jobs",
    "interaction_states",
    "source_trace_refs",
    "production_roles",
    "product3_projection_refs",
    "product5_targets",
)
REQUIRED_LOCAL_SEMANTIC_SOURCES = (
    "product1_source",
    "product2_source",
    "product3_chapter2_contract",
    "product3_chapter3_contract",
    "accepted_product3_artifact",
    "current_project_contract",
)
REQUIRED_ACCEPTANCE_KEYS = {
    "upstream_ids_preserved_in_metadata",
    "single_business_tree_verified",
    "parallel_audience_roots_absent",
    "client_titles_free_of_backend_ids_and_jargon",
    "production_details_nested_under_business_nodes",
    "main_value_branches_have_embedded_actual_visuals",
    "human_framework_node_comparison_complete",
    "product3_complete_logic_inherited",
    "common_route_module_graph_closed",
    "upper_business_story_complete",
    "deep_production_expansion_complete",
    "product3_projection_complete",
    "product5_presales_focus_mapped",
    "product5_delivery_full_mapped",
    "change_impact_traceable",
    "search_delta_limited_to_material_gaps",
    "official_map_dual_layer_respected",
    "visuals_have_files_proof_jobs_rights_and_embedded_refs",
    "grade_a_semantic_review_complete",
    "grade_a_lint_complete",
    "grade_b_report_only_complete",
    "native_xmind_open_verified",
    "html_not_produced",
}


def load_contract(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("合同根节点必须是对象")
    return data


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def require_mapping(data: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        errors.append(f"缺少对象字段: {key}")
        return {}
    return value


def require_nonempty_list(data: dict[str, Any], key: str, errors: list[str]) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        errors.append(f"字段必须是非空数组: {key}")
        return []
    return value


def require_nonempty_text(data: dict[str, Any], key: str, errors: list[str], label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}必须填写非空文本: {key}")
        return ""
    return value


def validate_prefix(values: list[Any], prefix: str, label: str, errors: list[str]) -> None:
    for value in values:
        if not isinstance(value, str) or not value.startswith(prefix):
            errors.append(f"{label}必须使用{prefix}前缀: {value!r}")


def collect_ids(items: list[Any], label: str, errors: list[str]) -> set[str]:
    result: set[str] = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            errors.append(f"{label}中的每个对象都必须有字符串id")
            continue
        item_id = item["id"]
        if item_id in result:
            errors.append(f"{label}存在重复id: {item_id}")
        result.add(item_id)
    return result


def iter_tree(node: dict[str, Any]) -> Iterable[dict[str, Any]]:
    yield node
    for child in as_list(node.get("children")):
        if isinstance(child, dict):
            yield from iter_tree(child)


def validate_visible_title(node: dict[str, Any], errors: list[str]) -> None:
    node_id = node.get("node_id", "[unknown]")
    title = node.get("visible_title")
    if not isinstance(title, str) or not title.strip():
        errors.append(f"业务节点{node_id}缺少visible_title")
        return
    if VISIBLE_ID_PREFIX.search(title):
        errors.append(f"甲方可见标题不得展示后台编号: {node_id} -> {title}")
    for term in FORBIDDEN_VISIBLE_TERMS:
        if term.lower() in title.lower():
            errors.append(f"甲方可见标题包含后台或受众分树语言: {node_id} -> {term}")


def validate_production_expansion(
    node_id: str,
    expansion: Any,
    errors: list[str],
) -> None:
    if not isinstance(expansion, dict):
        errors.append(f"业务节点{node_id}必须在同一分支内包含production_expansion")
        return
    require_nonempty_text(expansion, "page_job", errors, f"业务节点{node_id}生产展开")
    for field in REQUIRED_PRODUCTION_FIELDS:
        require_nonempty_list(expansion, field, errors)
    depths = {
        target.get("execution_depth")
        for target in as_list(expansion.get("product5_targets"))
        if isinstance(target, dict)
    }
    if depths != REQUIRED_P5_DEPTHS:
        errors.append(f"业务节点{node_id}必须同时映射产物5两种执行深度")
    if expansion.get("folded_by_default") is not True:
        errors.append(f"业务节点{node_id}的深层生产展开必须默认折叠")


def validate_contract(
    data: dict[str, Any],
    strict: bool = False,
    base_dir: Path | None = None,
) -> list[str]:
    errors: list[str] = []

    version = data.get("contract_version")
    if not isinstance(version, str) or not version.startswith("product4_value_framework.v1.2"):
        errors.append("contract_version必须使用product4_value_framework.v1.2系列")
    if "views" in data:
        errors.append("合同根节点禁止使用全局views；甲方与内部消费必须通过同一业务树的展开深度表达")

    task = require_mapping(data, "task", errors)
    if task.get("lifecycle_stage") != "post_contract_first_delivery":
        errors.append("task.lifecycle_stage必须是post_contract_first_delivery")
    audiences = set(as_list(task.get("target_audiences")))
    if not REQUIRED_AUDIENCES.issubset(audiences):
        errors.append("task.target_audiences必须同时包含甲方确认与内部交付团队")
    if task.get("delivery_form") != "native_xmind":
        errors.append("task.delivery_form必须是native_xmind")
    if task.get("html_delivery_allowed") is not False:
        errors.append("task.html_delivery_allowed必须为false")
    if any("html" in str(item).lower() for item in as_list(task.get("delivery_outputs"))):
        errors.append("task.delivery_outputs不得包含HTML")
    if task.get("product5_execution_depth") not in REQUIRED_P5_DEPTHS:
        errors.append("task.product5_execution_depth必须是presales_focus或delivery_full")

    semantic_sources = require_mapping(data, "semantic_sources", errors)
    for key in REQUIRED_LOCAL_SEMANTIC_SOURCES:
        value = require_nonempty_text(semantic_sources, key, errors, "上游语义来源")
        if strict and base_dir is not None and value and "://" not in value:
            source_path = (base_dir / value).resolve()
            if not source_path.is_file() or source_path.stat().st_size <= 0:
                errors.append(f"上游语义来源不存在或为空: {key} -> {source_path}")
    require_nonempty_list(data, "human_reference_inputs", errors)

    refs = require_mapping(data, "stable_semantic_refs", errors)
    if refs.get("value_anchor_ref") != "VALUE-ANCHOR":
        errors.append("stable_semantic_refs.value_anchor_ref必须保持VALUE-ANCHOR")
    sc_refs = require_nonempty_list(refs, "super_competitiveness_refs", errors)
    if sc_refs and not 2 <= len(sc_refs) <= 4:
        errors.append("超级竞争力编号数量必须为2至4条")
    validate_prefix(sc_refs, "SC-", "超级竞争力编号", errors)
    common_refs = require_nonempty_list(refs, "common_scene_refs", errors)
    route_refs = require_nonempty_list(refs, "route_refs", errors)
    module_refs = require_nonempty_list(refs, "module_refs", errors)
    validate_prefix(common_refs, "COMMON-", "通用接待编号", errors)
    validate_prefix(route_refs, "ROUTE-", "客户分流编号", errors)
    validate_prefix(module_refs, "MODULE-", "模块编号", errors)

    rendering = require_mapping(data, "rendering_contract", errors)
    if rendering.get("tree_model") != "single_business_tree":
        errors.append("rendering_contract.tree_model必须是single_business_tree")
    if rendering.get("root_branch_policy") != "business_value_branches_only":
        errors.append("根节点下只允许业务价值分支")
    if rendering.get("native_xmind_required") is not True:
        errors.append("rendering_contract.native_xmind_required必须为true")
    placement = str(rendering.get("internal_detail_placement", ""))
    if "nested" not in placement:
        errors.append("内部生产明细必须嵌套在对应业务节点内")
    forbidden_roots = set(as_list(rendering.get("forbidden_parallel_audience_roots")))
    if not {"甲方确认层", "内部生产层"}.issubset(forbidden_roots):
        errors.append("rendering_contract必须明确禁止甲方确认层／内部生产层并列根分支")

    depth_policy = require_mapping(data, "depth_policy", errors)
    client_depth = depth_policy.get("client_confirmation_depth")
    production_depth = depth_policy.get("production_detail_depth_min")
    if not isinstance(client_depth, int) or not isinstance(production_depth, int):
        errors.append("depth_policy必须提供整数展开深度")
    elif production_depth <= client_depth:
        errors.append("内部生产明细深度必须大于甲方确认深度")

    search_method = require_mapping(data, "shared_search_method", errors)
    require_nonempty_list(search_method, "shared_business_objects", errors)
    contributions = require_mapping(search_method, "product_contributions", errors)
    for product in ("product1", "product2", "product3", "product4", "product5_feedback"):
        require_nonempty_list(contributions, product, errors)

    graph = require_mapping(data, "experience_graph", errors)
    common_nodes = require_nonempty_list(graph, "common_reception", errors)
    route_nodes = require_nonempty_list(graph, "customer_routes", errors)
    module_nodes = require_nonempty_list(graph, "reusable_modules", errors)
    common_ids = collect_ids(common_nodes, "experience_graph.common_reception", errors)
    route_ids = collect_ids(route_nodes, "experience_graph.customer_routes", errors)
    module_ids = collect_ids(module_nodes, "experience_graph.reusable_modules", errors)
    if set(common_refs) != common_ids:
        errors.append("stable_semantic_refs.common_scene_refs必须与通用接待节点一致")
    if set(route_refs) != route_ids:
        errors.append("stable_semantic_refs.route_refs必须与客户分流节点一致")
    if set(module_refs) != module_ids:
        errors.append("stable_semantic_refs.module_refs必须与复用模块节点一致")
    for route in route_nodes:
        if not isinstance(route, dict):
            continue
        for module_ref in as_list(route.get("module_refs")):
            if module_ref not in module_ids:
                errors.append(f"客户分流引用了不存在的模块: {module_ref}")

    visuals = require_nonempty_list(data, "visuals", errors)
    visual_ids: set[str] = set()
    visual_by_id: dict[str, dict[str, Any]] = {}
    for visual in visuals:
        if not isinstance(visual, dict) or not isinstance(visual.get("visual_id"), str):
            errors.append("visuals中的每项必须有visual_id")
            continue
        visual_id = visual["visual_id"]
        if visual_id in visual_ids:
            errors.append(f"visuals存在重复visual_id: {visual_id}")
        visual_ids.add(visual_id)
        visual_by_id[visual_id] = visual
        for key in ("proof_job", "source", "rights_status", "local_asset_path"):
            require_nonempty_text(visual, key, errors, f"图证{visual_id}")
        require_nonempty_list(visual, "embedded_in_node_refs", errors)
        if strict and base_dir is not None:
            rel = visual.get("local_asset_path")
            if isinstance(rel, str) and rel.strip():
                asset = (base_dir / rel).resolve()
                if not asset.is_file() or asset.stat().st_size <= 0:
                    errors.append(f"图证{visual_id}的实际文件不存在或为空: {asset}")

    tree = require_mapping(data, "business_tree", errors)
    root = require_mapping(tree, "root", errors)
    root_children = require_nonempty_list(root, "children", errors)
    all_nodes: list[dict[str, Any]] = list(iter_tree(root)) if root else []
    node_ids: set[str] = set()
    for node in all_nodes:
        node_id = node.get("node_id")
        if not isinstance(node_id, str) or not node_id:
            errors.append("business_tree每个节点必须有node_id")
            continue
        if node_id in node_ids:
            errors.append(f"business_tree存在重复node_id: {node_id}")
        node_ids.add(node_id)
        validate_visible_title(node, errors)
        for visual_ref in as_list(node.get("visual_refs")):
            if visual_ref not in visual_ids:
                errors.append(f"业务节点{node_id}引用不存在的图证: {visual_ref}")

    main_branches = [node for node in root_children if isinstance(node, dict)]
    for branch in main_branches:
        node_id = str(branch.get("node_id", "[unknown]"))
        if branch.get("main_value_branch") is not True:
            errors.append(f"根节点子分支必须明确为主业务价值分支: {node_id}")
        expression = branch.get("client_expression")
        if not isinstance(expression, dict) or not str(expression.get("claim", "")).strip():
            errors.append(f"主价值分支{node_id}缺少client_expression.claim")
        require_nonempty_text(branch, "customer_meaning", errors, f"主价值分支{node_id}")
        require_nonempty_text(branch, "project_conversion", errors, f"主价值分支{node_id}")
        branch_visuals = require_nonempty_list(branch, "visual_refs", errors)
        validate_production_expansion(node_id, branch.get("production_expansion"), errors)
        for visual_ref in branch_visuals:
            visual = visual_by_id.get(str(visual_ref))
            if visual and node_id not in as_list(visual.get("embedded_in_node_refs")):
                errors.append(f"主价值分支{node_id}的图证{visual_ref}未登记嵌入该节点")

    for node in all_nodes:
        if node is root:
            continue
        if "production_expansion" in node:
            validate_production_expansion(str(node.get("node_id")), node.get("production_expansion"), errors)

    for visual_id, visual in visual_by_id.items():
        for node_ref in as_list(visual.get("embedded_in_node_refs")):
            if node_ref not in node_ids:
                errors.append(f"图证{visual_id}登记了不存在的嵌入节点: {node_ref}")

    projections = require_nonempty_list(data, "product3_projection", errors)
    for projection in projections:
        if not isinstance(projection, dict):
            errors.append("product3_projection中的每项必须是对象")
            continue
        if projection.get("product4_node_ref") not in node_ids:
            errors.append(f"product3_projection引用了不存在的产物4节点: {projection.get('product4_node_ref')}")
        require_nonempty_list(projection, "product3_page_refs", errors)

    handoff = require_mapping(data, "product5_handoff", errors)
    profiles = require_nonempty_list(handoff, "profiles", errors)
    profile_depths = {
        profile.get("execution_depth")
        for profile in profiles
        if isinstance(profile, dict)
    }
    if profile_depths != REQUIRED_P5_DEPTHS:
        errors.append("product5_handoff.profiles必须同时包含presales_focus与delivery_full")
    require_nonempty_list(handoff, "role_handoff", errors)

    comparison = require_mapping(data, "human_framework_comparison", errors)
    require_nonempty_list(comparison, "comparison_scope", errors)
    if strict and comparison.get("status") != "complete":
        errors.append("严格验收要求human_framework_comparison.status为complete")

    require_nonempty_list(data, "change_impact_registry", errors)
    acceptance = require_mapping(data, "acceptance", errors)
    missing_acceptance = sorted(REQUIRED_ACCEPTANCE_KEYS - set(acceptance))
    if missing_acceptance:
        errors.append("acceptance缺少必需项: " + ", ".join(missing_acceptance))
    if strict:
        unfinished = [key for key in REQUIRED_ACCEPTANCE_KEYS if acceptance.get(key) is not True]
        if unfinished:
            errors.append("严格验收仍有未完成项: " + ", ".join(sorted(unfinished)))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--strict", action="store_true", help="要求图证文件存在且acceptance全部为true")
    args = parser.parse_args()

    try:
        contract = load_contract(args.contract)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    errors = validate_contract(contract, strict=args.strict, base_dir=args.contract.parent)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    mode = "strict" if args.strict else "structure"
    print(f"PASS: Product 4 single-tree contract {mode} validation succeeded: {args.contract}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
