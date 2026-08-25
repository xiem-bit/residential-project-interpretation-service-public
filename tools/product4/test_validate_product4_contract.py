#!/usr/bin/env python3

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_product4_contract import load_contract, validate_contract


TEMPLATE = ROOT / "templates" / "产物4价值框架生产消费合同.template.json"


class Product4ContractValidatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.valid = load_contract(TEMPLATE)

    def test_template_structure_is_valid(self) -> None:
        self.assertEqual([], validate_contract(copy.deepcopy(self.valid)))

    def test_requires_both_audiences(self) -> None:
        contract = copy.deepcopy(self.valid)
        contract["task"]["target_audiences"] = ["client_decision_maker"]
        self.assertTrue(any("内部交付团队" in error for error in validate_contract(contract)))

    def test_rejects_global_views(self) -> None:
        contract = copy.deepcopy(self.valid)
        contract["views"] = {"client_confirmation": {}, "internal_production": {}}
        self.assertTrue(any("全局views" in error for error in validate_contract(contract)))

    def test_rejects_parallel_audience_root(self) -> None:
        contract = copy.deepcopy(self.valid)
        contract["business_tree"]["root"]["children"][0]["visible_title"] = "甲方确认层"
        self.assertTrue(any("受众分树" in error for error in validate_contract(contract)))

    def test_rejects_visible_backend_id(self) -> None:
        contract = copy.deepcopy(self.valid)
        contract["business_tree"]["root"]["children"][0]["visible_title"] = "SC-01 黄金中场"
        self.assertTrue(any("后台编号" in error for error in validate_contract(contract)))

    def test_requires_main_branch_visual(self) -> None:
        contract = copy.deepcopy(self.valid)
        contract["business_tree"]["root"]["children"][0]["visual_refs"] = []
        self.assertTrue(any("visual_refs" in error for error in validate_contract(contract)))

    def test_rejects_dangling_visual_reference(self) -> None:
        contract = copy.deepcopy(self.valid)
        contract["business_tree"]["root"]["children"][0]["visual_refs"] = ["VIS-MISSING"]
        self.assertTrue(any("不存在的图证" in error for error in validate_contract(contract)))

    def test_rejects_dangling_module_reference(self) -> None:
        contract = copy.deepcopy(self.valid)
        contract["experience_graph"]["customer_routes"][0]["module_refs"].append("MODULE-MISSING")
        self.assertTrue(any("不存在的模块" in error for error in validate_contract(contract)))

    def test_requires_both_product5_depths(self) -> None:
        contract = copy.deepcopy(self.valid)
        contract["product5_handoff"]["profiles"] = [contract["product5_handoff"]["profiles"][0]]
        self.assertTrue(any("presales_focus" in error for error in validate_contract(contract)))

    def test_strict_requires_actual_visual_file(self) -> None:
        contract = copy.deepcopy(self.valid)
        for key in contract["acceptance"]:
            contract["acceptance"][key] = True
        contract["human_framework_comparison"]["status"] = "complete"
        with tempfile.TemporaryDirectory() as tmp:
            errors = validate_contract(contract, strict=True, base_dir=Path(tmp))
        self.assertTrue(any("实际文件不存在" in error for error in errors))

    def test_strict_requires_actual_semantic_source_file(self) -> None:
        contract = copy.deepcopy(self.valid)
        for key in contract["acceptance"]:
            contract["acceptance"][key] = True
        contract["human_framework_comparison"]["status"] = "complete"
        with tempfile.TemporaryDirectory() as tmp:
            errors = validate_contract(contract, strict=True, base_dir=Path(tmp))
        self.assertTrue(any("上游语义来源不存在" in error for error in errors))

    def test_strict_requires_all_acceptance_items(self) -> None:
        self.assertTrue(any("严格验收" in error for error in validate_contract(self.valid, strict=True)))

    def test_template_is_valid_json(self) -> None:
        with TEMPLATE.open("r", encoding="utf-8") as handle:
            self.assertIsInstance(json.load(handle), dict)


if __name__ == "__main__":
    unittest.main()
