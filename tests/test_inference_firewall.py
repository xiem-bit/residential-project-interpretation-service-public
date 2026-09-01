from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "production_core"))

from inference_firewall import evaluate_case, load_relationships, validate_inference_register  # noqa: E402


class InferenceFirewallTest(unittest.TestCase):
    def test_all_public_cases_match_relation_contract(self) -> None:
        cases = json.loads((ROOT / "fixtures" / "inference-harness" / "cases.json").read_text(encoding="utf-8"))
        table = load_relationships()
        for case in cases["cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(evaluate_case(case, table), case["expected"])

    def test_table_covers_every_approved_high_risk_relation(self) -> None:
        relation_ids = {item["id"] for item in load_relationships()["relations"]}
        self.assertTrue(
            {
                "REL-NONPROBABILITY-SOCIAL",
                "REL-COUNTEREXAMPLE",
                "REL-OPEN-WAITING",
                "REL-FUTURE-STATUS",
                "REL-SPATIAL-EXISTENCE",
                "REL-FEATURE-ATTRIBUTE",
                "REL-BRAND-PARTICIPATION",
                "REL-UE-CAPABILITY",
            }.issubset(relation_ids)
        )

    def test_forbidden_relation_cannot_be_marked_allowed(self) -> None:
        register = {
            "entries": [
                {
                    "id": "E-SOCIAL",
                    "evidence_roles": ["nonprobability_social_sample"],
                }
            ],
            "inference_links": [
                {
                    "id": "INF-01",
                    "relation_id": "REL-NONPROBABILITY-SOCIAL",
                    "source_refs": ["E-SOCIAL"],
                    "target_claim": "多数客户都这样认为",
                    "target_level": "population_prevalence",
                    "boundary": "不适用",
                    "bridge_refs": [],
                    "decision": "allowed_bounded",
                    "target_refs": ["SC-01"],
                }
            ],
        }
        errors: list[str] = []
        validate_inference_register(register, errors)
        self.assertTrue(any("禁止推导必须rejected" in error for error in errors))

    def test_bridge_cannot_be_same_high_risk_source_type(self) -> None:
        register = {
            "entries": [
                {"id": "E-FEATURE-1", "kind": "fact", "evidence_roles": ["feature_attribute"]},
                {"id": "E-FEATURE-2", "kind": "fact", "evidence_roles": ["feature_attribute"]},
            ],
            "inference_links": [
                {
                    "id": "INF-01",
                    "relation_id": "REL-FEATURE-ATTRIBUTE",
                    "source_refs": ["E-FEATURE-1"],
                    "target_claim": "可以直接推出真实使用效果",
                    "target_level": "actual_use_outcome",
                    "boundary": "测试",
                    "bridge_refs": ["E-FEATURE-2"],
                    "decision": "allowed_with_bridge",
                    "target_refs": ["SC-01"],
                }
            ],
        }
        errors: list[str] = []
        validate_inference_register(register, errors)
        self.assertTrue(any("不能只用同类高风险来源自我补桥" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
