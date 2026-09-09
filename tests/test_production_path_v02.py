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
        semantic["product_package"] = {"enabled": [1], "not_enabled": [2, 3, 5]}
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
            "product2-buyer-decision-summary.json",
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
        product1 = self.load("product1-competition-summary.json")
        product1["competitors"][0]["strengths"] = []
        self.write("product1-competition-summary.json", product1)
        self.assertTrue(any("strengths: 至少一项" in error for error in self.errors(mode="tutorial")))

    def test_client_reports_are_physically_separate_from_machine_summaries(self) -> None:
        for name in ("product1-competition-study.md", "product2-buyer-decision-study.md"):
            text = (self.run_dir / name).read_text(encoding="utf-8")
            self.assertNotIn("```json", text)
            self.assertNotIn('"schema"', text)
        self.assertTrue((self.run_dir / "product1-competition-summary.json").is_file())
        self.assertTrue((self.run_dir / "product2-buyer-decision-summary.json").is_file())

    def test_client_report_internal_machine_field_fails(self) -> None:
        path = self.run_dir / "product1-competition-study.md"
        path.write_text(path.read_text(encoding="utf-8") + "\n内部 stop_search 已完成。\n", encoding="utf-8")
        self.assertTrue(any("客户正文暴露机器字段" in error for error in self.errors(mode="tutorial")))

    def test_product1_summary_is_required(self) -> None:
        (self.run_dir / "product1-competition-summary.json").unlink()
        self.assertTrue(any("缺少必需文件：product1-competition-summary.json" in error for error in self.errors(mode="tutorial")))

    def test_boolean_only_five_check_fails(self) -> None:
        plan = self.load("super-competitiveness-plan.json")
        plan["items"][0]["five_checks"]["purchase_impact"] = True
        self.write("super-competitiveness-plan.json", plan)
        self.assertTrue(any("pass必须有解释和引用" in error for error in self.errors(mode="tutorial")))

    def test_missing_sc_causal_link_fails(self) -> None:
        plan = self.load("super-competitiveness-plan.json")
        del plan["items"][0]["causal_chain"]["customer_importance"]
        self.write("super-competitiveness-plan.json", plan)
        self.assertTrue(any("必须完整且只能包含六段因果" in error for error in self.errors(mode="tutorial")))

    def test_ue_capability_cannot_be_project_fact(self) -> None:
        plan = self.load("super-competitiveness-plan.json")
        plan["items"][0]["causal_chain"]["project_fact"]["refs"] = ["UE-SC-ACCESS"]
        self.write("super-competitiveness-plan.json", plan)
        self.assertTrue(any("UE能力不能反向充当事实" in error for error in self.errors(mode="tutorial")))

    def test_sc_causal_chain_cannot_self_repeat(self) -> None:
        plan = self.load("super-competitiveness-plan.json")
        repeated = "同一句循环自证"
        for link in plan["items"][0]["causal_chain"].values():
            link["statement"] = repeated
        self.write("super-competitiveness-plan.json", plan)
        self.assertTrue(any("六段不得用同一句循环自证" in error for error in self.errors(mode="tutorial")))

    def test_rejected_inference_cannot_support_sc(self) -> None:
        plan = self.load("super-competitiveness-plan.json")
        plan["items"][0]["inference_link_refs"] = ["INF-SOCIAL-PREVALENCE"]
        self.write("super-competitiveness-plan.json", plan)
        self.assertTrue(any("未接受或未指向本SC" in error for error in self.errors(mode="tutorial")))

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

    def test_independent_product1_needs_no_sc_or_ue_files(self) -> None:
        self.make_product1_only()
        for name in ("semantic-core.json", "super-competitiveness-plan.json"):
            (self.run_dir / name).unlink()
        (self.run_dir / "change-impact-registry.json").unlink(missing_ok=True)
        receipt = self.load("production-receipt.json")
        for key in ("semantic_core_frozen", "minimum_three_sc_pass"):
            receipt["business_statuses"].pop(key, None)
        self.write("production-receipt.json", receipt)
        summary = self.load("product1-competition-summary.json")
        summary["sc_candidates"] = []
        self.write("product1-competition-summary.json", summary)
        self.assertEqual(self.errors(mode="tutorial"), [])

    def test_independent_product2_keeps_research_without_ue_or_product1(self) -> None:
        matrix = self.load("product-enablement-matrix.json")
        for item in matrix["products"]:
            if item["product"] != 2:
                item.update(status="not_enabled", reason="本轮独立产物2", deliverables=[])
        matrix["high_cost_admission"]["status"] = "research_only"
        self.write("product-enablement-matrix.json", matrix)
        contract = self.run_dir / "project-contract.md"
        contract.write_text(contract.read_text().replace('"enabled_products": [1, 2, 3, 5]', '"enabled_products": [2]'))
        semantic = self.load("semantic-core.json")
        semantic["product_package"] = {"enabled": [2], "not_enabled": [1, 3, 5]}
        semantic["source_outputs"] = ["project-contract.md", "product2-buyer-decision-study.md"]
        self.write("semantic-core.json", semantic)
        plan = self.load("super-competitiveness-plan.json")
        for item in plan["items"]:
            item.pop("production_items", None)
            item["five_checks"].pop("ue_provability", None)
            item["causal_chain"].pop("ue_proof", None)
        self.write("super-competitiveness-plan.json", plan)
        for name in ("product1-competition-study.md", "product1-competition-summary.json", "product3-chapter2-contract.json", "product3-chapter3-contract.json", "ue-solution-handoff.json", "product5-interaction-blueprint.json"):
            (self.run_dir / name).unlink()
        receipt = self.load("production-receipt.json")
        receipt["enabled_products"] = [2]
        for key in ("product1_complete", "ue_solution_bridge_pass", "product5_blueprint_pass"):
            receipt["business_statuses"].pop(key, None)
        self.write("production-receipt.json", receipt)
        self.assertEqual(self.errors(mode="tutorial"), [])

    def test_page_reuse_keeps_two_scripts_and_rejects_broken_relations(self) -> None:
        chapter3 = self.load("product3-chapter3-contract.json")
        self.assertEqual(len(chapter3["family_routes"]), 2)
        self.assertEqual(self.errors(mode="tutorial"), [])
        chapter3["system_modules"][1]["ue_pages"][0]["production_item_refs"] = ["MISSING"]
        self.write("product3-chapter3-contract.json", chapter3)
        self.assertTrue(any("production_item_refs" in e for e in self.errors(mode="tutorial")))
        chapter3 = json.loads((FIXTURE / "product3-chapter3-contract.json").read_text())
        chapter3["family_routes"][0]["scenes"][0]["script"] = ""
        self.write("product3-chapter3-contract.json", chapter3)
        self.assertTrue(any(".script" in e for e in self.errors(mode="tutorial")))

    def test_disabled_product_stale_file_fails(self) -> None:
        product2 = (FIXTURE / "product2-buyer-decision-study.md").read_text(encoding="utf-8")
        self.make_product1_only()
        (self.run_dir / "product2-buyer-decision-study.md").write_text(product2, encoding="utf-8")
        self.assertTrue(any("产物2未启用" in error for error in self.errors(mode="tutorial")))

    def test_enabled_product_missing_file_fails(self) -> None:
        (self.run_dir / "product5-interaction-blueprint.json").unlink()
        self.assertTrue(any("缺少必需文件：product5-interaction-blueprint.json" in error for error in self.errors(mode="tutorial")))

    def test_initializer_creates_blank_outputs_not_tutorial_answers(self) -> None:
        output = Path(self.temp.name) / "blank"
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "init_production_run.py"), "--input-dir", str(ROOT / "examples" / "production-path-tutorial" / "input"), "--output-dir", str(output)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse((output / "semantic-core.json").exists())
        self.assertFalse((output / "product2-buyer-decision-study.md").exists())
        self.assertFalse((output / "product2-buyer-decision-summary.json").exists())
        self.assertFalse((output / "product3-chapter2-contract.json").exists())
        self.assertNotIn("SC-ACCESS", (output / "product1-competition-study.md").read_text(encoding="utf-8"))
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
        self.assertTrue((output / "product2-buyer-decision-summary.json").is_file())
        self.assertTrue((output / "product3-chapter2-contract.json").is_file())
        self.assertTrue((output / "product5-interaction-blueprint.json").is_file())
        self.assertFalse((output / "product4-value-framework-contract.json").exists())

    def test_initializer_never_claims_business_completion(self) -> None:
        for products in ("1", "1,2", "2", "1,2,3,5"):
            with self.subTest(products=products):
                output = Path(self.temp.name) / ("honest-" + products)
                completed = subprocess.run(
                    [sys.executable, str(ROOT / "scripts/init_production_run.py"),
                     "--input-dir", str(ROOT / "examples/production-path-tutorial/input"),
                     "--output-dir", str(output), "--products", products],
                    text=True, capture_output=True, check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                contract_text = (output / "project-contract.md").read_text()
                self.assertIn('"identity_status": "pending"', contract_text)
                self.assertIn('"status": "research_in_progress"', contract_text)
                matrix = json.loads((output / "product-enablement-matrix.json").read_text())
                admission = matrix["high_cost_admission"]
                self.assertNotEqual(admission["status"], "admitted")
                self.assertEqual(admission["established_sc_count"], 0)
                self.assertFalse(any(value for value in admission.values() if isinstance(value, bool)))
                receipt = json.loads((output / "production-receipt.json").read_text())
                self.assertEqual(receipt["enabled_products"], sorted(map(int, products.split(","))))
                self.assertEqual(set(receipt["business_statuses"].values()), {"not_run"})
                facts = json.loads((output / "fact-conflict-gap-register.json").read_text())
                self.assertEqual(facts["freeze_status"], "not_frozen")
                self.assertFalse(any(item["status"] == "accepted" for item in facts["entries"]))
                for path in output.glob("*.json"):
                    data = json.loads(path.read_text())
                    self.assertNotIn(data.get("status"), {"complete", "product1_complete", "product2_complete", "semantic_core_frozen", "minimum_three_sc_pass", "ue_solution_bridge_pass"})
                sc_path = output / "super-competitiveness-plan.json"
                if sc_path.exists():
                    plan = json.loads(sc_path.read_text())
                    self.assertTrue(all(item["status"] == "candidate" for item in plan["items"]))
                    self.assertTrue(all(check["status"] == "not_run" for item in plan["items"] for check in item["five_checks"].values()))
                _, errors = validate_all(output)
                self.assertTrue(errors, "An empty initialized run must not pass final acceptance")

    def test_initializer_rejects_product4_in_current_release(self) -> None:
        output = Path(self.temp.name) / "product4-rejected"
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "init_production_run.py"),
                "--input-dir",
                str(ROOT / "examples" / "production-path-tutorial" / "input"),
                "--output-dir",
                str(output),
                "--products",
                "1,4",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Enable only the requested products from 1,2,3,5", completed.stderr)
        self.assertFalse(output.exists())

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
        self.assertEqual(manifest["semantic_core_role"], "current_production_basis_when_task_requires_complete_research_or_solution")
        self.assertNotIn("semantic-core.json", manifest["base_required_run_files"])
        self.assertIn("semantic-core.json", manifest["complete_research_or_solution_files"])
        self.assertTrue(manifest["adapter_pass_cannot_satisfy_business_gate"])


if __name__ == "__main__":
    unittest.main()
