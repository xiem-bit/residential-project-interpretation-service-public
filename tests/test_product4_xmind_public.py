from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "product4" / "validate_product4_xmind.py"
SPEC = importlib.util.spec_from_file_location("validate_product4_xmind", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PublicProduct4XMindTests(unittest.TestCase):
    def write_xmind(self, destination: Path, top_title: str = "客户价值") -> None:
        root = {
            "title": "住宅价值框架",
            "children": {
                "attached": [
                    {
                        "title": top_title,
                        "children": {
                            "attached": [
                                {
                                    "title": "项目图证",
                                    "image": {"src": "xap:resources/proof.png"},
                                },
                                {
                                    "title": "页面与制作展开",
                                    "branch": "folded",
                                },
                            ]
                        },
                    }
                ]
            },
        }
        content = [{"rootTopic": root}]
        with zipfile.ZipFile(destination, "w") as archive:
            archive.writestr("content.json", json.dumps(content, ensure_ascii=False))
            archive.writestr("metadata.json", "{}")
            archive.writestr("manifest.json", "{}")
            archive.writestr("resources/proof.png", b"synthetic-proof")

    def validate_fixture(self, top_title: str = "客户价值") -> list[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            xmind_file = Path(temp_dir) / "synthetic.xmind"
            self.write_xmind(xmind_file, top_title)
            errors, _inventory = MODULE.validate(
                xmind_file,
                min_topics=4,
                min_images=1,
                min_depth=3,
                expected_top_branches=1,
            )
            return errors

    def test_synthetic_single_tree_passes(self) -> None:
        self.assertEqual([], self.validate_fixture())

    def test_audience_split_top_branch_is_rejected(self) -> None:
        errors = self.validate_fixture("甲方确认层")
        self.assertTrue(any("禁止受众分树" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
