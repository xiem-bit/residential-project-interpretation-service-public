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

    def test_tutorial_cannot_claim_blind_business_pass(self) -> None:
        receipt = self.load("production-receipt.json")
        receipt["business_statuses"]["business_judgment_blind_review_pass"] = "pass"
        receipt["business_statuses"]["production_path_replication_pass"] = "pass"
        receipt["final_status"] = "production_path_replication_pass"
        self.write("production-receipt.json", receipt)
        self.assertTrue(any("教程回执不得声称" in error for error in self.errors(mode="tutorial")))

    def test_replication_pass_requires_review_and_observation_files(self) -> None:
        receipt = self.load("production-receipt.json")
        receipt["run_mode"] = "hidden_answer_replay"
        receipt["candidate_commit"] = "a" * 40
        receipt["business_statuses"]["business_judgment_blind_review_pass"] = "pass"
        receipt["business_statuses"]["production_path_replication_pass"] = "pass"
        receipt["blind_review"].update({"status": "pass", "reviewer_independent": True, "score": 82})
        receipt["final_status"] = "production_path_replication_pass"
        self.write("production-receipt.json", receipt)
        self.assertTrue(any("要求独立盲审文件和观察文件" in error for error in self.errors(require_replication_pass=True)))

    def test_evidence_backed_hidden_replication_receipt_passes_contract(self) -> None:
        scores = {
            "competition_problem": 12,
            "competitor_boundary": 11,
            "buyer_tasks": 10,
            "semantic_core_and_value_anchor": 7,
            "super_competitiveness": 17,
            "five_checks": 8,
            "ue_solution": 10,
            "cross_product_consistency": 3,
            "change_handling": 2,
            "honest_boundaries": 2,
        }
        review = {
            "schema": "residential.hidden_answer_review.v0.2",
            "task_id": "UNIT-HOLDOUT",
            "reviewer_independent": True,
            "rubric": "evaluation/hidden-answer/rubric.json",
            "scores": {key: {"score": value, "evidence": "unit fixture"} for key, value in scores.items()},
            "total": sum(scores.values()),
            "automatic_failures": [],
            "decision": "pass",
        }
        commit = "b" * 40
        input_hash = "c" * 64
        output_hash = "d" * 64
        observation = {
            "schema": "residential.hidden_answer_observation.v0.2",
            "candidate_commit": commit,
            "input_manifest_sha256": input_hash,
            "output_manifest_sha256": output_hash,
            "participant": {"independent_from_release_design": True, "prior_access_to_holdout_answer": False},
            "content_guidance_count": 0,
            "final_status": "production_path_replication_pass",
        }
        self.write("blind-review.json", review)
        self.write("cold-start-observation.json", observation)
        receipt = self.load("production-receipt.json")
        receipt.update({"run_mode": "hidden_answer_replay", "candidate_commit": commit, "input_manifest_sha256": input_hash, "output_manifest_sha256": output_hash, "final_status": "production_path_replication_pass"})
        receipt["business_statuses"]["business_judgment_blind_review_pass"] = "pass"
        receipt["business_statuses"]["production_path_replication_pass"] = "pass"
        receipt["blind_review"].update({"status": "pass", "reviewer_independent": True, "score": 82, "review_file": "blind-review.json", "observation_file": "cold-start-observation.json"})
        self.write("production-receipt.json", receipt)
        self.assertEqual(self.errors(require_replication_pass=True), [])

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
        self.assertNotIn("SC-ACCESS", (output / "semantic-core.json").read_text(encoding="utf-8"))
        _, errors = validate_all(output)
        self.assertTrue(any("模板占位符" in error for error in errors))

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
