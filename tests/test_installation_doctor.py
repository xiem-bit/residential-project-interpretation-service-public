#!/usr/bin/env python3
"""Installation doctor and structured carrier-gap checks."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check_environment.py"
SPEC = importlib.util.spec_from_file_location("installation_doctor", MODULE_PATH)
assert SPEC and SPEC.loader
DOCTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOCTOR)


class InstallationDoctorTest(unittest.TestCase):
    def test_production_core_doctor_passes_without_node(self) -> None:
        with mock.patch.object(DOCTOR.shutil, "which", return_value=None):
            report = DOCTOR.check_environment("production-core")
        self.assertEqual(report["schema"], "residential.public_installation_doctor.v1")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["gaps"], [])
        self.assertNotIn("node", report["checks"])

    def test_product3_gold_reference_is_packaged_and_valid(self) -> None:
        report = DOCTOR.check_environment("product3")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["checks"]["product3_gold_reference"]["status"], "pass")
        self.assertIn("20 slides", report["checks"]["product3_gold_reference"]["detail"])

    def test_product5_missing_node_returns_actionable_gap(self) -> None:
        with mock.patch.object(DOCTOR.shutil, "which", return_value=None):
            report = DOCTOR.check_environment("product5")
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["checks"]["node"]["status"], "fail")
        self.assertTrue(any(item["scope"] == "node" and item["action"] for item in report["gaps"]))

    def test_adapter_gap_template_uses_existing_contract(self) -> None:
        template = json.loads((ROOT / "templates" / "平台适配与能力缺口回传.template.json").read_text(encoding="utf-8"))
        self.assertEqual(template["schema"], "residential.platform_adapter_contract.v0.2")
        self.assertEqual(template["adapter_status"], "gap")
        self.assertTrue(template["gaps"])
        self.assertFalse(template["gaps"][0]["blocks_business_core"])


if __name__ == "__main__":
    unittest.main()
