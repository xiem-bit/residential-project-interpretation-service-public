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
        self.assertEqual(manifest["status"], "public_prerelease_apache_2_0")
        self.assertEqual(manifest["rights"]["license"], "Apache-2.0")
        self.assertTrue(manifest["rights"]["rights_holder_approval_confirmed"])
        self.assertTrue(manifest["rights"]["public_distribution_authorized"])
        self.assertEqual(manifest["public_release"]["visibility"], "public")
        self.assertEqual(
            manifest["public_release"]["repository"],
            "https://github.com/xiem-bit/residential-project-interpretation-service-public",
        )

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
