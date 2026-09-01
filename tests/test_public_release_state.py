#!/usr/bin/env python3
"""Public-release checks that must remain true for every GitHub build."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_OWNER_PATH = "/Users/" + "xieming"
PRIVATE_RC_NAME = "residential-project-interpretation-service-public" + "-rc"
PRIVATE_OR_SECRET = re.compile(
    rf"(?:{re.escape(PRIVATE_OWNER_PATH)}|{re.escape(PRIVATE_RC_NAME)}|"
    r"ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (?:RSA |OPENSSH )?PRIVATE KEY)"
)


class PublicReleaseStateTest(unittest.TestCase):
    def test_apache_license_is_present(self) -> None:
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Apache License", license_text)
        self.assertIn("Version 2.0, January 2004", license_text)
        self.assertIn("http://www.apache.org/licenses/", license_text)

    def test_manifest_declares_public_apache_release(self) -> None:
        manifest = json.loads((ROOT / "PUBLIC_CORE_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "public_prerelease_v0_2_0_rc_1_published_capability_complete_authorized_assets_apache_2_0")
        self.assertEqual(manifest["rights"]["license"], "Apache-2.0")
        self.assertTrue(manifest["rights"]["rights_holder_approval_confirmed"])
        self.assertTrue(manifest["rights"]["public_distribution_authorized"])
        self.assertTrue(manifest["rights"]["authorized_real_client_materials_may_be_included"])
        self.assertEqual(manifest["rights"]["authorized_reference_assets"], "references/authorized-reference-assets.json")
        self.assertTrue(manifest["rights"]["unauthorized_client_materials_require_anonymization_or_structural_distillation"])
        self.assertTrue(manifest["rights"]["credentials_paths_internal_runtime_state_always_excluded"])
        self.assertEqual(manifest["public_release"]["visibility"], "public")
        self.assertEqual(
            manifest["public_release"]["repository"],
            "https://github.com/xiem-bit/residential-project-interpretation-service-public",
        )
        self.assertEqual(manifest["semantic_core_role"], "production_output")
        self.assertEqual(manifest["public_release"]["latest_published_tag"], "v0.2.0-rc.1")
        self.assertTrue(manifest["public_release"]["candidate_tag_created"])
        self.assertFalse(manifest["business_acceptance"]["presentation_or_web_required"])
        self.assertFalse(manifest["business_acceptance"]["workbuddy_style_blind_training_included"])
        self.assertTrue(manifest["business_acceptance"]["fresh_install_full_project_acceptance_required"])
        self.assertEqual(manifest["capability_parity_contract"], "CAPABILITY_PARITY_CONTRACT.md")
        self.assertEqual(manifest["capability_parity_manifest"], "CAPABILITY_PARITY_MANIFEST.json")

    def test_v02_authority_map_targets_existing_public_files(self) -> None:
        authority = json.loads((ROOT / "PRODUCTION_AUTHORITY_MAP.json").read_text(encoding="utf-8"))
        self.assertEqual(authority["source_baseline"]["commit"], "8c917683b8f7a118aa584698cf4cd484a8ed73cd")
        for mapping in authority["mappings"]:
            self.assertTrue(mapping["coverage"])
            for relative in mapping["public"]:
                self.assertTrue((ROOT / relative).exists(), relative)

    def test_current_release_has_no_hidden_answer_training_tree(self) -> None:
        self.assertFalse((ROOT / "evaluation" / "hidden-answer").exists())
        manifest = json.loads((ROOT / "PUBLIC_CORE_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertNotIn("evaluation/hidden-answer", manifest["v0_2_public_roots"])

    def test_v02_roots_have_no_absolute_user_paths(self) -> None:
        manifest = json.loads((ROOT / "PUBLIC_CORE_MANIFEST.json").read_text(encoding="utf-8"))
        forbidden = re.compile(r"(?:/Users/|file://|[A-Za-z]:\\\\|\.workbuddy/binaries/)")
        for root_name in manifest["v0_2_public_roots"]:
            for path in (ROOT / root_name).rglob("*"):
                if path.is_file() and path.suffix.lower() in {".json", ".md", ".py", ".yml"}:
                    self.assertIsNone(forbidden.search(path.read_text(encoding="utf-8")), path.relative_to(ROOT).as_posix())

    def test_source_tree_has_no_private_release_or_secret_marker(self) -> None:
        excluded_parts = {".git", ".venv", "node_modules", "verification-tmp", "__pycache__"}
        for path in ROOT.rglob("*"):
            relative = path.relative_to(ROOT)
            if any(part in excluded_parts for part in relative.parts):
                continue
            if path.is_symlink():
                self.fail(f"public source cannot contain symlink: {relative.as_posix()}")
            if not path.is_file() or path.suffix.lower() not in {
                ".json",
                ".md",
                ".py",
                ".js",
                ".mjs",
                ".html",
                ".css",
                ".txt",
                ".yml",
                "",
            }:
                continue
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(PRIVATE_OR_SECRET.search(text), relative.as_posix())

        for forbidden in ("projects", "assets", "evals"):
            self.assertFalse((ROOT / forbidden).exists(), forbidden)


if __name__ == "__main__":
    unittest.main()
