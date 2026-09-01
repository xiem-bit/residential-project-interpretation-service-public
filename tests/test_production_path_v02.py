#!/usr/bin/env python3
"""Positive and negative tests for the v0.2 business production path."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "production_core"))

from common import validate_all  # noqa: E402


FIXTURE = ROOT / "examples" / "production-path-tutorial" / "expected"


class ProductionPathV02Test(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.temp.name) / "run"
        shutil.copytree(FIXTURE, self.run_dir)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def load(self, name: str):
        return json.loads((self.run_dir / name).read_text(encoding="utf-8"))

    def write(self, name: str, data) -> None:
        (self.run_dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def errors(self, **kwargs):
        return validate_all(self.run_dir, **kwargs)[1]

    def make_product1_only(self) -> None:
        matrix = self.load("product-enablement-matrix.json")
        for item in matrix["products"]:
            product_id = item["product"]
            if product_id == 1:
                continue
            item.update(status="not_enabled", reason="unit test does not enable this product", deliverables=[])
        matrix["high_cost_admission"]["status"] = "research_only"
        self.write("product-enablement-matrix.json", matrix)

        contract_path = self.run_dir / "project-contract.md"
        text = contract_path.read_text(encoding="utf-8")
        text = text.replace('"enabled_products": [1, 2, 3, 5]', '"enabled_products": [1]')
        contract_path.write_text(text, encoding="utf-8")

        semantic = self.load("semantic-core.json")
        semantic["source_outputs"] = ["project-contract.md", "product1-competition-study.md"]
        semantic["product_package"] = {"enabled": [1], "not_enabled": [2, 3, 4, 5]}
        self.write("semantic-core.json", semantic)

        receipt = self.load("production-receipt.json")
        receipt["enabled_products"] = [1]
        receipt["business_statuses"] = {
            "rules_loaded": "pass",
            "project_identity_closed": "pass",
            "product1_complete": "pass",
            "semantic_core_frozen": "pass",
            "minimum_three_sc_pass": "pass",
            "cross_product_consistency_pass": "pass",
        }
        self.write("production-receipt.json", receipt)
        for name in (
            "product2-buyer-decision-study.md",
            "product3-chapter2-contract.json",
            "product3-chapter3-contract.json",
            "ue-solution-handoff.json",
            "product5-interaction-blueprint.json",
        ):
            (self.run_dir / name).unlink()

    def test_complete_tutorial_machine_contract_passes_without_blind_claim(self) -> None:
        self.assertEqual(self.errors(mode="tutorial"), [])

    def test_fewer_than_three_super_competitiveness_items_fail(self) -> None:
        plan = self.load("super-competitiveness-plan.json")
        plan["items"] = plan["items"][:2]
        self.write("super-competitiveness-plan.json", plan)
        self.assertTrue(any("必须有3—4条SC" in error for error in self.errors(mode="tutorial")))

    def test_duplicate_super_competitiveness_mechanism_fails(self) -> None:
        plan = self.load("super-competitiveness-plan.json")
        plan["items"][1]["mechanism"] = plan["items"][0]["mechanism"]
        self.write("super-competitiveness-plan.json", plan)
        self.assertTrue(any("机制重复" in error for error in self.errors(mode="tutorial")))

    def test_competitor_without_acknowledged_strength_fails(self) -> None:
        path = self.run_dir / "product1-competition-study.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace('"strengths": ["距既有轨道站约650米", "成熟商业和学校更集中"]', '"strengths": []', 1)
        path.write_text(text, encoding="utf-8")
        self.assertTrue(any("strengths: 至少一项" in error for error in self.errors(mode="tutorial")))

    def test_boolean_only_five_check_fails(self) -> None:
        plan = self.load("super-competitiveness-plan.json")
        plan["items"][0]["five_checks"]["purchase_impact"] = True
        self.write("super-competitiveness-plan.json", plan)
        self.assertTrue(any("pass必须有解释和引用" in error for error in self.errors(mode="tutorial")))

    def test_chapter3_cannot_drift_from_value_anchor(self) -> None:
        chapter3 = self.load("product3-chapter3-contract.json")
        chapter3["value_anchor"]["text"] = "另一个下游自创价值锚点"
        self.write("product3-chapter3-contract.json", chapter3)
        self.assertTrue(any("价值锚点必须与语义核一致" in error for error in self.errors(mode="tutorial")))

    def test_product5_ai_advisor_cannot_create_new_sc(self) -> None:
        blueprint = self.load("product5-interaction-blueprint.json")
        blueprint["ai_advisor"]["creates_new_sc"] = True
        self.write("product5-interaction-blueprint.json", blueprint)
        self.assertTrue(any("AI推荐官不得新增SC" in error for error in self.errors(mode="tutorial")))

    def test_product1_only_run_passes_without_disabled_product_files(self) -> None:
        self.make_product1_only()
        self.assertEqual(self.errors(mode="tutorial"), [])

    def test_disabled_product_stale_file_fails(self) -> None:
        product2 = (FIXTURE / "product2-buyer-decision-study.md").read_text(encoding="utf-8")
        self.make_product1_only()
        (self.run_dir / "product2-buyer-decision-study.md").write_text(product2, encoding="utf-8")
        self.assertTrue(any("产物2未启用" in error for error in self.errors(mode="tutorial")))

    def test_enabled_product_missing_file_fails(self) -> None:
        (self.run_dir / "product5-interaction-blueprint.json").unlink()
        self.assertTrue(any("产物5已启用但缺少文件" in error for error in self.errors(mode="tutorial")))

    def test_initializer_creates_blank_outputs_not_tutorial_answers(self) -> None:
        output = Path(self.temp.name) / "blank"
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "init_production_run.py"), "--input-dir", str(ROOT / "examples" / "production-path-tutorial" / "input"), "--output-dir", str(output)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue((output / "semantic-core.json").is_file())
        self.assertFalse((output / "product2-buyer-decision-study.md").exists())
        self.assertFalse((output / "product3-chapter2-contract.json").exists())
        self.assertNotIn("SC-ACCESS", (output / "semantic-core.json").read_text(encoding="utf-8"))
        _, errors = validate_all(output)
        self.assertTrue(any("模板占位符" in error for error in errors))

    def test_initializer_creates_only_explicitly_enabled_product_templates(self) -> None:
        output = Path(self.temp.name) / "enabled"
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "init_production_run.py"),
                "--input-dir",
                str(ROOT / "examples" / "production-path-tutorial" / "input"),
                "--output-dir",
                str(output),
                "--products",
                "1,2,3,5",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue((output / "product2-buyer-decision-study.md").is_file())
        self.assertTrue((output / "product3-chapter2-contract.json").is_file())
        self.assertTrue((output / "product5-interaction-blueprint.json").is_file())
        self.assertFalse((output / "product4-value-framework-contract.json").exists())

    def test_revision_tutorial_verifier_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verify_revision_tutorial.py"), str(ROOT / "examples" / "production-path-revision")],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("REVISION TUTORIAL: PASS", completed.stdout)

    def test_authority_manifest_marks_semantic_core_as_output(self) -> None:
        manifest = json.loads((ROOT / "PRODUCTION_PATH_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["semantic_core_role"], "required_production_output_not_bootstrap_input")
        self.assertTrue(manifest["adapter_pass_cannot_satisfy_business_gate"])


if __name__ == "__main__":
    unittest.main()
