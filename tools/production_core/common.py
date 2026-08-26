#!/usr/bin/env python3
"""Standard-library validators for the public residential production path."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable


REQUIRED_FILES = [
    "project-contract.md",
    "fact-conflict-gap-register.json",
    "product1-competition-study.md",
    "product2-buyer-decision-study.md",
    "semantic-core.json",
    "super-competitiveness-plan.json",
    "product-enablement-matrix.json",
    "product3-chapter2-contract.json",
    "product3-chapter3-contract.json",
    "ue-solution-handoff.json",
    "change-impact-registry.json",
    "production-receipt.json",
]

FIVE_CHECKS = {
    "purchase_impact",
    "bounded_unique_or_best",
    "enemy_relation",
    "project_support",
    "ue_provability",
}
PURCHASE_STAGES = {"enter_consideration", "win_comparison", "prompt_action"}
PLACEHOLDER_MARKERS = (
    "[填写",
    "REPLACE_WITH",
    "PROJECT-001",
    "TASK-YYYYMMDD-001",
    "YYYY-MM-DD",
)
PRIVATE_OR_LOCAL = re.compile(
    r"(?:/" + "Users/|" + "file" + r"://|[A-Za-z]:\\|\.workbuddy/" + "binaries/)"
)
JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")


class RunData(dict[str, Any]):
    root: Path


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def _load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path.name}: 无法读取JSON：{exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{path.name}: 根节点必须是对象")
        return {}
    return data


def _load_markdown_summary(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        errors.append(f"{path.name}: 无法读取Markdown：{exc}")
        return {}
    match = JSON_BLOCK.search(text)
    if not match:
        errors.append(f"{path.name}: 缺少第一个```json机器摘要块")
        return {}
    try:
        data = json.loads(match.group(1))
    except Exception as exc:
        errors.append(f"{path.name}: JSON摘要无效：{exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{path.name}: JSON摘要根节点必须是对象")
        return {}
    return data


def load_run(root: Path) -> tuple[RunData, list[str]]:
    root = root.resolve()
    errors: list[str] = []
    data = RunData()
    data.root = root
    for name in REQUIRED_FILES:
        path = root / name
        if not path.is_file():
            errors.append(f"缺少必需文件：{name}")
            data[name] = {}
            continue
        if path.suffix == ".md":
            data[name] = _load_markdown_summary(path, errors)
        else:
            data[name] = _load_json(path, errors)
    return data, errors


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_strings(child)


def validate_no_placeholders_or_local_paths(data: RunData, errors: list[str]) -> None:
    for name, value in data.items():
        for text in _walk_strings(value):
            if any(marker in text for marker in PLACEHOLDER_MARKERS):
                errors.append(f"{name}: 仍含模板占位符：{text[:80]}")
            if PRIVATE_OR_LOCAL.search(text):
                errors.append(f"{name}: 含本机或平台私有路径：{text[:100]}")


def _ids(items: Any, path: str, errors: list[str]) -> set[str]:
    if not isinstance(items, list):
        errors.append(f"{path}: 必须是数组")
        return set()
    result: set[str] = set()
    for index, item in enumerate(items):
        item_id = item.get("id") if isinstance(item, dict) else None
        if not _text(item_id):
            errors.append(f"{path}[{index}].id: 不能为空")
        elif item_id in result:
            errors.append(f"{path}[{index}].id: 重复ID {item_id}")
        else:
            result.add(item_id)
    return result


def validate_project_identity(data: RunData, errors: list[str]) -> None:
    contract = data["project-contract.md"]
    if contract.get("schema") != "residential.project_contract.v0.2":
        errors.append("project-contract.md: schema错误")
    for field in ("task_id", "business_question", "primary_audience", "use_case", "business_stage"):
        if not _text(contract.get(field)):
            errors.append(f"project-contract.md.{field}: 不能为空")
    if contract.get("mode") not in {"real_project_delivery", "hidden_answer_replay", "non_research_task", "tutorial"}:
        errors.append("project-contract.md.mode: 模式无效")
    project = contract.get("project")
    if not isinstance(project, dict):
        errors.append("project-contract.md.project: 缺少项目身份")
        return
    for field in (
        "id",
        "canonical_name",
        "city",
        "district_or_area",
        "location",
        "developer",
        "land_and_phase_relation",
        "lifecycle",
        "fact_cutoff",
    ):
        if not _text(project.get(field)):
            errors.append(f"project-contract.md.project.{field}: 不能为空")
    if project.get("identity_status") != "closed":
        errors.append("project-contract.md.project.identity_status: 必须为closed才能继续")
    if contract.get("status") != "project_identity_closed":
        errors.append("project-contract.md.status: 必须为project_identity_closed")
    inputs = contract.get("authorized_inputs")
    if not isinstance(inputs, list) or not inputs:
        errors.append("project-contract.md.authorized_inputs: 至少一项")
    else:
        _ids(inputs, "project-contract.md.authorized_inputs", errors)
        for index, item in enumerate(inputs):
            if not isinstance(item, dict):
                continue
            if item.get("authorization") not in {"confirmed", "synthetic_public_fixture"}:
                errors.append(f"project-contract.md.authorized_inputs[{index}].authorization: 未确认使用权")
            if item.get("role") not in {
                "formal_material",
                "consultant_work",
                "customer_voice",
                "public_evidence",
                "institutional_data",
                "expert_judgment",
            }:
                errors.append(f"project-contract.md.authorized_inputs[{index}].role: 输入角色无效")


def validate_fact_register(data: RunData, errors: list[str]) -> None:
    register = data["fact-conflict-gap-register.json"]
    if register.get("schema") != "residential.fact_conflict_gap_register.v0.2":
        errors.append("fact-conflict-gap-register.json: schema错误")
    entries = register.get("entries")
    entry_ids = _ids(entries, "fact-conflict-gap-register.json.entries", errors)
    if not entry_ids:
        errors.append("fact-conflict-gap-register.json.entries: 至少一项")
    allowed_kinds = {"fact", "limited_observation", "business_judgment", "working_assumption", "gap", "conflict", "cannot_infer"}
    for index, item in enumerate(entries if isinstance(entries, list) else []):
        if not isinstance(item, dict):
            continue
        if item.get("kind") not in allowed_kinds:
            errors.append(f"fact-conflict-gap-register.json.entries[{index}].kind: 无效")
        for field in ("claim", "scope", "impact", "status"):
            if not _text(item.get(field)):
                errors.append(f"fact-conflict-gap-register.json.entries[{index}].{field}: 不能为空")
        if item.get("kind") in {"gap", "conflict"} and item.get("status") == "open":
            if not _text(item.get("owner")) or not _text(item.get("stop_condition")):
                errors.append(f"fact-conflict-gap-register.json.entries[{index}]: 开放缺口必须有owner和停止条件")


def validate_product1(data: RunData, errors: list[str]) -> None:
    product1 = data["product1-competition-study.md"]
    if product1.get("schema") != "residential.product1_competition_study.v0.2":
        errors.append("product1-competition-study.md: schema错误")
    if product1.get("status") != "product1_complete":
        errors.append("product1-competition-study.md.status: 必须为product1_complete")
    competitors = product1.get("competitors")
    _ids(competitors, "product1-competition-study.md.competitors", errors)
    role_count = 0
    for index, item in enumerate(competitors if isinstance(competitors, list) else []):
        if not isinstance(item, dict):
            continue
        if item.get("role") in {"direct", "partial", "internal_substitute"}:
            role_count += 1
        for field in ("name", "role_boundary", "why_chosen"):
            if not _text(item.get(field)):
                errors.append(f"product1-competition-study.md.competitors[{index}].{field}: 不能为空")
        for field in ("substitution_basis", "strengths", "tradeoffs", "evidence_refs"):
            if not _list(item.get(field)):
                errors.append(f"product1-competition-study.md.competitors[{index}].{field}: 至少一项")
        if "purchase_task" not in set(item.get("substitution_basis") or []):
            errors.append(f"product1-competition-study.md.competitors[{index}]: 替代依据必须包含purchase_task")
    if role_count == 0:
        errors.append("product1-competition-study.md: 至少裁定一个直接、局部或内部替代")
    problem = product1.get("competition_problem")
    if not isinstance(problem, dict):
        errors.append("product1-competition-study.md.competition_problem: 缺少竞争问题")
    else:
        for field in ("adverse_belief", "target_belief"):
            if not _text(problem.get(field)):
                errors.append(f"product1-competition-study.md.competition_problem.{field}: 不能为空")
        for field in ("tangible_enemies", "intangible_enemies", "evidence_refs"):
            if not _list(problem.get(field)):
                errors.append(f"product1-competition-study.md.competition_problem.{field}: 至少一项")
    boundary = product1.get("effective_boundary")
    for field in ("geography", "customer", "area_and_price", "product_form", "purchase_task", "lifecycle_window", "rationale"):
        if not isinstance(boundary, dict) or not _text(boundary.get(field)):
            errors.append(f"product1-competition-study.md.effective_boundary.{field}: 不能为空")
    if len(product1.get("sc_candidates") or []) < 3:
        errors.append("product1-competition-study.md.sc_candidates: 至少三条候选机制")
    stop = product1.get("stop_search")
    if not isinstance(stop, dict) or not isinstance(stop.get("value"), bool) or not _text(stop.get("reason")):
        errors.append("product1-competition-study.md.stop_search: 必须说明是否停止及理由")


def validate_product2(data: RunData, errors: list[str]) -> None:
    product2 = data["product2-buyer-decision-study.md"]
    if product2.get("schema") != "residential.product2_buyer_decision_study.v0.2":
        errors.append("product2-buyer-decision-study.md: schema错误")
    enabled = product2.get("enabled")
    if enabled is True:
        if product2.get("status") != "product2_complete":
            errors.append("product2-buyer-decision-study.md.status: 启用时必须complete")
        tasks = product2.get("purchase_tasks")
        _ids(tasks, "product2-buyer-decision-study.md.purchase_tasks", errors)
        if not tasks:
            errors.append("product2-buyer-decision-study.md.purchase_tasks: 至少一条")
        for index, item in enumerate(tasks if isinstance(tasks, list) else []):
            if not isinstance(item, dict):
                continue
            for field in ("roles_and_relations", "circumstance", "trigger", "desired_progress", "project_fit", "boundary", "source_kind"):
                if not _text(item.get(field)):
                    errors.append(f"product2-buyer-decision-study.md.purchase_tasks[{index}].{field}: 不能为空")
            for field in ("alternatives", "gains", "tolerances", "facilitators", "blockers", "evidence_refs"):
                if not _list(item.get(field)):
                    errors.append(f"product2-buyer-decision-study.md.purchase_tasks[{index}].{field}: 至少一项")
        if not _list(product2.get("counterexamples")):
            errors.append("product2-buyer-decision-study.md.counterexamples: 至少一条反例或失效边界")
    elif enabled is False:
        if product2.get("status") != "not_enabled" or not _text(product2.get("not_enabled_reason")) or not _list(product2.get("covered_by")):
            errors.append("product2-buyer-decision-study.md: 未启用时必须说明理由与等价来源")
    else:
        errors.append("product2-buyer-decision-study.md.enabled: 必须为布尔值")


def validate_semantic_core(data: RunData, errors: list[str]) -> None:
    semantic = data["semantic-core.json"]
    if semantic.get("schema") != "residential.semantic_core.v0.2":
        errors.append("semantic-core.json: schema错误")
    if semantic.get("status") != "semantic_core_frozen":
        errors.append("semantic-core.json.status: 必须为semantic_core_frozen")
    for field in ("project_and_task_identity", "belief_change", "enemies", "effective_boundary", "value_anchor", "product_package"):
        if not isinstance(semantic.get(field), dict):
            errors.append(f"semantic-core.json.{field}: 缺少八项真值组成")
    for field in ("target_customers", "purchase_tasks", "source_outputs", "source_refs"):
        if not _list(semantic.get(field)):
            errors.append(f"semantic-core.json.{field}: 至少一项")
    sc_refs = semantic.get("super_competitiveness_refs")
    if not isinstance(sc_refs, list) or not 3 <= len(sc_refs) <= 4 or len(set(sc_refs)) != len(sc_refs):
        errors.append("semantic-core.json.super_competitiveness_refs: 必须是3—4个唯一ID")
    source_outputs = set(semantic.get("source_outputs") or [])
    if not {"project-contract.md", "product1-competition-study.md"}.issubset(source_outputs):
        errors.append("semantic-core.json.source_outputs: 必须证明语义核来自上游生产输出")


def validate_super_competitiveness(data: RunData, errors: list[str]) -> None:
    plan = data["super-competitiveness-plan.json"]
    semantic = data["semantic-core.json"]
    if plan.get("schema") != "residential.super_competitiveness_plan.v0.2":
        errors.append("super-competitiveness-plan.json: schema错误")
    if plan.get("status") != "minimum_three_sc_pass":
        errors.append("super-competitiveness-plan.json.status: 必须为minimum_three_sc_pass")
    items = plan.get("items")
    sc_ids = _ids(items, "super-competitiveness-plan.json.items", errors)
    if not 3 <= len(sc_ids) <= 4:
        errors.append("super-competitiveness-plan.json.items: 必须有3—4条SC")
    mechanisms: set[str] = set()
    for index, item in enumerate(items if isinstance(items, list) else []):
        if not isinstance(item, dict):
            continue
        if item.get("status") != "established":
            errors.append(f"super-competitiveness-plan.json.items[{index}].status: 正式武器必须established")
        mechanism = str(item.get("mechanism", "")).strip().lower()
        if not mechanism:
            errors.append(f"super-competitiveness-plan.json.items[{index}].mechanism: 不能为空")
        elif mechanism in mechanisms:
            errors.append(f"super-competitiveness-plan.json.items[{index}].mechanism: 机制重复")
        mechanisms.add(mechanism)
        for field in ("target_customer_refs", "purchase_task_refs", "enemy_refs", "project_support_refs", "purchase_stage_effects", "production_items"):
            if not _list(item.get(field)):
                errors.append(f"super-competitiveness-plan.json.items[{index}].{field}: 至少一项")
        bounded = item.get("bounded_claim")
        for field in ("comparison_set", "boundary", "claim"):
            if not isinstance(bounded, dict) or not _text(bounded.get(field)):
                errors.append(f"super-competitiveness-plan.json.items[{index}].bounded_claim.{field}: 不能为空")
        checks = item.get("five_checks")
        if not isinstance(checks, dict) or set(checks) != FIVE_CHECKS:
            errors.append(f"super-competitiveness-plan.json.items[{index}].five_checks: 必须完整且只能包含五项")
        else:
            for name, check in checks.items():
                if not isinstance(check, dict) or check.get("status") != "pass" or not _text(check.get("rationale")) or not _list(check.get("refs")):
                    errors.append(f"super-competitiveness-plan.json.items[{index}].five_checks.{name}: pass必须有解释和引用")
    if set(semantic.get("super_competitiveness_refs") or []) != sc_ids:
        errors.append("semantic-core.json与super-competitiveness-plan.json的SC集合不一致")
    coverage = plan.get("purchase_stage_coverage")
    if not isinstance(coverage, dict) or set(coverage) != PURCHASE_STAGES:
        errors.append("super-competitiveness-plan.json.purchase_stage_coverage: 必须完整覆盖三种购买效果")
    else:
        for stage, refs in coverage.items():
            if not _list(refs) or not set(refs).issubset(sc_ids):
                errors.append(f"super-competitiveness-plan.json.purchase_stage_coverage.{stage}: 引用为空或无效")


def validate_enablement(data: RunData, errors: list[str]) -> None:
    matrix = data["product-enablement-matrix.json"]
    plan = data["super-competitiveness-plan.json"]
    if matrix.get("schema") != "residential.product_enablement_matrix.v0.2":
        errors.append("product-enablement-matrix.json: schema错误")
    products = matrix.get("products")
    ids = {item.get("product") for item in products if isinstance(item, dict)} if isinstance(products, list) else set()
    if ids != {1, 2, 3, 4, 5} or len(products or []) != 5:
        errors.append("product-enablement-matrix.json.products: 必须且只能登记产物1—5")
    by_id = {item.get("product"): item for item in products or [] if isinstance(item, dict)}
    if by_id.get(1, {}).get("status") != "complete":
        errors.append("product-enablement-matrix.json: 研究型任务产物1必须complete")
    for product_id, item in by_id.items():
        if not _text(item.get("reason")) or not isinstance(item.get("deliverables"), list):
            errors.append(f"product-enablement-matrix.json.products[{product_id}]: 必须有理由和deliverables")
    admission = matrix.get("high_cost_admission")
    product3_enabled = by_id.get(3, {}).get("status") in {"enabled", "complete", "in_progress"}
    if product3_enabled:
        if not isinstance(admission, dict) or admission.get("status") != "admitted":
            errors.append("product-enablement-matrix.json: 产物3启用前必须高成本准入")
        elif admission.get("established_sc_count") != len(plan.get("items") or []):
            errors.append("product-enablement-matrix.json: established_sc_count与SC计划不一致")
        elif not all(admission.get(key) is True for key in ("semantic_core_frozen", "all_five_checks_pass", "purchase_stage_coverage_complete", "fact_and_rights_boundary_declared")):
            errors.append("product-enablement-matrix.json: 高成本准入条件未全部成立")
    product5_enabled = by_id.get(5, {}).get("status") in {"enabled", "complete", "in_progress"}
    if product5_enabled:
        path = data.root / "product5-interaction-blueprint.json"
        if not path.is_file():
            errors.append("product5-interaction-blueprint.json: 产物5启用但缺少蓝图")
        else:
            blueprint = _load_json(path, errors)
            data["product5-interaction-blueprint.json"] = blueprint
            if blueprint.get("schema") != "residential.product5_interaction_blueprint.v0.2":
                errors.append("product5-interaction-blueprint.json: schema错误")
            if blueprint.get("project_id") != matrix.get("project_id") or blueprint.get("semantic_version") != matrix.get("semantic_version"):
                errors.append("product5-interaction-blueprint.json: 项目或语义版本不一致")
            sc_ids = {item.get("id") for item in plan.get("items") or [] if isinstance(item, dict)}
            scene_sc_ids = {item.get("sc_id") for item in blueprint.get("sc_scenes") or [] if isinstance(item, dict)}
            if scene_sc_ids != sc_ids:
                errors.append("product5-interaction-blueprint.json: 必须完整映射当前SC集合")
            if blueprint.get("ai_advisor", {}).get("creates_new_sc") is not False:
                errors.append("product5-interaction-blueprint.json: AI推荐官不得新增SC")
            for text in _walk_strings(blueprint):
                if any(marker in text for marker in PLACEHOLDER_MARKERS):
                    errors.append("product5-interaction-blueprint.json: 仍含模板占位符")
                    break
                if PRIVATE_OR_LOCAL.search(text):
                    errors.append("product5-interaction-blueprint.json: 含本机或平台私有路径")
                    break


def validate_ue_solution_bridge(data: RunData, errors: list[str]) -> None:
    semantic = data["semantic-core.json"]
    plan = data["super-competitiveness-plan.json"]
    chapter2 = data["product3-chapter2-contract.json"]
    chapter3 = data["product3-chapter3-contract.json"]
    handoff = data["ue-solution-handoff.json"]
    if chapter2.get("schema") != "residential.product3_chapter2_strategy_contract.v0.2":
        errors.append("product3-chapter2-contract.json: schema错误")
    if chapter3.get("schema") != "residential.product3_chapter3_ue_contract.v0.2":
        errors.append("product3-chapter3-contract.json: schema错误")
    if handoff.get("schema") != "residential.ue_solution_handoff.v0.2":
        errors.append("ue-solution-handoff.json: schema错误")
    project_ids = {item.get("project_id") for item in (semantic, plan, chapter2, chapter3, handoff)}
    versions = {item.get("semantic_version", item.get("version")) for item in (semantic, plan, chapter2, chapter3, handoff)}
    if len(project_ids) != 1:
        errors.append("UE桥接：项目ID不一致")
    if len(versions) != 1:
        errors.append("UE桥接：语义版本不一致")
    semantic_sc = set(semantic.get("super_competitiveness_refs") or [])
    plan_sc = {item.get("id") for item in plan.get("items") or [] if isinstance(item, dict)}
    chapter2_sc = {item.get("id") for item in chapter2.get("super_competitiveness") or [] if isinstance(item, dict)}
    solutions = chapter3.get("solutions") or []
    chapter3_sc = {item.get("sc_id") for item in solutions if isinstance(item, dict)}
    mappings = handoff.get("mappings") or []
    handoff_sc = {item.get("sc_id") for item in mappings if isinstance(item, dict)}
    if not semantic_sc or not (semantic_sc == plan_sc == chapter2_sc == chapter3_sc == handoff_sc):
        errors.append("UE桥接：语义核、SC计划、第二章、第三章和交接的SC集合必须一致")
    anchor_texts = {
        semantic.get("value_anchor", {}).get("text"),
        chapter2.get("value_anchor", {}).get("text"),
        chapter3.get("value_anchor", {}).get("text"),
    }
    if len(anchor_texts) != 1 or None in anchor_texts:
        errors.append("UE桥接：第二／三章价值锚点必须与语义核一致")
    task_ids = {item.get("id") for item in semantic.get("purchase_tasks") or [] if isinstance(item, dict)}
    module_ids = {item.get("id") for item in chapter3.get("system_modules") or [] if isinstance(item, dict)}
    scene_ids: set[str] = set()
    for index, solution in enumerate(solutions):
        if not isinstance(solution, dict):
            continue
        for field in ("customer_gain", "bounded_claim"):
            if not _text(solution.get(field)):
                errors.append(f"product3-chapter3-contract.json.solutions[{index}].{field}: 不能为空")
        for field in ("project_fact_refs", "competition_relation_refs", "purchase_task_refs", "ue_scenes"):
            if not _list(solution.get(field)):
                errors.append(f"product3-chapter3-contract.json.solutions[{index}].{field}: 至少一项")
        if not set(solution.get("purchase_task_refs") or []).issubset(task_ids):
            errors.append(f"product3-chapter3-contract.json.solutions[{index}]: 购买任务引用无效")
        for scene_index, scene in enumerate(solution.get("ue_scenes") or []):
            if not isinstance(scene, dict):
                errors.append(f"product3-chapter3-contract.json.solutions[{index}].ue_scenes[{scene_index}]: 必须是对象")
                continue
            scene_id = scene.get("id")
            if not _text(scene_id) or scene_id in scene_ids:
                errors.append(f"product3-chapter3-contract.json: UE场景ID为空或重复")
            scene_ids.add(scene_id)
            for field in ("customer_problem", "visual_proof", "interaction", "sales_logic", "target_judgment", "product5_target"):
                if not _text(scene.get(field)):
                    errors.append(f"product3-chapter3-contract.json.{scene_id}.{field}: 不能为空")
            if not _list(scene.get("module_refs")) or not set(scene.get("module_refs") or []).issubset(module_ids):
                errors.append(f"product3-chapter3-contract.json.{scene_id}.module_refs: 为空或无效")
    for index, mapping in enumerate(mappings):
        if not isinstance(mapping, dict):
            continue
        for field in ("purchase_task_refs", "chapter2_refs", "chapter3_scene_refs", "module_refs", "product5_target_refs"):
            if not _list(mapping.get(field)):
                errors.append(f"ue-solution-handoff.json.mappings[{index}].{field}: 至少一项")
        if not set(mapping.get("chapter3_scene_refs") or []).issubset(scene_ids):
            errors.append(f"ue-solution-handoff.json.mappings[{index}]: 场景引用无效")
        if not set(mapping.get("module_refs") or []).issubset(module_ids):
            errors.append(f"ue-solution-handoff.json.mappings[{index}]: 模块引用无效")
    if handoff.get("status") != "ue_solution_bridge_pass":
        errors.append("ue-solution-handoff.json.status: 必须为ue_solution_bridge_pass")


def validate_cross_product_consistency(data: RunData, errors: list[str], mode: str = "normal", require_replication_pass: bool = False) -> None:
    contract = data["project-contract.md"]
    expected_project_id = contract.get("project", {}).get("id")
    for name in REQUIRED_FILES:
        item = data[name]
        project_id = item.get("project_id") if isinstance(item, dict) else None
        if name == "project-contract.md":
            continue
        if project_id != expected_project_id:
            errors.append(f"{name}.project_id: 与项目合同不一致")
    semantic_version = data["semantic-core.json"].get("version")
    for name in ("super-competitiveness-plan.json", "product-enablement-matrix.json", "product3-chapter2-contract.json", "product3-chapter3-contract.json", "ue-solution-handoff.json"):
        if data[name].get("semantic_version") != semantic_version:
            errors.append(f"{name}.semantic_version: 与语义核不一致")
    changes = data["change-impact-registry.json"]
    if changes.get("current_semantic_version") != semantic_version:
        errors.append("change-impact-registry.json.current_semantic_version: 与当前语义核不一致")
    if changes.get("status") == "reprojection_complete" and not changes.get("changes"):
        errors.append("change-impact-registry.json: 声称重投影完成但没有变更")
    receipt = data["production-receipt.json"]
    statuses = receipt.get("business_statuses")
    expected_pass = {
        "rules_loaded",
        "project_identity_closed",
        "product1_complete",
        "product2_complete_or_not_enabled",
        "semantic_core_frozen",
        "minimum_three_sc_pass",
        "ue_solution_bridge_pass",
        "cross_product_consistency_pass",
    }
    if not isinstance(statuses, dict):
        errors.append("production-receipt.json.business_statuses: 缺少")
        statuses = {}
    for key in expected_pass:
        if statuses.get(key) != "pass":
            errors.append(f"production-receipt.json.business_statuses.{key}: 应为pass")
    blind = receipt.get("blind_review")
    final_status = receipt.get("final_status")
    if mode == "tutorial":
        if statuses.get("business_judgment_blind_review_pass") != "not_run" or statuses.get("production_path_replication_pass") != "not_run":
            errors.append("教程回执不得声称独立盲审或生产路径复刻通过")
        if final_status != "tutorial_reference_complete":
            errors.append("教程回执final_status必须为tutorial_reference_complete")
    if require_replication_pass or final_status == "production_path_replication_pass":
        if receipt.get("run_mode") != "hidden_answer_replay":
            errors.append("production_path_replication_pass只能来自hidden_answer_replay")
        if receipt.get("content_guidance_count") != 0:
            errors.append("首次生产路径冷启动要求content_guidance_count=0")
        if not isinstance(blind, dict) or blind.get("status") != "pass" or blind.get("reviewer_independent") is not True or not isinstance(blind.get("score"), (int, float)) or blind.get("score") < 80:
            errors.append("production_path_replication_pass要求独立盲审通过且总分至少80")
        if statuses.get("business_judgment_blind_review_pass") != "pass" or statuses.get("production_path_replication_pass") != "pass":
            errors.append("生产路径最终业务状态未全部pass")
        if not HEX_40.fullmatch(str(receipt.get("candidate_commit", ""))):
            errors.append("production_path_replication_pass要求固定40位候选提交")
        for field in ("input_manifest_sha256", "output_manifest_sha256"):
            if not HEX_64.fullmatch(str(receipt.get(field, ""))):
                errors.append(f"production_path_replication_pass要求有效{field}")
        review_file = blind.get("review_file") if isinstance(blind, dict) else None
        observation_file = blind.get("observation_file") if isinstance(blind, dict) else None
        if not _text(review_file) or not _text(observation_file):
            errors.append("production_path_replication_pass要求独立盲审文件和观察文件")
        else:
            review_path = data.root / str(review_file)
            observation_path = data.root / str(observation_file)
            if not review_path.is_file() or not observation_path.is_file():
                errors.append("独立盲审文件或观察文件不存在")
            else:
                review = _load_json(review_path, errors)
                observation = _load_json(observation_path, errors)
                if review.get("schema") != "residential.hidden_answer_review.v0.2" or review.get("reviewer_independent") is not True or review.get("decision") != "pass" or review.get("automatic_failures"):
                    errors.append("独立盲审文件未形成无自动失败的pass")
                if review.get("total") != blind.get("score") or not isinstance(review.get("total"), (int, float)) or review.get("total") < 80:
                    errors.append("盲审文件总分与回执不一致或不足80")
                rubric_path = Path(__file__).resolve().parents[2] / "evaluation" / "hidden-answer" / "rubric.json"
                rubric = _load_json(rubric_path, errors)
                scores = review.get("scores") if isinstance(review.get("scores"), dict) else {}
                calculated_total = 0
                for dimension in rubric.get("dimensions") or []:
                    dimension_id = dimension.get("id")
                    score_item = scores.get(dimension_id)
                    score = score_item.get("score") if isinstance(score_item, dict) else None
                    if not isinstance(score, (int, float)) or score < dimension.get("minimum", 0) or score > dimension.get("weight", 0):
                        errors.append(f"盲审维度{dimension_id}未达到最低分或超过权重")
                    else:
                        calculated_total += score
                if calculated_total != review.get("total"):
                    errors.append("盲审维度合计与total不一致")
                if observation.get("schema") != "residential.hidden_answer_observation.v0.2" or observation.get("content_guidance_count") != 0 or observation.get("participant", {}).get("independent_from_release_design") is not True or observation.get("participant", {}).get("prior_access_to_holdout_answer") is not False or observation.get("final_status") != "production_path_replication_pass":
                    errors.append("观察文件未证明独立、零内容指导的正式冷启动")
                if observation.get("candidate_commit") != receipt.get("candidate_commit") or observation.get("input_manifest_sha256") != receipt.get("input_manifest_sha256") or observation.get("output_manifest_sha256") != receipt.get("output_manifest_sha256"):
                    errors.append("观察文件与生产回执的提交或输入输出哈希不一致")


STAGE_VALIDATORS: dict[str, Callable[[RunData, list[str]], None]] = {
    "identity": validate_project_identity,
    "fact_register": validate_fact_register,
    "product1": validate_product1,
    "product2": validate_product2,
    "semantic_core": validate_semantic_core,
    "super_competitiveness": validate_super_competitiveness,
    "enablement": validate_enablement,
    "ue_bridge": validate_ue_solution_bridge,
}


def validate_all(root: Path, mode: str = "normal", require_replication_pass: bool = False) -> tuple[RunData, list[str]]:
    data, errors = load_run(root)
    validate_no_placeholders_or_local_paths(data, errors)
    for validator in STAGE_VALIDATORS.values():
        validator(data, errors)
    validate_cross_product_consistency(data, errors, mode=mode, require_replication_pass=require_replication_pass)
    return data, errors


def validate_one(root: Path, stage: str) -> list[str]:
    data, errors = load_run(root)
    if errors:
        return errors
    validate_no_placeholders_or_local_paths(data, errors)
    STAGE_VALIDATORS[stage](data, errors)
    return errors
