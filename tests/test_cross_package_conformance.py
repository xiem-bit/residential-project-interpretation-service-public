from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CrossPackageConformanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.compatibility = json.loads(
            (ROOT / "external-capabilities" / "cross-package-compatibility.json").read_text(encoding="utf-8")
        )
        self.receipt = json.loads(
            (ROOT / "external-capabilities" / "cross-package-conformance-receipt.json").read_text(encoding="utf-8")
        )

    def test_candidate_interface_is_frozen_and_round_trip_passed(self) -> None:
        self.assertEqual(self.compatibility["status"], "compatible_candidate_frozen")
        self.assertEqual(self.receipt["status"], "pass")
        self.assertTrue(self.receipt["round_trip"]["producer_validated_consumer_fixture"])
        self.assertTrue(self.receipt["round_trip"]["consumer_validated_producer_fixture"])
        self.assertFalse(self.receipt["round_trip"]["fulfilled_equals_accepted"])

    def test_consumer_schema_raw_hashes_are_frozen(self) -> None:
        records = {
            self.compatibility["request_contract"]["schema"]: self.compatibility["request_contract"],
            self.compatibility["response_contract"]["schema"]: self.compatibility["response_contract"],
            self.compatibility["adoption_contract"]["schema"]: self.compatibility["adoption_contract"],
        }
        for schema_id, record in records.items():
            with self.subTest(schema=schema_id):
                path = ROOT / record["path"]
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record["sha256_raw_file_bytes"])
                schema = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(schema["$id"], schema_id)

    def test_producer_hash_and_contract_ids_match_receipt(self) -> None:
        producer = self.compatibility["upstream_evidence_contract"]
        self.assertEqual(producer["schema_sha256"], self.receipt["producer"]["sha256_raw_file_bytes"])
        self.assertEqual(
            {item["schema"] for item in self.receipt["consumer"]["contracts"]},
            {
                "residential.upstream_task.v0.2",
                "residential.upstream_response.v0.2",
                "residential.upstream_adoption_receipt.v0.2",
            },
        )

    def test_receipt_is_portable_and_does_not_overclaim(self) -> None:
        serialized = json.dumps(self.receipt, ensure_ascii=False)
        forbidden = re.compile(r"(?:/" + "Users/|" + "file" + r"://|[A-Za-z]:\\)")
        self.assertIsNone(forbidden.search(serialized))
        boundaries = self.receipt["boundaries"]
        self.assertFalse(boundaries["shared_cwd_required"])
        self.assertFalse(boundaries["platform_opened"])
        self.assertFalse(boundaries["business_acceptance_validated"])
        self.assertFalse(boundaries["release_or_tag_created"])


if __name__ == "__main__":
    unittest.main()
