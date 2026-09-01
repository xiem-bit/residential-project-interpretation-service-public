from __future__ import annotations

import hashlib
import json
import re
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GOLD_DIR = ROOT / "examples/gold-product3-public-safe"
AUTHORITY_PATH = GOLD_DIR / "gold-authority.json"


class Product3GoldAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))
        cls.deck = GOLD_DIR / cls.authority["authority_file"]
        cls.inspect = cls.deck.with_suffix(cls.deck.suffix + ".inspect.ndjson")
        cls.records = [
            json.loads(line)
            for line in cls.inspect.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_single_current_gold_file_and_hash(self) -> None:
        decks = sorted(GOLD_DIR.glob("*.pptx"))
        self.assertEqual(decks, [self.deck])
        digest = hashlib.sha256(self.deck.read_bytes()).hexdigest()
        self.assertEqual(digest, self.authority["authority_sha256"])
        self.assertNotIn("青岚澄境", self.deck.name)

    def test_twenty_slide_roles_and_non_symmetric_proof_depth(self) -> None:
        slides = [record for record in self.records if record.get("kind") == "slide"]
        self.assertEqual(len(slides), 20)
        self.assertEqual([item["slide"] for item in slides], list(range(1, 21)))
        roles = self.authority["page_roles"]
        self.assertEqual([item["slide"] for item in roles], list(range(1, 21)))
        self.assertEqual(self.authority["proof_depth_by_sc"], [3, 4, 2])
        self.assertEqual(self.authority["ai_recommender_slides"], [19])
        self.assertEqual(roles[18]["role"], "lightweight_ai_recommender_preview")
        self.assertEqual(roles[19]["role"], "closing")

    def test_twenty_sources_notes_and_no_private_paths(self) -> None:
        notes = [record for record in self.records if record.get("kind") == "notes"]
        self.assertEqual(len(notes), 20)
        for record in notes:
            text = record.get("text", "")
            self.assertIn("[Sources]", text)
            self.assertIn("[/Sources]", text)
            self.assertNotRegex(text, r"/Users/|file://|[A-Za-z]:\\\\|verification-tmp|worktree")

    def test_real_standard_map_and_attribution_remain_on_slides_five_to_seven(self) -> None:
        attributions = {
            record["slide"]: record.get("text")
            for record in self.records
            if record.get("kind") == "textbox"
            and record.get("text") == "© OpenStreetMap contributors"
        }
        self.assertEqual(set(attributions), {5, 6, 7})
        self.assertFalse(self.authority["map_policy"]["ai_generated_map"])
        self.assertTrue(self.authority["map_policy"]["same_base_map"])

    def test_pptx_package_has_twenty_slides_and_no_runtime_residue(self) -> None:
        sensitive = re.compile(
            rb"/Users/|file://|[A-Za-z]:\\\\|verification-tmp|worktree|"
            rb"password|passwd|api[_-]?key|cookie|localhost|127\\.0\\.0\\.1",
            re.IGNORECASE,
        )
        with zipfile.ZipFile(self.deck) as archive:
            slide_xml = [
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ]
            self.assertEqual(len(slide_xml), 20)
            for name in archive.namelist():
                if name.startswith("ppt/media/"):
                    continue
                data = archive.read(name)
                self.assertIsNone(sensitive.search(data), name)

    def test_full_render_set_and_no_retired_nineteen_page_assets(self) -> None:
        renders = sorted((GOLD_DIR / "qa").glob("slide-??.png"))
        self.assertEqual(len(renders), 20)
        self.assertEqual(renders[0].name, "slide-01.png")
        self.assertEqual(renders[-1].name, "slide-20.png")
        self.assertTrue((GOLD_DIR / "qa/deck-montage.png").is_file())
        self.assertFalse((GOLD_DIR / "qa/deck-montage.webp").exists())

    def test_assertive_writing_gate_is_still_mandatory(self) -> None:
        rules = (ROOT / "AGENT_RULES.md").read_text(encoding="utf-8")
        self.assertIn("A级", rules)
        self.assertIn("affirmative_statement_lint.py", rules)
        self.assertIn("--report-only", rules)


if __name__ == "__main__":
    unittest.main()
