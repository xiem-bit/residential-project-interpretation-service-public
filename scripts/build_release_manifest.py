#!/usr/bin/env python3
"""Build or verify the clean RC source-file manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "RELEASE_MANIFEST.json"
EXCLUDED_PARTS = {".git", ".venv", "node_modules", "verification-tmp", "__pycache__"}
EXCLUDED_NAMES = {".DS_Store", "RELEASE_MANIFEST.json"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.name in EXCLUDED_NAMES or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError(f"release source cannot contain symlink: {relative.as_posix()}")
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix().encode("utf-8"))


def build_manifest() -> dict[str, Any]:
    records = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in source_files()
    ]
    tree_input = "".join(f"{item['sha256']}  {item['path']}\n" for item in records)
    return {
        "schema": "residential.public_rc_source_manifest.v0.1",
        "version": "v0.1.0-rc.1",
        "status": "public_prerelease_apache_2_0",
        "source_commit": "21a68a543ee7322a0a2532a0c254ecf211d1a878",
        "excluded": [
            ".git/**",
            ".venv/**",
            "**/node_modules/**",
            "verification-tmp/**",
            "**/__pycache__/**",
            "**/*.pyc",
            ".DS_Store",
            "RELEASE_MANIFEST.json",
        ],
        "file_count": len(records),
        "tree_sha256": hashlib.sha256(tree_input.encode("utf-8")).hexdigest(),
        "files": records,
    }


def serialized_manifest() -> str:
    return json.dumps(build_manifest(), ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = serialized_manifest()
    if args.write:
        OUTPUT.write_text(expected, encoding="utf-8")
        manifest = build_manifest()
        print(f"wrote release manifest: {manifest['file_count']} files {manifest['tree_sha256']}")
        return 0
    if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != expected:
        print("RELEASE_MANIFEST.json is missing or stale", file=sys.stderr)
        return 1
    manifest = build_manifest()
    print(f"release manifest verified: {manifest['file_count']} files {manifest['tree_sha256']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
