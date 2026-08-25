from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
T2 = ROOT / "templates/产物3第二章生产消费合同.template.json"
T3 = ROOT / "templates/产物3第三章生产消费合同.template.json"
VALIDATOR = ROOT / "tools/product3_chapter23/validate_chapter23_bridge.py"


def aligned_contracts():
    c2 = json.loads(T2.read_text(encoding="utf-8"))
    c3 = json.loads(T3.read_text(encoding="utf-8"))
    c3["meta"]["project_id"] = c2["meta"]["project_id"]
    c3["chapter3"]["value_anchor"]["text"] = c2["chapter2"]["value_anchor"]["text"]
    source = {
        item["super_competitiveness"]["id"]: item["super_competitiveness"]["text"]
        for item in c2["chapter2"]["advantage_matrix"]["columns"]
    }
    for section in c3["chapter3"]["common_project_answer"]["super_competitiveness_sections"]:
        section["text"] = source[section["source_ref"]]
    return c2, c3


class Chapter23BridgeTest(unittest.TestCase):
    def run_contracts(self, mutate=None):
        c2, c3 = aligned_contracts()
        if mutate:
            mutate(c2, c3)
        paths = []
        for data in (c2, c3):
            with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as fh:
                json.dump(data, fh, ensure_ascii=False)
                paths.append(Path(fh.name))
        result = subprocess.run(["python3", str(VALIDATOR), str(paths[0]), str(paths[1])], capture_output=True, text=True)
        for path in paths:
            path.unlink(missing_ok=True)
        return result

    def test_aligned_templates_pass(self):
        result = self.run_contracts()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_changed_anchor_fails(self):
        result = self.run_contracts(lambda _c2, c3: c3["chapter3"]["value_anchor"].__setitem__("text", "改写后的锚点"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("价值锚点文本", result.stderr)

    def test_changed_super_competitiveness_fails(self):
        def mutate(_c2, c3):
            c3["chapter3"]["common_project_answer"]["super_competitiveness_sections"][0]["text"] = "改写后的竞争力"

        result = self.run_contracts(mutate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("超级竞争力文本发生改写", result.stderr)

    def test_changed_bounded_superlative_fails(self):
        def mutate(_c2, c3):
            c3["chapter3"]["common_project_answer"][
                "super_competitiveness_sections"
            ][0]["bounded_superlative"]["claim"] = "改写后的唯一和最结论"

        result = self.run_contracts(mutate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("边界内唯一和最发生改写", result.stderr)

    def test_two_competitiveness_bridge_is_rejected(self):
        def mutate(c2, c3):
            removed = c2["chapter2"]["advantage_matrix"]["columns"].pop()
            removed_ref = removed["super_competitiveness"]["id"]
            c3["chapter3"]["common_project_answer"][
                "super_competitiveness_sections"
            ] = [
                section
                for section in c3["chapter3"]["common_project_answer"][
                    "super_competitiveness_sections"
                ]
                if section["source_ref"] != removed_ref
            ]

        result = self.run_contracts(mutate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("第二章必须形成3—4条超级竞争力", result.stderr)

    def test_four_competitiveness_bridge_is_supported(self):
        def mutate(c2, c3):
            column = deepcopy(c2["chapter2"]["advantage_matrix"]["columns"][-1])
            column["id"] = "BRAND"
            column["super_competitiveness"]["id"] = "SC-BRAND"
            column["super_competitiveness"]["text"] = "品牌信任形成第四条超级竞争力"
            c2["chapter2"]["advantage_matrix"]["columns"].append(column)

            section = deepcopy(
                c3["chapter3"]["common_project_answer"][
                    "super_competitiveness_sections"
                ][-1]
            )
            section["source_ref"] = "SC-BRAND"
            section["text"] = "品牌信任形成第四条超级竞争力"
            c3["chapter3"]["common_project_answer"][
                "super_competitiveness_sections"
            ].append(section)

        result = self.run_contracts(mutate)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
