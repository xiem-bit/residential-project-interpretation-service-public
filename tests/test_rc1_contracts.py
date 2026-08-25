#!/usr/bin/env python3
"""Focused negative and positive tests for RC1 public contracts."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.rc1.build_demo_contracts import build_presentation_request, build_product5_config, load_json  # noqa: E402
from tools.rc1.validate_rc1_contracts import (  # noqa: E402
    ContractError,
    assert_no_private_paths,
    validate_presentation_request,
    validate_product5_config,
    validate_semantic_core,
)


FIXTURE = ROOT / "examples/fictional-qinglan-chengjing"


class Rc1ContractsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.core = load_json(FIXTURE / "work/semantic_core.json")
        cls.gaps = load_json(FIXTURE / "input/evidence_gaps.json")

    def test_approved_fictional_semantic_core_is_valid(self) -> None:
        validate_semantic_core(self.core)

    def test_presentation_request_preserves_all_super_competitiveness_ids(self) -> None:
        request = build_presentation_request(self.core)
        validate_presentation_request(request)
        self.assertEqual(
            set(request["semantic_core"]["super_competitiveness_ids"]),
            {"SC-ACCESS", "SC-CONTINUITY", "SC-FLEXIBILITY"},
        )

    def test_product5_consumes_the_same_semantic_core(self) -> None:
        config = build_product5_config(self.core, self.gaps)
        validate_product5_config(config, {"SC-ACCESS", "SC-CONTINUITY", "SC-FLEXIBILITY"})

    def test_semantic_core_rejects_fewer_than_three_competitiveness_items(self) -> None:
        broken = copy.deepcopy(self.core)
        broken["dimensions"] = broken["dimensions"][:2]
        with self.assertRaises(ContractError):
            validate_semantic_core(broken)

    def test_presentation_request_rejects_unknown_super_competitiveness_reference(self) -> None:
        broken = build_presentation_request(self.core)
        broken["pages"][0]["super_competitiveness_refs"].append("SC-UNKNOWN")
        with self.assertRaises(ContractError):
            validate_presentation_request(broken)

    def test_private_absolute_path_is_rejected(self) -> None:
        with self.assertRaises(ContractError):
            assert_no_private_paths({"artifact": "/Users/example/private.pptx"})

    def test_https_repository_url_is_not_misread_as_windows_path(self) -> None:
        assert_no_private_paths(
            {
                "repository": (
                    "https://github.com/xiem-bit/"
                    "residential-project-interpretation-service-public"
                )
            }
        )


if __name__ == "__main__":
    unittest.main()
