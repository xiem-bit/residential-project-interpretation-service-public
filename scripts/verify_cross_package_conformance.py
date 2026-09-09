#!/usr/bin/env python3
"""Verify the frozen public-information producer interface against this consumer."""

from __future__ import annotations

import argparse
import copy
import tempfile
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


def consumer_contracts_for(request: dict[str, Any], envelope: dict[str, Any], schema_sha256: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Wrap a result while retaining a request frozen before producer execution."""
    request = copy.deepcopy(request)
    execution = envelope.get("query_execution") or {}
    executed = list(execution.get("executed_query_ids") or [])
    proposed = list(execution.get("proposed_incremental_query_ids") or [])
    mode = request["acceptance_contract"]["acceptance_mode"]
    project_id = request["project_id"]
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
        [sys.executable, "tools/validate_public_evidence.py", "--input", str(local_envelope),
         "--request", str(ROOT / "fixtures/upstream-exchange/request.json"),
         "--sufficiency-input", str(ROOT / "fixtures/upstream-exchange/sufficiency-input.json")],
        upstream_root,
    )
    if local_error or local_for_producer.get("status") != "pass":
        errors.append(f"producer rejected residential fixture: {local_error or local_for_producer.get('status')}")

    fixture_root = ROOT / "fixtures/upstream-exchange"
    original_request = load_json(fixture_root / "request.json")
    original_hash = canonical_json_sha256(original_request)
    sufficiency_input = load_json(fixture_root / "sufficiency-input.json")
    with tempfile.TemporaryDirectory(prefix="residential-exchange-") as temp:
        output = Path(temp) / "envelope.json"
        owner_plan = {"channel": "public_web", "queries": original_request["query_plan"]["frozen_queries"]}
        plan_path = Path(temp) / "owner-plan.json"
        plan_path.write_text(json.dumps(owner_plan, ensure_ascii=False), encoding="utf-8")
        compiled_path = Path(temp) / "compiled-request.json"
        compilation, compilation_error = run_json(
            [sys.executable, "tools/compile_retrieval_execution_request.py",
             "--task", str(fixture_root / "request.json"), "--plan", str(plan_path), "--output", str(compiled_path)], upstream_root,
        )
        compiled_ok = False
        if compilation_error or not compilation.get("passed") or not compiled_path.exists():
            errors.append(f"producer request compilation failed: {compilation_error or compilation.get('status')}")
        else:
            compiled = load_json(compiled_path)
            compiled_ok = (compiled.get("retrieval_task") == original_request
                           and compiled.get("source_request_sha256") == original_hash
                           and compiled.get("request_id") == original_request["request_id"]
                           and all(compiled.get("sufficiency_applicability", {}).get(k) == v
                                   for k, v in original_request["acceptance_contract"].items()))
            if not compiled_ok:
                errors.append("producer compilation changed frozen request criteria")
        packaging, packaging_error = run_json(
            [sys.executable, "tools/package_evidence.py", "--input", str(local_envelope),
             "--request", str(fixture_root / "request.json"),
             "--sufficiency-input", str(fixture_root / "sufficiency-input.json"),
             "--output", str(output)], upstream_root,
        )
        if packaging_error or packaging.get("status") != "pass" or not output.exists():
            errors.append(f"producer request-bound packaging failed: {packaging_error or packaging.get('status')}")
            consumer_report = {"status": "fail"}
        else:
            producer_golden = load_json(output)
            for field in ("sources", "items", "negative_hits", "conflicts", "gaps"):
                if producer_golden[field] != load_json(local_envelope)[field]:
                    errors.append(f"producer changed preserved evidence field: {field}")
            request, response, adoption = consumer_contracts_for(original_request, producer_golden, actual_schema_hash)
            consumer_report = validate_exchange(request, producer_golden, response, adoption, compatibility,
                                                sufficiency_input=sufficiency_input)
    if canonical_json_sha256(load_json(fixture_root / "request.json")) != original_hash:
        errors.append("producer changed the frozen request")
    negative_cases = []
    for case in ("mode_changed", "threshold_lowered", "quality_removed", "diversity_lowered", "unknown_mode", "another_request"):
        draft = load_json(local_envelope)
        sufficient = copy.deepcopy(sufficiency_input)
        if case == "mode_changed":
            draft["query_execution"]["acceptance_mode"] = "quality_sufficiency"
        elif case == "threshold_lowered":
            sufficient["consumer_contract"]["count_threshold"] = 1
        elif case == "quality_removed":
            sufficient["consumer_contract"]["quality_criteria"] = []
        elif case == "diversity_lowered":
            sufficient["consumer_contract"]["diversity_requirements"]["minimum_source_role_count"] = 1
        elif case == "unknown_mode":
            draft["query_execution"]["acceptance_mode"] = "unknown"
        else:
            sufficient["request_id"] = "REQUEST-OTHER"
        with tempfile.TemporaryDirectory(prefix="residential-negative-") as temp:
            temp_root = Path(temp)
            for name, value in (("draft.json", draft), ("sufficiency.json", sufficient)):
                (temp_root / name).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
            output = temp_root / "output.json"
            completed = subprocess.run(
                [sys.executable, "tools/package_evidence.py", "--input", str(temp_root / "draft.json"),
                 "--request", str(fixture_root / "request.json"),
                 "--sufficiency-input", str(temp_root / "sufficiency.json"), "--output", str(output)],
                cwd=upstream_root, capture_output=True, text=True, check=False,
            )
            try:
                rejection = json.loads(completed.stdout)
            except json.JSONDecodeError:
                rejection = {}
            passed = (completed.returncode != 0 and rejection.get("status") == "fail"
                      and bool(rejection.get("errors")) and not output.exists())
            negative_cases.append({"case": case, "passed": passed})
            if not passed:
                errors.append(f"producer failed to reject contract drift: {case}")
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
        "request_frozen_before_execution": True,
        "request_compiled_without_execution": compiled_ok,
        "original_request_sha256": original_hash,
        "contract_drift_negative_cases": negative_cases,
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
