#!/usr/bin/env python3
"""Verify the public semantic-change and targeted-reprojection tutorial."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tutorial_dir", type=Path)
    args = parser.parse_args()
    root = args.tutorial_dir.resolve()
    before = load(root / "before" / "snapshot.json")
    request = load(root / "change" / "change-request.json")
    registry = load(root / "after" / "change-impact-registry.json")
    delta = load(root / "after" / "semantic-delta.json")
    projection = load(root / "after" / "reprojection-map.json")
    errors: list[str] = []
    project_ids = {item.get("project_id") for item in (before, request, registry, delta, projection)}
    if len(project_ids) != 1:
        errors.append("project IDs differ")
    if before.get("semantic_version") != delta.get("from_version"):
        errors.append("before version does not match semantic delta")
    if registry.get("current_semantic_version") != delta.get("to_version") or projection.get("semantic_version") != delta.get("to_version"):
        errors.append("updated semantic versions differ")
    if registry.get("status") != "reprojection_complete" or not registry.get("changes"):
        errors.append("change registry is not complete")
    if "SC-CONTINUITY" in set(delta.get("current_sc_ids") or []) or "SC-DAILY-ROUTE" not in set(delta.get("current_sc_ids") or []):
        errors.append("old and new SC states are incorrect")
    affected = {item.get("id"): item.get("action") for item in projection.get("affected_outputs") or []}
    required = {
        "fact-conflict-gap-register",
        "project-contract",
        "product1",
        "product2",
        "semantic-core",
        "super-competitiveness-plan",
        "product3-chapter2-contract",
        "product3-chapter3-contract",
        "ue-solution-handoff",
        "product5-interaction-blueprint",
        "product4",
    }
    if set(affected) != required:
        errors.append("affected output set is incomplete")
    if affected.get("product2") != "reviewed_no_content_change" or affected.get("product4") != "not_enabled_no_reprojection_required":
        errors.append("reviewed and non-enabled dispositions are missing")
    if projection.get("cross_product_consistency") != "pass":
        errors.append("cross-product consistency is not pass")
    if errors:
        for error in errors:
            print("ERROR:", error)
        return 1
    print("REVISION TUTORIAL: PASS")
    print("Boundary: update order and affected references only; strategic quality is not machine-scored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
