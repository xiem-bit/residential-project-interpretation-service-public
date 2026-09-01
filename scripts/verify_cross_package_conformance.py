#!/usr/bin/env python3
"""Verify the frozen public-information producer interface against this consumer."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "production_core"))

from validate_upstream_exchange import canonical_json_sha256, validate_exchange  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON root must be an object")
    return value


def raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_json(command: list[str], cwd: Path) -> tuple[dict[str, Any], str]:
    completed = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        return {}, completed.stderr.strip() or completed.stdout.strip()
    try:
        return json.loads(completed.stdout), ""
    except json.JSONDecodeError as exc:
        return {}, f"non-JSON command output: {exc}"


def first_query_text(envelope: dict[str, Any], query_id: str) -> str:
    for source in envelope.get("sources", []):
        query_ref = source.get("query_ref") if isinstance(source, dict) else None
        if isinstance(query_ref, dict) and query_ref.get("query_id") == query_id and query_ref.get("exact_query_text"):
            return query_ref["exact_query_text"]
    return f"公开证据检索 {query_id}"


def consumer_contracts_for(envelope: dict[str, Any], schema_sha256: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    execution = envelope.get("query_execution") or {}
    executed = list(execution.get("executed_query_ids") or [])
    proposed = list(execution.get("proposed_incremental_query_ids") or [])
    mode = execution.get("acceptance_mode") or "quality_sufficiency"
    if mode not in {"count_based", "quality_sufficiency", "hybrid"}:
        mode = "quality_sufficiency"
    project_id = envelope.get("project_id") or "PROJECT-NOT-SPECIFIED"
    request = {
        "schema": "residential.upstream_task.v0.2",
        "request_id": envelope["request_id"],
        "task_id": envelope["task_id"],
        "project_id": project_id,
        "owner": "public_information_owner",
        "business_question": envelope["request"]["business_question"],
        "judgment_gap": "验证生产方黄金证据包能否被住宅侧完整消费",
        "requested_evidence_roles": ["official_public_fact", "nonprobability_social_sample", "counterexample"],
        "object_scope": {
            "canonical_subject": envelope["subject"],
            "aliases": [],
            "comparison_objects": [],
            "identity_boundary": "只验证公开候选接口，不产生真实项目判断",
        },
        "time_scope": envelope["request"]["time_scope"],
        "geo_scope": envelope["request"]["geo_scope"],
        "downstream_destination": {
            "products": [1],
            "judgment_refs": ["INTEROP-CHECK"],
            "allowed_uses": ["接口一致性检查"],
            "blocked_uses": ["真实项目结论", "自动裁定超级竞争力"],
        },
        "acceptance_contract": {
            "acceptance_mode": mode,
            "qualified_match_classes": ["direct", "supporting"],
            "quality_criteria": ["证据层级保留", "冲突与缺口不丢失"],
            "count_threshold": 1 if mode in {"count_based", "hybrid"} else None,
            "diversity_requirements": {
                "minimum_source_role_count": 1,
                "minimum_project_or_brand_count": 1,
                "maximum_qualified_items_per_project_or_brand": 2,
            },
            "research_characteristics": ["support_and_counterevidence_required", "adaptive_extension_possible"],
        },
        "query_plan": {
            "mode": "research_retrieval",
            "plan_schema": execution.get("plan_schema"),
            "plan_version": execution.get("plan_version"),
            "channel_scope": list(envelope["request"]["channel_scope"]),
            "frozen_queries": [
                {
                    "query_id": query_id,
                    "exact_query_text": first_query_text(envelope, query_id),
                    "object_identity": envelope["subject"],
                    "term_provenance": ["producer_golden_fixture"],
                    "minimum_result_batches": 1,
                    "minimum_actual_opens": 1,
                }
                for query_id in executed
            ],
            "simple_direct_retrieval_exemption": None,
        },
        "incremental_policy": {
            "proposal_allowed": True,
            "execution_authorized": False,
            "authorization_ref": None,
            "maximum_incremental_batches": 0,
            "time_limit_minutes": 0,
            "cost_limit": None,
            "minimum_marginal_information_gain": "low",
        },
        "stop_conditions": [envelope["stop_reason"]],
        "authorization": "synthetic_fixture",
        "status": "fulfilled",
        "portability_boundary": "no_shared_cwd_no_absolute_path_no_private_runtime_state",
    }
    package_hash = canonical_json_sha256(envelope)
    response = {
        "schema": "residential.upstream_response.v0.2",
        "request_id": request["request_id"],
        "task_id": request["task_id"],
        "project_id": project_id,
        "upstream_owner": "public_information_owner",
        "status": envelope["upstream_status"],
        "evidence_envelope": {
            "schema": "public_evidence_envelope.v1",
            "package_id": envelope["package_id"],
            "content_sha256": package_hash,
            "schema_sha256": schema_sha256,
            "transfer_mode": "inline",
            "artifact_ref": None,
        },
        "sufficiency": {
            "acceptance_mode": mode,
            "evidence_sufficiency_status": execution["evidence_sufficiency_status"],
            "coverage_summary": "生产方黄金证据包跨仓消费检查",
            "marginal_information_gain": "unknown",
            "executed_query_ids": executed,
            "proposed_incremental_query_ids": proposed,
            "failure_attribution_complete": execution["failure_attribution_complete"],
        },
        "negative_hits": [hit["negative_hit_id"] for hit in envelope["negative_hits"]],
        "conflicts": list(envelope["conflicts"]),
        "gaps": list(envelope["gaps"]),
        "stop_reason": envelope["stop_reason"],
        "upstream_does_not_adjudicate_strategy": True,
        "fulfilled_does_not_equal_accepted": True,
    }
    accepted_items = []
    for item in envelope["items"]:
        if item["evidence_class"] in {"conflict", "gap"}:
            continue
        allowed = list(item.get("allowed_use") or [])
        accepted_items.append(
            {
                "item_id": item["item_id"],
                "evidence_role": item["evidence_class"],
                "allowed_uses": allowed,
                "target_refs": ["INTEROP-CHECK"],
                "interpretation_boundary": item["usage_boundary"],
            }
        )
    adoption = {
        "schema": "residential.upstream_adoption_receipt.v0.2",
        "request_id": request["request_id"],
        "task_id": request["task_id"],
        "project_id": project_id,
        "evidence_package": {
            "schema": "public_evidence_envelope.v1",
            "package_id": envelope["package_id"],
            "content_sha256": package_hash,
        },
        "upstream_status": response["status"],
        "downstream_acceptance": "accepted_with_conditions" if envelope["conflicts"] or envelope["gaps"] else "accepted",
        "accepted_items": accepted_items,
        "rejected_items": [],
        "unresolved_conflicts": list(envelope["conflicts"]),
        "unresolved_gaps": list(envelope["gaps"]),
        "incremental_decision": {
            "decision": "hold" if proposed else "stop_search",
            "authorized_query_ids": [],
            "reason": "互操作检查不取得真实增量执行授权",
            "limits": None,
        },
        "judgment_effect": "pending",
        "accepted_by": "cross_package_conformance_owner",
        "accepted_at": "candidate_conformance",
        "machine_check_does_not_approve_business_quality": True,
    }
    return request, response, adoption


def verify(upstream_root: Path, full: bool) -> dict[str, Any]:
    compatibility = load_json(ROOT / "external-capabilities" / "cross-package-compatibility.json")
    producer = compatibility["upstream_evidence_contract"]
    schema_path = upstream_root / producer["plugin_relative_schema_path"]
    fixture_path = upstream_root / producer["plugin_relative_golden_fixture_path"]
    interop_path = upstream_root / producer["plugin_relative_interop_manifest_path"]
    errors: list[str] = []

    actual_schema_hash = raw_sha256(schema_path)
    if actual_schema_hash != producer["schema_sha256"]:
        errors.append("producer schema raw-byte SHA-256 mismatch")
    schema = load_json(schema_path)
    if schema.get("$id") != "public_evidence_envelope.v1":
        errors.append("producer schema $id mismatch")
    interop = load_json(interop_path)
    required_consumer_ids = {
        "residential.upstream_task.v0.2",
        "residential.upstream_response.v0.2",
        "residential.upstream_adoption_receipt.v0.2",
    }
    if not required_consumer_ids.issubset(set(interop.get("consumer_owned_interfaces") or [])):
        errors.append("producer interop manifest does not enumerate all residential interfaces")

    minimal_report, minimal_error = run_json([sys.executable, "tests/run_public_evidence_contract.py"], upstream_root)
    if minimal_error or minimal_report.get("status") != "pass":
        errors.append(f"producer minimal conformance failed: {minimal_error or minimal_report.get('status')}")
    full_report: dict[str, Any] | None = None
    if full:
        full_report, full_error = run_json([sys.executable, "tests/run_release_harness.py"], upstream_root)
        if full_error or full_report.get("status") != "pass":
            errors.append(f"producer full harness failed: {full_error or full_report.get('status')}")

    local_envelope = ROOT / "fixtures" / "upstream-exchange" / "public-evidence-envelope.json"
    local_for_producer, local_error = run_json(
        [sys.executable, "tools/validate_public_evidence.py", "--input", str(local_envelope)],
        upstream_root,
    )
    if local_error or local_for_producer.get("status") != "pass":
        errors.append(f"producer rejected residential fixture: {local_error or local_for_producer.get('status')}")

    producer_golden = load_json(fixture_path)
    request, response, adoption = consumer_contracts_for(producer_golden, actual_schema_hash)
    consumer_report = validate_exchange(request, producer_golden, response, adoption, compatibility)
    if consumer_report.get("status") != "pass":
        errors.extend(f"consumer rejected producer fixture: {error}" for error in consumer_report.get("errors", []))

    local_contracts = {}
    for name, record in (
        ("request", compatibility["request_contract"]),
        ("response", compatibility["response_contract"]),
        ("adoption", compatibility["adoption_contract"]),
    ):
        path = ROOT / record["path"]
        local_contracts[name] = {
            "schema": record["schema"],
            "path": record["path"],
            "sha256_raw_file_bytes": raw_sha256(path),
        }

    return {
        "schema": "residential.cross_package_conformance_receipt.v0.2",
        "status": "pass" if not errors else "fail",
        "error_count": len(errors),
        "errors": errors,
        "producer": {
            "release_candidate": producer["release_candidate"],
            "schema": "public_evidence_envelope.v1",
            "sha256_raw_file_bytes": actual_schema_hash,
            "minimal_case_count": minimal_report.get("case_count"),
            "full_fixture_case_count": full_report.get("fixture_case_count") if full_report else None,
        },
        "consumer_contracts": local_contracts,
        "producer_validated_consumer_fixture": local_for_producer.get("status") == "pass",
        "consumer_validated_producer_fixture": consumer_report.get("status") == "pass",
        "shared_cwd_required": False,
        "network_accessed": False,
        "platform_opened": False,
        "business_acceptance_validated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-plugin-root", required=True)
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    receipt = verify(Path(args.upstream_plugin_root).resolve(), args.full)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
