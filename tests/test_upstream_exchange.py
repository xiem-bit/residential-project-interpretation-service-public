from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "production_core"))

from validate_upstream_exchange import canonical_json_sha256, validate_exchange  # noqa: E402


class UpstreamExchangeTest(unittest.TestCase):
    def setUp(self) -> None:
        fixture_root = ROOT / "fixtures" / "upstream-exchange"
        self.request = json.loads((fixture_root / "request.json").read_text(encoding="utf-8"))
        self.envelope = json.loads((fixture_root / "public-evidence-envelope.json").read_text(encoding="utf-8"))
        self.response = json.loads((fixture_root / "response.json").read_text(encoding="utf-8"))
        self.adoption = json.loads((fixture_root / "adoption-receipt.json").read_text(encoding="utf-8"))

    def test_public_safe_round_trip_passes_before_upstream_freeze(self) -> None:
        receipt = validate_exchange(self.request, self.envelope, self.response, self.adoption)
        self.assertEqual(receipt["status"], "pass", receipt["errors"])
        self.assertEqual(receipt["compatibility_status"], "awaiting_upstream_freeze")
        self.assertTrue(receipt["adoption_checked"])

    def test_response_binds_canonical_envelope_hash(self) -> None:
        self.assertEqual(
            self.response["evidence_envelope"]["content_sha256"],
            canonical_json_sha256(self.envelope),
        )

    def test_upstream_cannot_claim_downstream_acceptance(self) -> None:
        envelope = copy.deepcopy(self.envelope)
        envelope["downstream_acceptance"] = {
            "status": "accepted",
            "decided_by": "public_information_owner",
            "reason": "上游自行宣布采用",
        }
        response = copy.deepcopy(self.response)
        response["evidence_envelope"]["content_sha256"] = canonical_json_sha256(envelope)
        adoption = copy.deepcopy(self.adoption)
        adoption["evidence_package"]["content_sha256"] = canonical_json_sha256(envelope)
        receipt = validate_exchange(self.request, envelope, response, adoption)
        self.assertTrue(any("不得声称下游已经采用" in error for error in receipt["errors"]))

    def test_soft_evidence_cannot_be_adopted_as_hard_fact(self) -> None:
        adoption = copy.deepcopy(self.adoption)
        adoption["accepted_items"][1]["allowed_uses"] = ["project_hard_fact"]
        receipt = validate_exchange(self.request, self.envelope, self.response, adoption)
        self.assertTrue(any("软证据不得升级" in error for error in receipt["errors"]))

    def test_negative_hits_cannot_be_dropped(self) -> None:
        response = copy.deepcopy(self.response)
        response["negative_hits"] = []
        receipt = validate_exchange(self.request, self.envelope, response, self.adoption)
        self.assertTrue(any("不得丢弃、增补或重排上游负命中" in error for error in receipt["errors"]))

    def test_conflicts_and_gaps_cannot_be_hidden(self) -> None:
        adoption = copy.deepcopy(self.adoption)
        adoption["unresolved_conflicts"] = []
        adoption["unresolved_gaps"] = []
        receipt = validate_exchange(self.request, self.envelope, self.response, adoption)
        self.assertTrue(any("必须保留所有未解冲突" in error for error in receipt["errors"]))
        self.assertTrue(any("必须保留所有未解缺口" in error for error in receipt["errors"]))

    def test_incremental_authority_must_come_from_downstream(self) -> None:
        adoption = copy.deepcopy(self.adoption)
        adoption["incremental_decision"]["authorized_query_ids"] = ["unproposed-query"]
        receipt = validate_exchange(self.request, self.envelope, self.response, adoption)
        self.assertTrue(any("只能授权上游已提出" in error for error in receipt["errors"]))

    def test_research_task_cannot_hide_as_simple_direct_retrieval(self) -> None:
        request = copy.deepcopy(self.request)
        request["query_plan"]["mode"] = "simple_direct_retrieval"
        request["query_plan"]["simple_direct_retrieval_exemption"] = {
            "exemption_type": "known_url_read",
            "evidence_target": "某一已知页面",
            "stop_condition": "读完页面",
            "human_authorization_ref": "AUTH-01",
        }
        receipt = validate_exchange(request, self.envelope, self.response, self.adoption)
        self.assertTrue(any("不得伪装成简单定向获取" in error for error in receipt["errors"]))

    def test_frozen_schema_hash_is_enforced_after_compatibility_freeze(self) -> None:
        compatibility = json.loads(
            (ROOT / "external-capabilities" / "cross-package-compatibility.json").read_text(encoding="utf-8")
        )
        compatibility["status"] = "compatible_frozen"
        compatibility["upstream_evidence_contract"]["schema_sha256"] = "a" * 64
        receipt = validate_exchange(self.request, self.envelope, self.response, self.adoption, compatibility)
        self.assertTrue(any("未匹配冻结上游Schema" in error for error in receipt["errors"]))


if __name__ == "__main__":
    unittest.main()
