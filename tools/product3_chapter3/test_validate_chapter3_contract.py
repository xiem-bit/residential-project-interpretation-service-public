from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "templates/产物3第三章生产消费合同.template.json"
VALIDATOR = ROOT / "tools/product3_chapter3/validate_chapter3_contract.py"


class Chapter3ContractTest(unittest.TestCase):
    def run_contract(self, mutate=None):
        data = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        if mutate:
            mutate(data)
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as fh:
            json.dump(data, fh, ensure_ascii=False)
            path = Path(fh.name)
        result = subprocess.run(["python3", str(VALIDATOR), str(path)], capture_output=True, text=True)
        path.unlink(missing_ok=True)
        return result

    def test_template_passes(self):
        result = self.run_contract()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_anchor_visualization_fails(self):
        result = self.run_contract(lambda d: d["meta"].__setitem__("value_anchor_visualization_service", True))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("必须明确为 false", result.stderr)

    def test_internal_term_in_visible_title_fails(self):
        def mutate(data):
            data["chapter3"]["family_routes"][0]["scenes"][0]["visible_title"] = "进入客户分流"

        result = self.run_contract(mutate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("客户分流", result.stderr)

    def test_missing_product5_mapping_fails(self):
        def mutate(data):
            data["chapter3"]["family_routes"][0]["scenes"][0]["product5_target"] = ""

        result = self.run_contract(mutate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("缺少产物5", result.stderr)

    def test_bounded_superlative_is_required(self):
        def mutate(data):
            del data["chapter3"]["common_project_answer"][
                "super_competitiveness_sections"
            ][0]["bounded_superlative"]

        result = self.run_contract(mutate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("必须承接第二章的比较对象、购买任务", result.stderr)

    def test_two_competitiveness_sections_are_rejected(self):
        result = self.run_contract(
            lambda d: d["chapter3"]["common_project_answer"][
                "super_competitiveness_sections"
            ].pop()
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("必须登记3—4条超级竞争力", result.stderr)

    def test_four_competitiveness_sections_are_supported(self):
        def mutate(data):
            section = deepcopy(
                data["chapter3"]["common_project_answer"][
                    "super_competitiveness_sections"
                ][-1]
            )
            section["source_ref"] = "SC-BRAND"
            section["text"] = "品牌信任形成第四条超级竞争力"
            section["customer_gain"] = "客户获得更清楚的长期兑现预期"
            for index, scene in enumerate(section["ue_scenes"]):
                scene["id"] = f"SC-BRAND-S{index + 1}"
            data["chapter3"]["common_project_answer"][
                "super_competitiveness_sections"
            ].append(section)

        result = self.run_contract(mutate)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
