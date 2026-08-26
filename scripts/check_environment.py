#!/usr/bin/env python3
"""Check the runtime for the v0.2 production core or historical RC1 adapters."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any


def _version(command: str) -> str | None:
    executable = shutil.which(command)
    if not executable:
        return None
    result = subprocess.run(
        [executable, "--version"],
        check=False,
        capture_output=True,
        text=True,
    )
    return (result.stdout or result.stderr).strip() or None


def _major(value: str | None) -> int | None:
    if not value:
        return None
    digits = "".join(character if character.isdigit() else " " for character in value).split()
    return int(digits[0]) if digits else None


def check_environment(profile: str = "legacy-rc1") -> dict[str, Any]:
    python_version = ".".join(str(item) for item in sys.version_info[:3])
    node_version = _version("node")
    npm_version = _version("npm")
    all_checks = {
        "python": {
            "version": python_version,
            "minimum": "3.9",
            "status": "pass" if sys.version_info >= (3, 9) else "fail",
        },
        "node": {
            "version": node_version,
            "minimum": "20",
            "status": "pass" if (_major(node_version) or 0) >= 20 else "fail",
        },
        "npm": {
            "version": npm_version,
            "status": "pass" if npm_version else "fail",
        },
    }
    checks = {"python": all_checks["python"]}
    if profile == "legacy-rc1":
        checks.update({"node": all_checks["node"], "npm": all_checks["npm"]})
    return {
        "schema": "residential.public_environment_check.v0.2",
        "profile": profile,
        "status": "pass" if all(item["status"] == "pass" for item in checks.values()) else "fail",
        "checks": checks,
        "codex_runtime_required": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--profile", choices=["production-core", "legacy-rc1"], default="production-core")
    args = parser.parse_args()
    report = check_environment(args.profile)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for name, item in report["checks"].items():
            print(f"{name}: {item['version'] or 'missing'} [{item['status']}]")
        print(f"environment: {report['status']}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
