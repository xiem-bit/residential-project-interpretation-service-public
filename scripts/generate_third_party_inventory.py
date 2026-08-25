#!/usr/bin/env python3
"""Generate or verify the deterministic npm license inventory from package-lock.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCKFILE = ROOT / "tools/product3_ppt_pipeline/automizer_adapter/package-lock.json"
OUTPUT = ROOT / "THIRD_PARTY_LICENSES.json"


def package_name(lock_path: str, metadata: dict[str, Any]) -> str:
    if metadata.get("name"):
        return str(metadata["name"])
    marker = "node_modules/"
    if marker not in lock_path:
        return lock_path
    return lock_path.rsplit(marker, 1)[1]


def build_inventory() -> dict[str, Any]:
    lock = json.loads(LOCKFILE.read_text(encoding="utf-8"))
    packages = []
    for lock_path, metadata in lock.get("packages", {}).items():
        if not lock_path or not isinstance(metadata, dict):
            continue
        name = package_name(lock_path, metadata)
        version = str(metadata.get("version", "")).strip()
        license_name = metadata.get("license", "UNKNOWN")
        if isinstance(license_name, list):
            license_name = json.dumps(license_name, ensure_ascii=False, sort_keys=True)
        packages.append(
            {
                "name": name,
                "version": version,
                "license": str(license_name),
                "development_only": bool(metadata.get("dev", False)),
            }
        )
    packages.sort(key=lambda item: (item["name"], item["version"]))
    unknown = [f"{item['name']}@{item['version']}" for item in packages if item["license"] == "UNKNOWN"]
    return {
        "schema": "residential.public_third_party_licenses.v0.1",
        "status": "lockfile_derived_verified_for_public_rc",
        "source_lockfile": "tools/product3_ppt_pipeline/automizer_adapter/package-lock.json",
        "package_count": len(packages),
        "unknown_license_count": len(unknown),
        "unknown_licenses": unknown,
        "packages": packages,
    }


def serialized_inventory() -> str:
    return json.dumps(build_inventory(), ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = serialized_inventory()
    if args.write:
        OUTPUT.write_text(expected, encoding="utf-8")
        inventory = build_inventory()
        print(f"wrote {inventory['package_count']} locked package licenses")
        return 0
    if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != expected:
        print("THIRD_PARTY_LICENSES.json is missing or stale", file=sys.stderr)
        return 1
    inventory = build_inventory()
    if inventory["unknown_license_count"]:
        print(f"unknown licenses: {inventory['unknown_licenses']}", file=sys.stderr)
        return 1
    print(f"third-party inventory verified: {inventory['package_count']} packages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
