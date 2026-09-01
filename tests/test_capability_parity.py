#!/usr/bin/env python3
"""P0 capability-parity contract regression tests."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CapabilityParityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.parity = json.loads((ROOT / "CAPABILITY_PARITY_MANIFEST.json").read_text(encoding="utf-8"))

    def test_parity_validator_passes_without_private_source(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verify_capability_parity.py")],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["capabilities"], 18)
        self.assertGreater(result["release_blockers"], 0)

    def test_complete_not_simplified_and_progressive(self) -> None:
        principles = self.parity["principles"]
        self.assertTrue(principles["complete_semantic_parity_required"])
        self.assertTrue(principles["simplified_subset_is_not_acceptable"])
        self.assertTrue(principles["normal_runtime_progressive_loading"])
        self.assertTrue(principles["product1_default_product2_to_5_on_demand"])
        self.assertFalse(principles["empty_disabled_product_files_required"])

    def test_private_material_and_training_routes_are_excluded(self) -> None:
        principles = self.parity["principles"]
        self.assertFalse(principles["real_client_materials_included"])
        self.assertTrue(principles["public_safe_structural_derivatives_required"])
        self.assertFalse(principles["workbuddy_blind_training_included"])
        self.assertFalse(principles["private_evaluation_holdout_included"])

    def test_cross_package_contract_is_explicit(self) -> None:
        interface = self.parity["cross_package_interface"]
        self.assertEqual(interface["upstream_request_schema"], "residential.upstream_task.v0.2")
        self.assertEqual(interface["public_evidence_schema"], "public_evidence_envelope.v1")
        self.assertEqual(interface["upstream_response_schema"], "residential.upstream_response.v0.2")
        self.assertEqual(interface["downstream_adoption_schema"], "residential.upstream_adoption_receipt.v0.2")
        self.assertFalse(interface["shared_cwd_required"])
        self.assertFalse(interface["upstream_fulfilled_equals_downstream_accepted"])
        self.assertFalse(interface["upstream_may_adjudicate_competitor_value_anchor_or_sc"])


if __name__ == "__main__":
    unittest.main()
