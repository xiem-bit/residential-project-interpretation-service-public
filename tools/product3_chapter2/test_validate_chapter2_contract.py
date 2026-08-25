#!/usr/bin/env python3
"""Regression tests for the Product 3 Chapter 2 production contract."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools/product3_chapter2/validate_chapter2_contract.py"
TEMPLATE = ROOT / "templates/产物3第二章生产消费合同.template.json"


class Chapter2ContractValidatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def run_contract(self, contract: dict) -> subprocess.CompletedProcess[str]:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as handle:
            json.dump(contract, handle, ensure_ascii=False)
            handle.flush()
            return subprocess.run(
                [sys.executable, str(VALIDATOR), handle.name],
                check=False,
                capture_output=True,
                text=True,
            )

    def test_template_passes_structural_validation(self) -> None:
        result = self.run_contract(deepcopy(self.template))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("3项客户决策机制", result.stdout)

    def test_conclusion_requires_customer_decision_reference(self) -> None:
        contract = deepcopy(self.template)
        del contract["chapter2"]["dimensions"][0]["conclusions"][0]["customer_decision_refs"]
        result = self.run_contract(contract)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("至少引用一项客户决策机制", result.stderr)

    def test_advantage_requires_customer_progress(self) -> None:
        contract = deepcopy(self.template)
        del contract["chapter2"]["advantage_matrix"]["columns"][0]["items"][0]["customer_progress"]
        result = self.run_contract(contract)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("customer_progress", result.stderr)

    def test_bounded_superlative_is_required(self) -> None:
        contract = deepcopy(self.template)
        del contract["chapter2"]["advantage_matrix"]["columns"][0][
            "super_competitiveness"
        ]["bounded_superlative"]
        result = self.run_contract(contract)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("必须结构化登记比较对象、购买任务", result.stderr)

    def test_customer_segments_are_rejected_in_chapter2(self) -> None:
        contract = deepcopy(self.template)
        contract["chapter2"]["customer_segments"] = ["不应进入第二章"]
        result = self.run_contract(contract)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("必须进入第三章", result.stderr)

    def test_candidate_relations_are_required(self) -> None:
        contract = deepcopy(self.template)
        del contract["chapter2"]["candidate_and_substitute_relations"]
        result = self.run_contract(contract)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("缺少客户候选与替代关系", result.stderr)

    def test_anchor_visualization_service_is_rejected(self) -> None:
        contract = deepcopy(self.template)
        contract["chapter2"]["handoff_to_chapter3"]["value_anchor_visualization_service"] = True
        result = self.run_contract(contract)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("可视化服务必须为 false", result.stderr)

    def test_two_competitiveness_groups_are_rejected(self) -> None:
        contract = deepcopy(self.template)
        contract["meta"]["dimension_plan"] = {
            "default_order_used": False,
            "change_reason": "本项目只需区域与产品两个竞争维度",
        }
        removed_dimension = contract["chapter2"]["dimensions"].pop(1)
        removed_column = contract["chapter2"]["advantage_matrix"]["columns"].pop(1)
        removed_advantage_ids = {item["id"] for item in removed_column["items"]}
        removed_super_id = removed_column["super_competitiveness"]["id"]
        anchor = contract["chapter2"]["value_anchor"]
        anchor["advantage_item_refs"] = [
            ref for ref in anchor["advantage_item_refs"] if ref not in removed_advantage_ids
        ]
        anchor["super_competitiveness_refs"] = [
            ref for ref in anchor["super_competitiveness_refs"] if ref != removed_super_id
        ]
        contract["chapter2"]["handoff_to_chapter3"]["super_competitiveness_refs"] = [
            ref
            for ref in contract["chapter2"]["handoff_to_chapter3"]["super_competitiveness_refs"]
            if ref != removed_super_id
        ]
        for strategy in contract["chapter2"]["display_strategy"].values():
            strategy["advantage_item_refs"] = [
                ref for ref in strategy["advantage_item_refs"] if ref not in removed_advantage_ids
            ]
        removed_dimension_id = removed_dimension["id"]
        self.assertEqual(removed_dimension_id, "PLAN")
        result = self.run_contract(contract)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("必须包含3—4组优势", result.stderr)

    def test_four_competitiveness_groups_are_supported(self) -> None:
        contract = deepcopy(self.template)
        contract["meta"]["dimension_plan"] = {
            "default_order_used": False,
            "change_reason": "本项目增加品牌维度，形成四组竞争力",
        }

        def replace_tokens(value, replacements):
            if isinstance(value, str):
                for source, target in replacements:
                    value = value.replace(source, target)
                return value
            if isinstance(value, list):
                return [replace_tokens(item, replacements) for item in value]
            if isinstance(value, dict):
                return {
                    key: replace_tokens(item, replacements)
                    for key, item in value.items()
                }
            return value

        new_dimension = replace_tokens(
            deepcopy(contract["chapter2"]["dimensions"][-1]),
            [("UNIT", "BRAND")],
        )
        new_dimension["name"] = "品牌"
        new_dimension["order"] = 4
        new_dimension["advantage_column_id"] = "BRAND"
        contract["chapter2"]["dimensions"].append(new_dimension)

        new_column = replace_tokens(
            deepcopy(contract["chapter2"]["advantage_matrix"]["columns"][-1]),
            [("ADV-U", "ADV-B"), ("SC-PRODUCT", "SC-BRAND"), ("PRODUCT", "BRAND"), ("UNIT", "BRAND")],
        )
        new_column["label"] = "品牌信任"
        new_column["super_competitiveness"]["text"] = "[范围／板块]最具信任基础的品牌答案"
        contract["chapter2"]["advantage_matrix"]["columns"].append(new_column)

        new_advantage_ids = [item["id"] for item in new_column["items"]]
        anchor = contract["chapter2"]["value_anchor"]
        anchor["advantage_item_refs"].extend(new_advantage_ids)
        anchor["super_competitiveness_refs"].append("SC-BRAND")
        contract["chapter2"]["handoff_to_chapter3"]["super_competitiveness_refs"].append(
            "SC-BRAND"
        )

        result = self.run_contract(contract)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("4条超级竞争力", result.stdout)


if __name__ == "__main__":
    unittest.main()
