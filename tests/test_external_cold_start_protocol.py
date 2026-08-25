#!/usr/bin/env python3
"""Tests that external cold-start evidence cannot be replaced by the local test double."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_external_cold_start import (  # noqa: E402
    ContractError,
    assert_external_platform_claim,
    validate_observation,
    validate_presentation_visual_review,
)


class ExternalColdStartProtocolTest(unittest.TestCase):
    def setUp(self) -> None:
        self.observation = json.loads(
            (ROOT / "cold-start/observation.template.json").read_text(encoding="utf-8")
        )

    def test_unfilled_observation_is_rejected(self) -> None:
        with self.assertRaises(ContractError):
            validate_observation(self.observation)

    def test_completed_zero_content_guidance_observation_passes(self) -> None:
        complete = copy.deepcopy(self.observation)
        complete["status"] = "complete"
        complete["tester_label"] = "external-colleague"
        complete["platform"]["workbuddy_agent_label"] = "workbuddy-test-agent"
        complete["platform"]["skills_selected_by_workbuddy"] = ["presentation", "web-preview"]
        complete["tester_attestation"] = "仅从固定GitHub tag完成冷启动，未获得工程内容指导。"
        validate_observation(complete)

    def test_local_test_double_cannot_claim_workbuddy_pass(self) -> None:
        response = {
            "status": "test_double_complete",
            "producer": {
                "platform": "standard_node_pptxgenjs",
                "formal_visual_renderer": False,
            },
            "gaps": [{"blocking_for_real_client_delivery": True}],
        }
        with self.assertRaises(ContractError):
            assert_external_platform_claim(response)

    def test_visual_review_requires_every_page_preview(self) -> None:
        page_ids = [f"P3-{index:02d}" for index in range(1, 9)]
        review = {
            "schema": "residential.presentation_visual_review.v0.1",
            "status": "pass",
            "platform": "WorkBuddy",
            "formal_visual_review": "pass",
            "pages": [
                {
                    "page_id": page_id,
                    "status": "pass",
                    "preview_path": f"previews/{page_id}.png",
                    "overflow": "none",
                }
                for page_id in page_ids
            ],
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "previews").mkdir()
            for page_id in page_ids[:-1]:
                (root / f"previews/{page_id}.png").write_bytes(b"synthetic-preview")
            with self.assertRaises(ContractError):
                validate_presentation_visual_review(review, root, page_ids)
            (root / f"previews/{page_ids[-1]}.png").write_bytes(b"synthetic-preview")
            validate_presentation_visual_review(review, root, page_ids)


if __name__ == "__main__":
    unittest.main()

