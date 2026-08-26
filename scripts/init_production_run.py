#!/usr/bin/env python3
"""Create a blank production run from public templates and authorized inputs."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = {
    "真实项目有效任务合同.md": "project-contract.md",
    "事实冲突缺口登记表.template.json": "fact-conflict-gap-register.json",
    "产物1竞争态势研究.template.md": "product1-competition-study.md",
    "产物2购买决策研究.template.md": "product2-buyer-decision-study.md",
    "统一语义核.template.json": "semantic-core.json",
    "超级竞争力与制作规划.template.json": "super-competitiveness-plan.json",
    "产物启用矩阵.template.json": "product-enablement-matrix.json",
    "产物3第二章战略合同.template.json": "product3-chapter2-contract.json",
    "产物3第三章UE合同.template.json": "product3-chapter3-contract.json",
    "UE解决方案交接.template.json": "ue-solution-handoff.json",
    "产物5交互蓝图.template.json": "product5-interaction-blueprint.json",
    "变更影响登记表.template.json": "change-impact-registry.json",
    "生产回执.template.json": "production-receipt.json",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    if not input_dir.is_dir():
        parser.error(f"input directory does not exist: {input_dir}")
    if output_dir.exists():
        parser.error(f"output directory already exists; choose a new path: {output_dir}")
    output_dir.mkdir(parents=True)
    shutil.copytree(input_dir, output_dir / "input")
    for source_name, target_name in TEMPLATES.items():
        shutil.copy2(ROOT / "templates" / source_name, output_dir / target_name)
    print(f"initialized blank production run: {output_dir}")
    print("The semantic core remains a blank production output; follow the public workflow to create the business judgments.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
