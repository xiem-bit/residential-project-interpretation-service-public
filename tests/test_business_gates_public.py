from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = ROOT / "tools" / "product3_ppt_pipeline"
sys.path.insert(0, str(PIPELINE_DIR))

from business_gates import (  # noqa: E402
    duplicate_sequence_errors,
    internal_method_hits,
    is_audience_portrait,
    rank_portrait_assets,
    required_portrait_count,
)


class PublicBusinessGateTests(unittest.TestCase):
    def test_internal_method_copy_is_detected(self) -> None:
        page = {
            "页面名称": "家庭选择",
            "页面文案": "把四种选择放进同一价值账重新排序。",
        }
        self.assertIn("价值账", internal_method_hits(page))

    def test_duplicate_pages_without_new_evidence_are_rejected(self) -> None:
        pages = [
            {
                "页面ID": "PAGE-001",
                "页面语义ID": "SEMANTIC-PROOF",
                "来源页ID": "SOURCE-A",
                "视觉结构": "双图证明",
                "素材编号": "",
            },
            {
                "页面ID": "PAGE-002",
                "页面语义ID": "SEMANTIC-PROOF",
                "来源页ID": "SOURCE-A",
                "视觉结构": "双图证明",
                "素材编号": "",
            },
        ]
        errors = duplicate_sequence_errors(pages)
        self.assertEqual(len(errors), 1)
        self.assertIn("PAGE-001", errors[0])
        self.assertIn("PAGE-002", errors[0])

    def test_portrait_routing_uses_business_semantics(self) -> None:
        assets = [
            {
                "asset_id": "ASSET-TEAM",
                "effective_business_semantic": "设计团队与机构背书",
                "asset_class": "case_reference",
            },
            {
                "asset_id": "ASSET-FAMILY",
                "effective_business_semantic": "年轻夫妻与亲子家庭肖像",
                "asset_class": "audience_portrait",
            },
        ]
        self.assertFalse(is_audience_portrait(assets[0]))
        self.assertTrue(is_audience_portrait(assets[1]))
        ranked = rank_portrait_assets(
            {
                "页面名称": "年轻夫妻家庭",
                "页面文案": "亲子家庭完成居住升级",
                "这一页只负责": "识别家庭角色",
                "视觉结构": "家庭肖像卡",
            },
            assets,
        )
        self.assertEqual([item["asset_id"] for item in ranked], ["ASSET-FAMILY"])

    def test_family_page_requires_three_portraits_when_declared(self) -> None:
        page = {
            "页面语义ID": "P3-FAMILY-SEGMENT",
            "页面名称": "三类家庭",
            "页面文案": "三类家庭对应三种居住任务。",
            "这一页只负责": "说明家庭差异",
            "视觉结构": "三组家庭角色卡",
        }
        self.assertEqual(required_portrait_count(page), 3)


if __name__ == "__main__":
    unittest.main()
