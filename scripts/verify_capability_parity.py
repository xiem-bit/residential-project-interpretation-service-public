#!/usr/bin/env python3
"""Validate the v0.2 capability-parity freeze and optional private source mapping."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PARITY_PATH = ROOT / "CAPABILITY_PARITY_MANIFEST.json"
AUTHORITY_PATH = ROOT / "PRODUCTION_AUTHORITY_MAP.json"

ALLOWED_CLASSIFICATIONS = {
    "public_required",
    "portable_adaptation",
    "private_replaced",
    "retired_excluded",
}
ALLOWED_STATUSES = {
    "implemented_current",
    "partial_upgrade_required",
    "public_safe_derivative_required",
    "cross_package_pending",
    "retired_excluded",
}
BLOCKING_STATUSES = {
    "partial_upgrade_required",
    "public_safe_derivative_required",
    "cross_package_pending",
}
REQUIRED_CAPABILITY_IDS = {f"CAP-{index:03d}" for index in range(1, 19)}
REQUIRED_DOMAINS = {
    "entry_and_orchestration",
    "input_governance",
    "product1",
    "product2",
    "incremental_research",
    "reasoning_harness",
    "semantic_core_and_sc",
    "cross_product_governance",
    "client_facing_writing",
    "product3",
    "product4",
    "product5",
    "gold_reference_and_learning",
    "machine_harness_and_receipts",
    "cross_package_interface",
    "installation_and_adapters",
    "release_governance",
    "history_and_rights_boundary",
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
ABSOLUTE_PATH = re.compile(r"(?:/Users/|file://|[A-Za-z]:\\\\)")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid JSON: {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON must be an object: {path.name}")
    return value


def validate_public_manifest(parity: dict[str, Any], authority: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if parity.get("schema") != "residential.capability_parity_manifest.v1":
        errors.append("CAPABILITY_PARITY_MANIFEST.json: unexpected schema")
    if parity.get("status") != "p5_gold_complete_product3_gold_pending_not_released":
        errors.append("CAPABILITY_PARITY_MANIFEST.json: unexpected current migration state")

    principles = parity.get("principles")
    required_true = {
        "complete_semantic_parity_required",
        "simplified_subset_is_not_acceptable",
        "normal_runtime_progressive_loading",
        "product1_default_product2_to_5_on_demand",
        "machine_checks_have_veto_not_business_approval",
        "public_safe_structural_derivatives_required",
    }
    required_false = {
        "empty_disabled_product_files_required",
        "real_client_materials_included",
        "workbuddy_blind_training_included",
        "private_evaluation_holdout_included",
    }
    if not isinstance(principles, dict):
        errors.append("CAPABILITY_PARITY_MANIFEST.json: principles must be an object")
    else:
        for field in sorted(required_true):
            if principles.get(field) is not True:
                errors.append(f"principles.{field}: must be true")
        for field in sorted(required_false):
            if principles.get(field) is not False:
                errors.append(f"principles.{field}: must be false")

    authority_mappings = authority.get("mappings")
    if not isinstance(authority_mappings, list):
        errors.append("PRODUCTION_AUTHORITY_MAP.json: mappings must be an array")
        authority_ids: set[str] = set()
    else:
        authority_ids = set()
        for index, mapping in enumerate(authority_mappings):
            if not isinstance(mapping, dict):
                errors.append(f"authority mapping {index}: must be an object")
                continue
            authority_id = mapping.get("authority")
            if not isinstance(authority_id, str) or not authority_id:
                errors.append(f"authority mapping {index}: missing authority")
                continue
            if authority_id in authority_ids:
                errors.append(f"authority mapping duplicate: {authority_id}")
            authority_ids.add(authority_id)
            coverage = mapping.get("coverage")
            if not isinstance(coverage, str) or not coverage:
                errors.append(f"authority mapping {authority_id}: missing coverage")
            for source in mapping.get("source", []):
                if not isinstance(source, dict):
                    errors.append(f"authority mapping {authority_id}: invalid source record")
                    continue
                if not isinstance(source.get("path"), str) or not source["path"]:
                    errors.append(f"authority mapping {authority_id}: source path missing")
                if not isinstance(source.get("git_blob"), str) or not HEX40.fullmatch(source["git_blob"]):
                    errors.append(f"authority mapping {authority_id}: source git_blob invalid")
            for target in mapping.get("public", []):
                if not isinstance(target, str) or not target:
                    errors.append(f"authority mapping {authority_id}: invalid public target")
                elif not (ROOT / target).exists():
                    errors.append(f"authority mapping {authority_id}: public target missing: {target}")

    capabilities = parity.get("capabilities")
    if not isinstance(capabilities, list):
        errors.append("CAPABILITY_PARITY_MANIFEST.json: capabilities must be an array")
        capabilities = []

    seen_ids: set[str] = set()
    seen_domains: set[str] = set()
    calculated_blockers: set[str] = set()
    for index, capability in enumerate(capabilities):
        if not isinstance(capability, dict):
            errors.append(f"capability {index}: must be an object")
            continue
        capability_id = capability.get("id")
        if not isinstance(capability_id, str) or not capability_id:
            errors.append(f"capability {index}: missing id")
            continue
        if capability_id in seen_ids:
            errors.append(f"capability duplicate: {capability_id}")
        seen_ids.add(capability_id)
        domain = capability.get("domain")
        if isinstance(domain, str):
            seen_domains.add(domain)
        else:
            errors.append(f"{capability_id}: missing domain")
        classification = capability.get("classification")
        if classification not in ALLOWED_CLASSIFICATIONS:
            errors.append(f"{capability_id}: invalid classification: {classification}")
        status = capability.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{capability_id}: invalid status: {status}")
        if status in BLOCKING_STATUSES:
            calculated_blockers.add(capability_id)
            if not capability.get("gap"):
                errors.append(f"{capability_id}: blocking status requires a gap")
        if classification == "retired_excluded" and status != "retired_excluded":
            errors.append(f"{capability_id}: retired classification requires retired status")
        source_ids = capability.get("source_authority_ids")
        if not isinstance(source_ids, list) or not source_ids:
            errors.append(f"{capability_id}: source_authority_ids must be non-empty")
        else:
            for authority_id in source_ids:
                if authority_id not in authority_ids:
                    errors.append(f"{capability_id}: unknown authority id: {authority_id}")
        targets = capability.get("public_targets")
        if not isinstance(targets, list) or not targets:
            errors.append(f"{capability_id}: public_targets must be non-empty")
        else:
            for target in targets:
                if not isinstance(target, str) or not target:
                    errors.append(f"{capability_id}: invalid public target")
                elif not (ROOT / target).exists():
                    errors.append(f"{capability_id}: public target missing: {target}")
        if not capability.get("load_condition"):
            errors.append(f"{capability_id}: load_condition missing")
        if not capability.get("acceptance"):
            errors.append(f"{capability_id}: acceptance missing")

    if seen_ids != REQUIRED_CAPABILITY_IDS:
        errors.append(
            "capability IDs mismatch: "
            f"missing={sorted(REQUIRED_CAPABILITY_IDS - seen_ids)} "
            f"extra={sorted(seen_ids - REQUIRED_CAPABILITY_IDS)}"
        )
    if seen_domains != REQUIRED_DOMAINS:
        errors.append(
            "capability domains mismatch: "
            f"missing={sorted(REQUIRED_DOMAINS - seen_domains)} "
            f"extra={sorted(seen_domains - REQUIRED_DOMAINS)}"
        )

    blockers = parity.get("release_blockers")
    if not isinstance(blockers, list) or set(blockers) != calculated_blockers:
        errors.append(
            "release_blockers must equal every capability in a blocking status: "
            f"expected={sorted(calculated_blockers)} actual={sorted(blockers or [])}"
        )

    interface = parity.get("cross_package_interface")
    if not isinstance(interface, dict):
        errors.append("cross_package_interface must be an object")
    else:
        expected_interface = {
            "upstream_request_schema": "residential.upstream_task.v0.2",
            "public_evidence_schema": "public_evidence_envelope.v1",
            "upstream_response_schema": "residential.upstream_response.v0.2",
            "downstream_adoption_schema": "residential.upstream_adoption_receipt.v0.2",
            "shared_cwd_required": False,
            "absolute_path_dependency_allowed": False,
            "upstream_fulfilled_equals_downstream_accepted": False,
            "upstream_may_adjudicate_competitor_value_anchor_or_sc": False,
            "status": "candidate_conformance_passed",
        }
        for field, expected in expected_interface.items():
            if interface.get(field) != expected:
                errors.append(f"cross_package_interface.{field}: expected {expected!r}")

    for required_file in (
        "CAPABILITY_PARITY_CONTRACT.md",
        "CAPABILITY_PARITY_MANIFEST.json",
        "RETIRED_AND_PRIVATE_BOUNDARY.md",
    ):
        if not (ROOT / required_file).is_file():
            errors.append(f"required P0 file missing: {required_file}")

    for file_name, payload in ((PARITY_PATH.name, parity), (AUTHORITY_PATH.name, authority)):
        serialized = json.dumps(payload, ensure_ascii=False)
        if ABSOLUTE_PATH.search(serialized):
            errors.append(f"{file_name}: absolute path is forbidden")

    return errors


def git_output(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ValueError(completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()


def validate_private_source(repo: Path, parity: dict[str, Any], authority: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not (repo / ".git").exists():
        try:
            git_output(repo, "rev-parse", "--git-dir")
        except ValueError:
            return ["source repository is not a Git worktree"]
    commit = parity.get("source_baseline", {}).get("commit")
    if not isinstance(commit, str) or not HEX40.fullmatch(commit):
        return ["source baseline commit is invalid"]
    try:
        git_output(repo, "cat-file", "-e", f"{commit}^{{commit}}")
    except ValueError:
        return ["source baseline commit does not exist in source repository"]
    for mapping in authority.get("mappings", []):
        authority_id = mapping.get("authority", "unknown")
        for source in mapping.get("source", []):
            path = source.get("path")
            expected_blob = source.get("git_blob")
            try:
                actual_blob = git_output(repo, "rev-parse", f"{commit}:{path}")
            except ValueError:
                errors.append(f"{authority_id}: source missing at frozen commit: {path}")
                continue
            if actual_blob != expected_blob:
                errors.append(f"{authority_id}: source blob mismatch: {path}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-repo",
        type=Path,
        help="Optional private source repository used only to verify frozen Git blobs.",
    )
    args = parser.parse_args()
    try:
        parity = load_json(PARITY_PATH)
        authority = load_json(AUTHORITY_PATH)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    errors = validate_public_manifest(parity, authority)
    source_checked = False
    if args.source_repo is not None:
        source_checked = True
        errors.extend(validate_private_source(args.source_repo.resolve(), parity, authority))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    summary = {
        "schema": parity["schema"],
        "capabilities": len(parity["capabilities"]),
        "release_blockers": len(parity["release_blockers"]),
        "source_checked": source_checked,
        "status": "pass",
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
