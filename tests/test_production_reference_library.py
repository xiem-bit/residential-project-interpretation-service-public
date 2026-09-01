#!/usr/bin/env python3
"""Production-reference and learning-feedback public library checks."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "references" / "production-reference-index.json"
FEEDBACK_PATH = ROOT / "references" / "learning-feedback" / "cases.json"


class ProductionReferenceLibraryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        self.references = self.index["references"]

    def test_reference_index_has_unique_routable_public_paths(self) -> None:
        self.assertEqual(self.index["schema"], "residential.production_reference_index.v1")
        ids = [item["id"] for item in self.references]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(self.references), 6)
        for item in self.references:
            self.assertIn(item["type"], {"production_reference", "learning_feedback", "regression_fixture"})
            self.assertTrue(item["load_when"])
            self.assertTrue(item["mechanisms"])
            self.assertFalse(item["may_supply_project_facts"])
            self.assertTrue((ROOT / item["path"]).exists(), item["path"])

    def test_two_mechanism_distinct_complete_projects_pass(self) -> None:
        projects = [item for item in self.references if item["stage"].startswith("end_to_end_")]
        self.assertGreaterEqual(len(projects), 2)
        mechanism_sets = [set(item["mechanisms"]) for item in projects]
        self.assertTrue(mechanism_sets[0].isdisjoint(mechanism_sets[1]))
        expected_dirs = [
            ROOT / "examples" / "production-path-tutorial" / "expected",
            ROOT / "examples" / "end-to-end-public-safe" / "fictional-wangchuan-xu" / "expected",
        ]
        for expected in expected_dirs:
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "verify_production_run.py"), str(expected), "--mode", "tutorial"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)

    def test_learning_feedback_preserves_reason_and_transfer_boundary(self) -> None:
        feedback = json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))
        self.assertEqual(feedback["schema"], "residential.learning_feedback.v1")
        cases = feedback["cases"]
        self.assertGreaterEqual(len(cases), 8)
        ids = [item["id"] for item in cases]
        self.assertEqual(len(ids), len(set(ids)))
        for item in cases:
            for field in ("stage", "before_problem", "human_revision", "transferable_reason", "do_not_transfer", "resulting_rule_refs"):
                self.assertTrue(item[field], f"{item['id']}.{field}")
            for relative in item["resulting_rule_refs"]:
                self.assertTrue((ROOT / relative).exists(), relative)

    def test_library_contains_no_evaluation_holdout_or_product4_reference(self) -> None:
        paths = [item["path"] for item in self.references]
        self.assertFalse(any("evaluation" in path or "holdout" in path for path in paths))
        self.assertFalse(any("product4" in path.lower() or "产物4" in path for path in paths))


if __name__ == "__main__":
    unittest.main()

