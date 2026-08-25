#!/usr/bin/env python3
"""Validate the internal production contract for Product 3, Chapter 2."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PLACEHOLDER_MARKERS = ("[填写", "[如实填写", "[甲方资料/", "[范围／板块]", "[空间锚点]")
CUSTOMER_DECISION_KINDS = {
    "candidate_entry",
    "active_comparison",
    "substitution",
    "screening",
    "veto",
    "final_choice",
}
FORBIDDEN_CHAPTER2_KEYS = {
    "customer_segments",
    "personas",
    "audience_segments",
    "product_segment_mapping",
    "interaction_branches",
    "sales_scripts",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path, help="Path to the project JSON contract")
    parser.add_argument(
        "--final",
        action="store_true",
        help="Reject template placeholders and require a final production-ready contract",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"文件不存在：{path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON无法解析：{exc}") from exc


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    try:
        data = load_json(args.contract)
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    def err(path: str, message: str) -> None:
        errors.append(f"{path}: {message}")

    def require_text(value: Any, path: str) -> str:
        if not isinstance(value, str) or not value.strip():
            err(path, "必须是非空文本")
            return ""
        return value.strip()

    meta = data.get("meta")
    if not isinstance(meta, dict):
        err("meta", "缺少元信息")
        meta = {}

    chapter_structure = meta.get("chapter_structure", {})
    if chapter_structure.get("template_chapters") != [1, 4]:
        err("meta.chapter_structure.template_chapters", "必须为[1, 4]")
    if chapter_structure.get("project_generated_chapters") != [2, 3]:
        err("meta.chapter_structure.project_generated_chapters", "必须为[2, 3]")

    evidence_registry = data.get("evidence_registry")
    if not isinstance(evidence_registry, list) or not evidence_registry:
        err("evidence_registry", "至少登记一条证据")
        evidence_registry = []
    evidence_ids: set[str] = set()
    for index, evidence in enumerate(evidence_registry):
        path = f"evidence_registry[{index}]"
        if not isinstance(evidence, dict):
            err(path, "必须是对象")
            continue
        evidence_id = require_text(evidence.get("id"), f"{path}.id")
        if evidence_id in evidence_ids:
            err(f"{path}.id", "证据ID重复")
        evidence_ids.add(evidence_id)
        require_text(evidence.get("type"), f"{path}.type")
        require_text(evidence.get("title"), f"{path}.title")
        require_text(evidence.get("locator"), f"{path}.locator")

    customer_decision_registry = data.get("customer_decision_registry")
    if not isinstance(customer_decision_registry, list) or not customer_decision_registry:
        err("customer_decision_registry", "至少登记一项客户决策机制与真实选择事件")
        customer_decision_registry = []
    customer_decision_ids: set[str] = set()
    for index, decision in enumerate(customer_decision_registry):
        path = f"customer_decision_registry[{index}]"
        if not isinstance(decision, dict):
            err(path, "必须是对象")
            continue
        decision_id = require_text(decision.get("id"), f"{path}.id")
        if decision_id in customer_decision_ids:
            err(f"{path}.id", "客户决策机制ID重复")
        customer_decision_ids.add(decision_id)
        kind = require_text(decision.get("kind"), f"{path}.kind")
        if kind and kind not in CUSTOMER_DECISION_KINDS:
            err(f"{path}.kind", f"必须属于{sorted(CUSTOMER_DECISION_KINDS)}")
        require_text(decision.get("text"), f"{path}.text")
        require_text(decision.get("choice_event"), f"{path}.choice_event")
        refs = decision.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            err(f"{path}.evidence_refs", "至少引用一条证据")
        else:
            for ref in refs:
                if ref not in evidence_ids:
                    err(f"{path}.evidence_refs", f"未知证据ID：{ref}")

    chapter2 = data.get("chapter2")
    if not isinstance(chapter2, dict):
        err("chapter2", "缺少第二章合同")
        chapter2 = {}

    for forbidden_key in sorted(FORBIDDEN_CHAPTER2_KEYS):
        if forbidden_key in chapter2:
            err(
                f"chapter2.{forbidden_key}",
                "具体客群、产品匹配、交互分支和销讲脚本必须进入第三章",
            )

    outcomes = chapter2.get("communication_outcomes")
    if not isinstance(outcomes, list) or len(outcomes) != 2:
        err("chapter2.communication_outcomes", "必须恰好包含两个目标")

    used_customer_decision_ids: set[str] = set()
    choice_context = chapter2.get("candidate_and_substitute_relations")
    if not isinstance(choice_context, dict):
        err("chapter2.candidate_and_substitute_relations", "缺少客户候选与替代关系")
        choice_context = {}
    require_text(
        choice_context.get("visible_claim"),
        "chapter2.candidate_and_substitute_relations.visible_claim",
    )
    relations = choice_context.get("relations")
    if not isinstance(relations, list) or not relations:
        err("chapter2.candidate_and_substitute_relations.relations", "至少包含一组候选或替代关系")
        relations = []
    relation_ids: set[str] = set()
    for index, relation in enumerate(relations):
        path = f"chapter2.candidate_and_substitute_relations.relations[{index}]"
        if not isinstance(relation, dict):
            err(path, "必须是对象")
            continue
        relation_id = require_text(relation.get("id"), f"{path}.id")
        if relation_id in relation_ids:
            err(f"{path}.id", "候选或替代关系ID重复")
        relation_ids.add(relation_id)
        require_text(relation.get("option_a"), f"{path}.option_a")
        require_text(relation.get("option_b"), f"{path}.option_b")
        require_text(relation.get("relation"), f"{path}.relation")
        require_text(relation.get("customer_reason"), f"{path}.customer_reason")
        refs = relation.get("customer_decision_refs")
        if not isinstance(refs, list) or not refs:
            err(f"{path}.customer_decision_refs", "至少引用一项客户决策机制")
        else:
            for ref in refs:
                if ref not in customer_decision_ids:
                    err(f"{path}.customer_decision_refs", f"未知客户决策机制ID：{ref}")
                else:
                    used_customer_decision_ids.add(ref)

    dimensions = chapter2.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        err("chapter2.dimensions", "至少包含一个竞争维度")
        dimensions = []

    ordered_dimensions = sorted(
        [dimension for dimension in dimensions if isinstance(dimension, dict)],
        key=lambda item: item.get("order", 10_000),
    )
    dimension_plan = meta.get("dimension_plan", {})
    if dimension_plan.get("default_order_used") is True:
        actual_names = [dimension.get("name") for dimension in ordered_dimensions]
        if actual_names != ["区域", "规划", "户型"]:
            err("meta.dimension_plan", "声明使用默认顺序时，维度必须为区域→规划→户型")
    else:
        require_text(dimension_plan.get("change_reason"), "meta.dimension_plan.change_reason")

    fact_ids: set[str] = set()
    subject_fact_ids: set[str] = set()
    competitor_fact_ids: set[str] = set()
    conclusion_ids: set[str] = set()
    dimension_column_ids: set[str] = set()
    dimension_ids: set[str] = set()
    dimension_orders: set[int] = set()

    def validate_fact(item: Any, path: str, factors: set[str], role: str) -> str:
        if not isinstance(item, dict):
            err(path, "必须是对象")
            return ""
        item_id = require_text(item.get("id"), f"{path}.id")
        if item_id in fact_ids:
            err(f"{path}.id", "事实ID重复")
        fact_ids.add(item_id)
        if role == "subject":
            subject_fact_ids.add(item_id)
        else:
            competitor_fact_ids.add(item_id)
        factor_id = require_text(item.get("factor_id"), f"{path}.factor_id")
        if factor_id and factor_id not in factors:
            err(f"{path}.factor_id", "必须属于本维度comparison_factors")
        require_text(item.get("text"), f"{path}.text")
        refs = item.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            err(f"{path}.evidence_refs", "至少引用一条证据")
        else:
            for ref in refs:
                if ref not in evidence_ids:
                    err(f"{path}.evidence_refs", f"未知证据ID：{ref}")
        return item_id

    for dim_index, dimension in enumerate(dimensions):
        path = f"chapter2.dimensions[{dim_index}]"
        if not isinstance(dimension, dict):
            err(path, "必须是对象")
            continue
        dimension_id = require_text(dimension.get("id"), f"{path}.id")
        if dimension_id in dimension_ids:
            err(f"{path}.id", "竞争维度ID重复")
        dimension_ids.add(dimension_id)
        require_text(dimension.get("name"), f"{path}.name")
        if not isinstance(dimension.get("order"), int):
            err(f"{path}.order", "必须是整数")
        elif dimension["order"] in dimension_orders:
            err(f"{path}.order", "竞争维度顺序重复")
        else:
            dimension_orders.add(dimension["order"])
        require_text(dimension.get("customer_question"), f"{path}.customer_question")
        dimension_customer_refs = dimension.get("customer_decision_refs")
        if not isinstance(dimension_customer_refs, list) or not dimension_customer_refs:
            err(f"{path}.customer_decision_refs", "至少引用一项与本维度相关的真实选择事件")
            dimension_customer_refs = []
        else:
            for ref in dimension_customer_refs:
                if ref not in customer_decision_ids:
                    err(f"{path}.customer_decision_refs", f"未知客户决策机制ID：{ref}")
                else:
                    used_customer_decision_ids.add(ref)
        column_id = require_text(dimension.get("advantage_column_id"), f"{path}.advantage_column_id")
        dimension_column_ids.add(column_id)

        factors_raw = dimension.get("comparison_factors")
        if not isinstance(factors_raw, list) or not 2 <= len(factors_raw) <= 5:
            err(f"{path}.comparison_factors", "必须包含2—5个比较因素")
            factors_raw = []
        factors = {str(factor) for factor in factors_raw}
        if len(factors) != len(factors_raw):
            err(f"{path}.comparison_factors", "比较因素不得重复")

        competitors = dimension.get("competitors")
        if not isinstance(competitors, list) or not competitors:
            err(f"{path}.competitors", "至少包含一个竞品")
            competitors = []
        competitor_ids = {
            competitor.get("id")
            for competitor in competitors
            if isinstance(competitor, dict) and isinstance(competitor.get("id"), str)
        }

        map_info = dimension.get("map")
        if not isinstance(map_info, dict):
            err(f"{path}.map", "缺少地图信息")
            map_info = {}
        spatial_comparison = map_info.get("spatial_comparison")
        if spatial_comparison is None:
            spatial_comparison = dimension.get("name") in {"区域", "地段", "配套", "交通"}
        if not isinstance(spatial_comparison, bool):
            err(f"{path}.map.spatial_comparison", "必须是布尔值")
            spatial_comparison = False
        if spatial_comparison:
            require_text(map_info.get("base_map_asset"), f"{path}.map.base_map_asset")
            require_text(map_info.get("subject_location"), f"{path}.map.subject_location")
        map_competitors = map_info.get("competitor_ids")
        if not isinstance(map_competitors, list) or set(map_competitors) != competitor_ids:
            err(f"{path}.map.competitor_ids", "必须与本维度竞品ID完整一致")
        supporting_assets = map_info.get("supporting_visual_assets")
        if not spatial_comparison and (
            not isinstance(supporting_assets, list) or not supporting_assets
        ):
            err(f"{path}.map.supporting_visual_assets", "非空间维度必须配置对应产品或事实证据图")

        subject = dimension.get("subject")
        if not isinstance(subject, dict):
            err(f"{path}.subject", "缺少本案卡片")
            subject = {}
        subject_strengths = subject.get("strengths")
        if not isinstance(subject_strengths, list) or len(subject_strengths) != 3:
            err(f"{path}.subject.strengths", "本案卡片必须恰好包含3条价值点")
            subject_strengths = []
        for item_index, item in enumerate(subject_strengths):
            validate_fact(item, f"{path}.subject.strengths[{item_index}]", factors, "subject")

        dimension_subject_fact_ids = {
            item.get("id")
            for item in subject_strengths
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        dimension_competitor_fact_ids: set[str] = set()

        for comp_index, competitor in enumerate(competitors):
            comp_path = f"{path}.competitors[{comp_index}]"
            if not isinstance(competitor, dict):
                err(comp_path, "必须是对象")
                continue
            require_text(competitor.get("id"), f"{comp_path}.id")
            require_text(competitor.get("name"), f"{comp_path}.name")
            require_text(competitor.get("role_boundary"), f"{comp_path}.role_boundary")
            strengths = competitor.get("strengths")
            if not isinstance(strengths, list) or not 1 <= len(strengths) <= 3:
                err(f"{comp_path}.strengths", "竞品优势必须为1—3条")
                strengths = []
            limitations = competitor.get("limitations")
            if not isinstance(limitations, list) or len(limitations) < 1:
                err(f"{comp_path}.limitations", "至少包含1条有证据的选择代价或适配边界")
                limitations = []
            for item_index, item in enumerate(strengths):
                validate_fact(item, f"{comp_path}.strengths[{item_index}]", factors, "competitor")
                if isinstance(item, dict) and isinstance(item.get("id"), str):
                    dimension_competitor_fact_ids.add(item["id"])
            for item_index, item in enumerate(limitations):
                validate_fact(item, f"{comp_path}.limitations[{item_index}]", factors, "competitor")
                if isinstance(item, dict) and isinstance(item.get("id"), str):
                    dimension_competitor_fact_ids.add(item["id"])

        dimension_fact_ids = dimension_subject_fact_ids | dimension_competitor_fact_ids

        conclusions = dimension.get("conclusions")
        if not isinstance(conclusions, list) or not 1 <= len(conclusions) <= 3:
            err(f"{path}.conclusions", "竞争结论必须为1—3条")
            conclusions = []
        for conclusion_index, conclusion in enumerate(conclusions):
            conclusion_path = f"{path}.conclusions[{conclusion_index}]"
            if not isinstance(conclusion, dict):
                err(conclusion_path, "必须是对象")
                continue
            conclusion_id = require_text(conclusion.get("id"), f"{conclusion_path}.id")
            if conclusion_id in conclusion_ids:
                err(f"{conclusion_path}.id", "竞争结论ID重复")
            conclusion_ids.add(conclusion_id)
            require_text(conclusion.get("text"), f"{conclusion_path}.text")
            refs = conclusion.get("fact_refs")
            if not isinstance(refs, list) or not refs:
                err(f"{conclusion_path}.fact_refs", "必须引用本页事实")
                continue
            unknown_refs = [ref for ref in refs if ref not in dimension_fact_ids]
            if unknown_refs:
                err(f"{conclusion_path}.fact_refs", f"不是本页事实ID：{unknown_refs}")
            if not any(ref in dimension_subject_fact_ids for ref in refs):
                err(f"{conclusion_path}.fact_refs", "至少引用一项本案事实")
            if not any(ref in dimension_competitor_fact_ids for ref in refs):
                err(f"{conclusion_path}.fact_refs", "至少引用一项竞品或竞争关系事实")
            customer_refs = conclusion.get("customer_decision_refs")
            if not isinstance(customer_refs, list) or not customer_refs:
                err(f"{conclusion_path}.customer_decision_refs", "至少引用一项客户决策机制")
            else:
                for ref in customer_refs:
                    if ref not in customer_decision_ids:
                        err(
                            f"{conclusion_path}.customer_decision_refs",
                            f"未知客户决策机制ID：{ref}",
                        )
                    elif ref not in dimension_customer_refs:
                        err(
                            f"{conclusion_path}.customer_decision_refs",
                            f"必须属于本维度已声明的客户决策机制：{ref}",
                        )
                    else:
                        used_customer_decision_ids.add(ref)

    matrix = chapter2.get("advantage_matrix")
    if not isinstance(matrix, dict):
        err("chapter2.advantage_matrix", "缺少优势收敛表")
        matrix = {}
    columns = matrix.get("columns")
    if not isinstance(columns, list) or not 3 <= len(columns) <= 4:
        err("chapter2.advantage_matrix.columns", "必须包含3—4组优势与对应超级竞争力，三条是统一下限")
        columns = []

    advantage_ids: set[str] = set()
    advantage_column_by_id: dict[str, str] = {}
    super_ids: set[str] = set()
    matrix_column_ids: set[str] = set()
    for column_index, column in enumerate(columns):
        path = f"chapter2.advantage_matrix.columns[{column_index}]"
        if not isinstance(column, dict):
            err(path, "必须是对象")
            continue
        column_id = require_text(column.get("id"), f"{path}.id")
        matrix_column_ids.add(column_id)
        require_text(column.get("label"), f"{path}.label")
        items = column.get("items")
        if not isinstance(items, list) or not 1 <= len(items) <= 3:
            err(f"{path}.items", "每组必须包含1—3项可溯源优势")
            items = []
        column_advantage_ids: set[str] = set()
        for item_index, item in enumerate(items):
            item_path = f"{path}.items[{item_index}]"
            if not isinstance(item, dict):
                err(item_path, "必须是对象")
                continue
            item_id = require_text(item.get("id"), f"{item_path}.id")
            if item_id in advantage_ids:
                err(f"{item_path}.id", "优势ID重复")
            advantage_ids.add(item_id)
            column_advantage_ids.add(item_id)
            advantage_column_by_id[item_id] = column_id
            require_text(item.get("text"), f"{item_path}.text")
            require_text(item.get("customer_progress"), f"{item_path}.customer_progress")
            refs = item.get("conclusion_refs")
            if not isinstance(refs, list) or not refs:
                err(f"{item_path}.conclusion_refs", "至少引用一条竞争结论")
            else:
                for ref in refs:
                    if ref not in conclusion_ids:
                        err(f"{item_path}.conclusion_refs", f"未知竞争结论ID：{ref}")

        super_comp = column.get("super_competitiveness")
        if not isinstance(super_comp, dict):
            err(f"{path}.super_competitiveness", "缺少超级竞争力")
            continue
        super_id = require_text(super_comp.get("id"), f"{path}.super_competitiveness.id")
        if super_id in super_ids:
            err(f"{path}.super_competitiveness.id", "超级竞争力ID重复")
        super_ids.add(super_id)
        for field in ("text", "range", "super_trait", "form"):
            require_text(super_comp.get(field), f"{path}.super_competitiveness.{field}")
        bounded = super_comp.get("bounded_superlative")
        if not isinstance(bounded, dict):
            err(
                f"{path}.super_competitiveness.bounded_superlative",
                "必须结构化登记比较对象、购买任务与边界内唯一和最结论",
            )
        else:
            for field in ("comparison_set", "purchase_task", "claim"):
                require_text(
                    bounded.get(field),
                    f"{path}.super_competitiveness.bounded_superlative.{field}",
                )
        refs = super_comp.get("advantage_item_refs")
        if not isinstance(refs, list) or set(refs) != column_advantage_ids:
            err(f"{path}.super_competitiveness.advantage_item_refs", "必须完整引用本组全部优势")

    if dimension_column_ids != matrix_column_ids:
        err("chapter2.advantage_matrix.columns", "维度声明的优势组与实际优势组不一致")

    anchor = chapter2.get("value_anchor")
    if not isinstance(anchor, dict):
        err("chapter2.value_anchor", "缺少价值锚点")
        anchor = {}
    for field in (
        "text",
        "spatial_anchor",
        "differentiating_trait",
        "product_form",
        "shared_customer_progress",
    ):
        require_text(anchor.get(field), f"chapter2.value_anchor.{field}")
    anchor_customer_refs = anchor.get("customer_decision_refs")
    if not isinstance(anchor_customer_refs, list) or not anchor_customer_refs:
        err("chapter2.value_anchor.customer_decision_refs", "至少引用一项共同客户决策机制")
    else:
        for ref in anchor_customer_refs:
            if ref not in customer_decision_ids:
                err("chapter2.value_anchor.customer_decision_refs", f"未知客户决策机制ID：{ref}")
            else:
                used_customer_decision_ids.add(ref)
    anchor_adv_refs = anchor.get("advantage_item_refs")
    if not isinstance(anchor_adv_refs, list) or len(anchor_adv_refs) < len(matrix_column_ids):
        err("chapter2.value_anchor.advantage_item_refs", "至少从每组引用1项优势")
    else:
        for ref in anchor_adv_refs:
            if ref not in advantage_ids:
                err("chapter2.value_anchor.advantage_item_refs", f"未知优势ID：{ref}")
        covered_columns = {
            advantage_column_by_id.get(ref)
            for ref in anchor_adv_refs
            if ref in advantage_column_by_id
        }
        if covered_columns != matrix_column_ids:
            err("chapter2.value_anchor.advantage_item_refs", "必须覆盖全部优势组")
    anchor_super_refs = anchor.get("super_competitiveness_refs")
    if not isinstance(anchor_super_refs, list) or set(anchor_super_refs) != super_ids:
        err("chapter2.value_anchor.super_competitiveness_refs", "必须完整引用全部超级竞争力")

    display_strategy = chapter2.get("display_strategy")
    if not isinstance(display_strategy, dict):
        err("chapter2.display_strategy", "缺少展示策略目标")
        display_strategy = {}
    for strategy_name in ("rational", "emotional"):
        strategy = display_strategy.get(strategy_name)
        path = f"chapter2.display_strategy.{strategy_name}"
        if not isinstance(strategy, dict):
            err(path, "缺少目标")
            continue
        require_text(strategy.get("text"), f"{path}.text")
        refs = strategy.get("advantage_item_refs")
        if not isinstance(refs, list) or not refs:
            err(f"{path}.advantage_item_refs", "至少引用一项优势")
        else:
            for ref in refs:
                if ref not in advantage_ids:
                    err(f"{path}.advantage_item_refs", f"未知优势ID：{ref}")

    handoff = chapter2.get("handoff_to_chapter3")
    if not isinstance(handoff, dict):
        err("chapter2.handoff_to_chapter3", "缺少第二章向第三章的消费接口")
        handoff = {}
    if handoff.get("value_anchor_usage") != "textual_recap_only":
        err("chapter2.handoff_to_chapter3.value_anchor_usage", "价值锚点只允许 textual_recap_only")
    if handoff.get("value_anchor_visualization_service") is not False:
        err(
            "chapter2.handoff_to_chapter3.value_anchor_visualization_service",
            "价值锚点可视化服务必须为 false",
        )
    if handoff.get("display_strategy_usage") != "internal_creative_brief":
        err(
            "chapter2.handoff_to_chapter3.display_strategy_usage",
            "展示目标必须标记为 internal_creative_brief",
        )
    if set(handoff.get("super_competitiveness_refs") or []) != super_ids:
        err(
            "chapter2.handoff_to_chapter3.super_competitiveness_refs",
            f"必须完整引用全部超级竞争力：{sorted(super_ids)}",
        )

    orphan_customer_decision_ids = customer_decision_ids - used_customer_decision_ids
    if orphan_customer_decision_ids:
        err(
            "customer_decision_registry",
            f"存在未被候选关系、竞争维度、竞争结论或价值锚点消费的机制：{sorted(orphan_customer_decision_ids)}",
        )

    if args.final:
        if meta.get("status") != "final":
            err("meta.status", "正式校验时必须为final")
        serialized = json.dumps(data, ensure_ascii=False)
        for marker in PLACEHOLDER_MARKERS:
            if marker in serialized:
                err("--final", f"仍包含模板占位符：{marker}")

    if errors:
        print(f"FAIL: {len(errors)}项错误", file=sys.stderr)
        for message in errors:
            print(f"- {message}", file=sys.stderr)
        return 1

    print(
        "PASS: 第二章生产消费合同结构有效；"
        f"{len(customer_decision_ids)}项客户决策机制，{len(relations)}组候选／替代关系，"
        f"{len(dimensions)}个竞争维度，{len(conclusion_ids)}条竞争结论，"
        f"{len(advantage_ids)}项收敛优势，{len(super_ids)}条超级竞争力。"
    )
    if not args.final:
        print("提示：当前只完成结构校验；正式生产请增加--final。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
