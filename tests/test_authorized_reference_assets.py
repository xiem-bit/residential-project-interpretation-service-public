from __future__ import annotations

import hashlib
import json
import re
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "references/authorized-reference-assets.json").read_text(encoding="utf-8"))


class AuthorizedReferenceAssetsTests(unittest.TestCase):
    def test_exact_library_counts_and_source_decks(self) -> None:
        page_root = ROOT / MANIFEST["page_template_library"]["path"]
        case_root = ROOT / MANIFEST["case_asset_library"]["path"]
        self.assertEqual(sum(path.is_file() for path in page_root.rglob("*")), 124)
        self.assertEqual(sum(path.is_file() for path in case_root.rglob("*")), 229)
        expected = MANIFEST["page_template_library"]["source_decks"]
        self.assertEqual(len(expected), 3)
        self.assertEqual(sum(item["slides"] for item in expected), 76)
        sensitive = re.compile(rb"/Users/|file://|[A-Za-z]:\\\\|verification-tmp|worktree|password|passwd|api[_-]?key|cookie", re.I)
        for item in expected:
            deck = page_root / item["file"]
            self.assertEqual(hashlib.sha256(deck.read_bytes()).hexdigest(), item["sha256"])
            with zipfile.ZipFile(deck) as archive:
                slides = [name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
                self.assertEqual(len(slides), item["slides"])
                for name in archive.namelist():
                    if not name.startswith("ppt/media/"):
                        self.assertIsNone(sensitive.search(archive.read(name)), f"{deck.name}:{name}")

    def test_case_inventory_resolves_all_originals(self) -> None:
        inventory_path = ROOT / MANIFEST["case_asset_library"]["inventory"]
        records = json.loads(inventory_path.read_text(encoding="utf-8"))
        self.assertEqual(len(records), 224)
        self.assertEqual(len({item["asset_id"] for item in records}), 224)
        for item in records:
            self.assertTrue((ROOT / item["original_asset"]).is_file(), item["asset_id"])

    def test_complete_writing_assets_and_learning_samples(self) -> None:
        writing = ROOT / MANIFEST["writing_library"]["path"]
        marketing = json.loads((writing / "营销文案表达库/datasets/marketing_copy_reference.v0.1.json").read_text(encoding="utf-8"))
        external = json.loads((writing / "营销文案表达库/datasets/hpsj_value_expression_reference.v0.2.json").read_text(encoding="utf-8"))
        samples = json.loads((writing / "human-revision-style-samples.json").read_text(encoding="utf-8"))
        feedback = json.loads((ROOT / "references/learning-feedback/human_revision_feedback.v0.1.json").read_text(encoding="utf-8"))
        self.assertEqual(marketing["qualitySummary"]["projectCount"], 100)
        self.assertEqual(marketing["qualitySummary"]["expressionCount"], 500)
        self.assertEqual(marketing["qualitySummary"]["writingRuleCount"], 10)
        self.assertEqual(len(external["articles"]), 16)
        self.assertEqual(len(external["patterns"]), 22)
        self.assertEqual(len(samples["samples"]), 10)
        self.assertEqual(len(feedback["entries"]), 10)
        required = (
            ROOT / "workflows/chinese-research-report-editor/SKILL.md",
            ROOT / "workflows/chinese-research-report-editor/scripts/audit_chinese_report.py",
            ROOT / "workflows/chinese-affirmative-business-editor/SKILL.md",
            writing / "16-断言式书写规范_v1.0.md",
        )
        self.assertTrue(all(path.is_file() for path in required))
        for path in writing.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".json"}:
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"/Users/|file://|verification-tmp|worktree")

    def test_external_runtime_is_prompted_not_bundled(self) -> None:
        install = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        for phrase in ("PPT生成引擎", "Grist", "Computer Use", "浏览器", "地图", "微信", "小红书", "自行安装", "自行登录"):
            self.assertIn(phrase, install)
        self.assertFalse((ROOT / "tools/product3_assembly_console").exists())
        self.assertEqual(
            set(MANIFEST["external_runtime_not_bundled"]),
            {"presentation_engine", "grist", "computer_use", "browser", "map_service", "wechat_login", "xiaohongshu_login", "publishing_accounts"},
        )


if __name__ == "__main__":
    unittest.main()
