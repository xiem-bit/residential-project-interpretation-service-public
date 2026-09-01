#!/usr/bin/env python3
"""Create a blank production run from public templates and authorized inputs."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_TEMPLATES = {
    "真实项目有效任务合同.md": "project-contract.md",
    "事实冲突缺口登记表.template.json": "fact-conflict-gap-register.json",
    "产物1竞争态势研究.template.md": "product1-competition-study.md",
    "统一语义核.template.json": "semantic-core.json",
    "超级竞争力与制作规划.template.json": "super-competitiveness-plan.json",
    "产物启用矩阵.template.json": "product-enablement-matrix.json",
    "生产回执.template.json": "production-receipt.json",
}

PRODUCT_TEMPLATES = {
    2: {"产物2购买决策研究.template.md": "product2-buyer-decision-study.md"},
    3: {
        "产物3第二章战略合同.template.json": "product3-chapter2-contract.json",
        "产物3第三章UE合同.template.json": "product3-chapter3-contract.json",
        "UE解决方案交接.template.json": "ue-solution-handoff.json",
    },
    4: {"产物4价值框架生产消费合同.template.json": "product4-value-framework-contract.json"},
    5: {"产物5交互蓝图.template.json": "product5-interaction-blueprint.json"},
}

JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def parse_products(value: str) -> set[int]:
    try:
        products = {int(item.strip()) for item in value.split(",") if item.strip()}
    except ValueError as exc:
        raise argparse.ArgumentTypeError("products must be comma-separated integers from 1 to 5") from exc
    if 1 not in products or not products.issubset({1, 2, 3, 4, 5}):
        raise argparse.ArgumentTypeError("Product 1 is required; allowed products are 1 to 5")
    return products


def configure_enablement(output_dir: Path, products: set[int]) -> None:
    matrix_path = output_dir / "product-enablement-matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    deliverables = {
        1: ["product1-competition-study.md"],
        2: ["product2-buyer-decision-study.md"],
        3: ["product3-chapter2-contract.json", "product3-chapter3-contract.json", "ue-solution-handoff.json"],
        4: ["product4-value-framework-contract.json"],
        5: ["product5-interaction-blueprint.json"],
    }
    for item in matrix["products"]:
        product_id = item["product"]
        if product_id == 1:
            item.update(status="complete", reason="住宅研究默认首要", deliverables=deliverables[1])
        elif product_id in products:
            item.update(status="enabled", reason="由本轮初始化参数启用，正式原因须在项目合同中写明", deliverables=deliverables[product_id])
        else:
            item.update(status="not_enabled", reason="本轮未启用", deliverables=[])
    matrix["high_cost_admission"]["status"] = "admitted" if products.intersection({3, 4, 5}) else "research_only"
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    contract_path = output_dir / "project-contract.md"
    text = contract_path.read_text(encoding="utf-8")
    match = JSON_BLOCK.search(text)
    if not match:
        raise RuntimeError("project contract template is missing its JSON summary")
    summary = json.loads(match.group(1))
    summary["enabled_products"] = sorted(products)
    summary["disabled_products"] = [
        {"product": product_id, "reason": "本轮未启用"}
        for product_id in sorted({1, 2, 3, 4, 5} - products)
    ]
    replacement = "```json\n" + json.dumps(summary, ensure_ascii=False, indent=2) + "\n```"
    contract_path.write_text(text[: match.start()] + replacement + text[match.end() :], encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--products", type=parse_products, default={1}, help="enabled products, for example 1,2,3,5; defaults to 1")
    parser.add_argument("--include-change-registry", action="store_true", help="include only when a material semantic change must be tracked")
    args = parser.parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    if not input_dir.is_dir():
        parser.error(f"input directory does not exist: {input_dir}")
    if output_dir.exists():
        parser.error(f"output directory already exists; choose a new path: {output_dir}")
    output_dir.mkdir(parents=True)
    shutil.copytree(input_dir, output_dir / "input")
    templates = dict(CORE_TEMPLATES)
    for product_id in sorted(args.products - {1}):
        templates.update(PRODUCT_TEMPLATES[product_id])
    if args.include_change_registry:
        templates["变更影响登记表.template.json"] = "change-impact-registry.json"
    for source_name, target_name in templates.items():
        shutil.copy2(ROOT / "templates" / source_name, output_dir / target_name)
    configure_enablement(output_dir, args.products)
    print(f"initialized blank production run: {output_dir}")
    print(f"enabled product templates: {','.join(str(item) for item in sorted(args.products))}")
    print("The semantic core remains a blank production output; follow the public workflow to create the business judgments.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
