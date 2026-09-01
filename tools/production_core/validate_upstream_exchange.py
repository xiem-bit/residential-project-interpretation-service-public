#!/usr/bin/env python3
"""Validate the residential request -> public evidence -> adoption exchange.

The validator intentionally uses only the Python standard library.  It checks
the business boundaries that a JSON Schema alone cannot express; it does not
approve the research conclusion or the quality of an SC judgment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
COMPATIBILITY_PATH = ROOT / "external-capabilities" / "cross-package-compatibility.json"
REQUEST_SCHEMA = "residential.upstream_task.v0.2"
ENVELOPE_SCHEMA = "public_evidence_envelope.v1"
RESPONSE_SCHEMA = "residential.upstream_response.v0.2"
ADOPTION_SCHEMA = "residential.upstream_adoption_receipt.v0.2"

ACCEPTANCE_MODES = {"count_based", "quality_sufficiency", "hybrid"}
RESEARCH_CHARACTERISTICS = {
    "multiple_independent_queries",
    "support_and_counterevidence_required",
    "source_or_project_diversity_required",
    "comparative_or_pattern_judgment",
    "adaptive_extension_possible",
    "market_or_industry_generalization",
}
UPSTREAM_STATUSES = {"fulfilled", "partial", "gap", "stopped"}
ENVELOPE_STATUSES = {"fulfilled", "partial", "gap"}
EVIDENCE_CLASSES = {"fact_candidate", "soft_evidence", "platform_observation", "conflict", "gap"}
SOFT_CLASSES = {"soft_evidence", "platform_observation"}
HARD_FACT_USES = {
    "project_hard_fact",
    "market_generalization",
    "statistical_ratio",
    "population_prevalence",
    "client_final_claim",
    "super_competitiveness_fact",
}
PRIVATE_OR_LOCAL = re.compile(
    r"(?:/" + "Users/|" + "file" + r"://|[A-Za-z]:\\|\.workbuddy/|browser_profile|storage_state)",
    re.I,
)
SHA256 = re.compile(r"^[a-f0-9]{64}$")


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any, *, nonempty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (not nonempty or bool(value))
        and all(_nonempty(item) for item in value)
    )


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_strings(child)


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _private_errors(value: Any, label: str) -> list[str]:
    return [f"{label}: 不能包含本机路径或私有运行状态" for text in _walk_strings(value) if PRIVATE_OR_LOCAL.search(text)]


def _required(data: Any, fields: tuple[str, ...], label: str, errors: list[str]) -> bool:
    if not isinstance(data, dict):
        errors.append(f"{label}: 必须是对象")
        return False
    for field in fields:
        if field not in data:
            errors.append(f"{label}.{field}: 缺失")
    return True


def validate_request(request: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = (
        "schema", "request_id", "task_id", "project_id", "owner", "business_question",
        "judgment_gap", "requested_evidence_roles", "object_scope", "time_scope", "geo_scope",
        "downstream_destination", "acceptance_contract", "query_plan", "incremental_policy",
        "stop_conditions", "authorization", "status", "portability_boundary",
    )
    if not _required(request, required, "request", errors):
        return errors
    if request.get("schema") != REQUEST_SCHEMA:
        errors.append("request.schema: 必须为 residential.upstream_task.v0.2")
    for field in ("request_id", "task_id", "project_id", "business_question", "judgment_gap", "time_scope", "geo_scope"):
        if not _nonempty(request.get(field)):
            errors.append(f"request.{field}: 不能为空")
    if request.get("portability_boundary") != "no_shared_cwd_no_absolute_path_no_private_runtime_state":
        errors.append("request.portability_boundary: 必须声明双包物理独立边界")
    if not _string_list(request.get("requested_evidence_roles"), nonempty=True):
        errors.append("request.requested_evidence_roles: 至少需要一个证据职责")
    if not _string_list(request.get("stop_conditions"), nonempty=True):
        errors.append("request.stop_conditions: 至少需要一个停止条件")

    contract = request.get("acceptance_contract")
    if _required(
        contract,
        ("acceptance_mode", "qualified_match_classes", "quality_criteria", "count_threshold", "diversity_requirements", "research_characteristics"),
        "request.acceptance_contract",
        errors,
    ):
        mode = contract.get("acceptance_mode")
        if mode not in ACCEPTANCE_MODES:
            errors.append("request.acceptance_contract.acceptance_mode: 无效")
        if not _string_list(contract.get("qualified_match_classes"), nonempty=True):
            errors.append("request.acceptance_contract.qualified_match_classes: 不能为空")
        if mode in {"quality_sufficiency", "hybrid"} and not _string_list(contract.get("quality_criteria"), nonempty=True):
            errors.append("request.acceptance_contract.quality_criteria: 质量充分或混合模式必须明确质量条件")
        threshold = contract.get("count_threshold")
        if mode in {"count_based", "hybrid"} and (not isinstance(threshold, int) or isinstance(threshold, bool) or threshold < 1):
            errors.append("request.acceptance_contract.count_threshold: 计数或混合模式必须为正整数")
        characteristics = contract.get("research_characteristics")
        if not isinstance(characteristics, list) or not set(characteristics).issubset(RESEARCH_CHARACTERISTICS):
            errors.append("request.acceptance_contract.research_characteristics: 存在未知研究特征")
        diversity = contract.get("diversity_requirements")
        if not isinstance(diversity, dict) or any(
            not isinstance(diversity.get(field), int) or isinstance(diversity.get(field), bool) or diversity.get(field) < 1
            for field in ("minimum_source_role_count", "minimum_project_or_brand_count", "maximum_qualified_items_per_project_or_brand")
        ):
            errors.append("request.acceptance_contract.diversity_requirements: 三项多样性门槛必须为正整数")

    plan = request.get("query_plan")
    if _required(plan, ("mode", "channel_scope", "frozen_queries", "simple_direct_retrieval_exemption"), "request.query_plan", errors):
        plan_mode = plan.get("mode")
        queries = plan.get("frozen_queries")
        if plan_mode == "research_retrieval":
            if not isinstance(queries, list) or not queries:
                errors.append("request.query_plan.frozen_queries: 研究检索必须冻结至少一个查询")
            if plan.get("simple_direct_retrieval_exemption") is not None:
                errors.append("request.query_plan.simple_direct_retrieval_exemption: 研究检索不得声明简单获取豁免")
        elif plan_mode == "simple_direct_retrieval":
            exemption = plan.get("simple_direct_retrieval_exemption")
            if not isinstance(exemption, dict):
                errors.append("request.query_plan.simple_direct_retrieval_exemption: 简单定向获取必须有人工豁免")
            characteristics = (contract or {}).get("research_characteristics") or []
            if characteristics:
                errors.append("request.query_plan: 带研究特征的任务不得伪装成简单定向获取")
        else:
            errors.append("request.query_plan.mode: 无效")
        query_ids: set[str] = set()
        if isinstance(queries, list):
            for index, query in enumerate(queries):
                if not isinstance(query, dict):
                    errors.append(f"request.query_plan.frozen_queries[{index}]: 必须是对象")
                    continue
                query_id = query.get("query_id")
                if not _nonempty(query_id) or query_id in query_ids:
                    errors.append(f"request.query_plan.frozen_queries[{index}].query_id: 不能为空或重复")
                else:
                    query_ids.add(query_id)
                if not _nonempty(query.get("exact_query_text")) or not _nonempty(query.get("object_identity")):
                    errors.append(f"request.query_plan.frozen_queries[{index}]: 必须冻结精确词和对象身份")
                for field in ("minimum_result_batches", "minimum_actual_opens"):
                    value = query.get(field)
                    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                        errors.append(f"request.query_plan.frozen_queries[{index}].{field}: 必须为正整数")

    incremental = request.get("incremental_policy")
    if _required(
        incremental,
        ("proposal_allowed", "execution_authorized", "authorization_ref", "maximum_incremental_batches", "time_limit_minutes", "cost_limit", "minimum_marginal_information_gain"),
        "request.incremental_policy",
        errors,
    ):
        authorized = incremental.get("execution_authorized")
        authorization_ref = incremental.get("authorization_ref")
        maximum = incremental.get("maximum_incremental_batches")
        if authorized is True:
            if not _nonempty(authorization_ref) or not isinstance(maximum, int) or maximum < 1:
                errors.append("request.incremental_policy: 已授权增量必须有授权引用和正数批次上限")
        elif authorized is False:
            if authorization_ref is not None or maximum != 0:
                errors.append("request.incremental_policy: 未授权增量不得伪造授权引用或执行批次")
        else:
            errors.append("request.incremental_policy.execution_authorized: 必须为布尔值")

    errors.extend(_private_errors(request, "request"))
    return sorted(set(errors))


def validate_envelope(envelope: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = (
        "schema", "package_id", "task_id", "request_id", "project_id", "subject", "release_version",
        "upstream_status", "downstream_acceptance", "request", "query_execution", "sources", "items",
        "negative_hits", "conflicts", "gaps", "stop_reason", "package_boundary",
    )
    if not _required(envelope, required, "envelope", errors):
        return errors
    if envelope.get("schema") != ENVELOPE_SCHEMA:
        errors.append("envelope.schema: 必须为 public_evidence_envelope.v1")
    if envelope.get("upstream_status") not in ENVELOPE_STATUSES:
        errors.append("envelope.upstream_status: 无效")
    acceptance = envelope.get("downstream_acceptance")
    if not isinstance(acceptance, dict) or acceptance.get("status") != "not_assessed" or acceptance.get("decided_by") is not None:
        errors.append("envelope.downstream_acceptance: 上游证据包不得声称下游已经采用")

    sources = envelope.get("sources")
    source_ids: set[str] = set()
    if not isinstance(sources, list):
        errors.append("envelope.sources: 必须是数组")
        sources = []
    for index, source in enumerate(sources):
        source_id = source.get("source_id") if isinstance(source, dict) else None
        if not _nonempty(source_id) or source_id in source_ids:
            errors.append(f"envelope.sources[{index}].source_id: 不能为空或重复")
        else:
            source_ids.add(source_id)

    items = envelope.get("items")
    item_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(items, list):
        errors.append("envelope.items: 必须是数组")
        items = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"envelope.items[{index}]: 必须是对象")
            continue
        item_id = item.get("item_id")
        if not _nonempty(item_id) or item_id in item_by_id:
            errors.append(f"envelope.items[{index}].item_id: 不能为空或重复")
            continue
        item_by_id[item_id] = item
        evidence_class = item.get("evidence_class")
        if evidence_class not in EVIDENCE_CLASSES:
            errors.append(f"envelope.items[{index}].evidence_class: 无效")
        refs = item.get("source_refs")
        if not isinstance(refs, list) or any(ref not in source_ids for ref in refs):
            errors.append(f"envelope.items[{index}].source_refs: 引用了未知来源")
        if evidence_class in SOFT_CLASSES:
            blocked = set(item.get("blocked_use") or [])
            if not {"project_hard_fact", "market_generalization"}.issubset(blocked):
                errors.append(f"envelope.items[{index}]: 软证据必须禁止硬事实和市场总体推导")

    negative_hits = envelope.get("negative_hits")
    negative_ids: set[str] = set()
    if not isinstance(negative_hits, list):
        errors.append("envelope.negative_hits: 必须是数组")
        negative_hits = []
    for index, hit in enumerate(negative_hits):
        hit_id = hit.get("negative_hit_id") if isinstance(hit, dict) else None
        if not _nonempty(hit_id) or hit_id in negative_ids:
            errors.append(f"envelope.negative_hits[{index}].negative_hit_id: 不能为空或重复")
        else:
            negative_ids.add(hit_id)

    conflicts = envelope.get("conflicts")
    gaps = envelope.get("gaps")
    if not _string_list(conflicts):
        errors.append("envelope.conflicts: 必须是字符串数组")
        conflicts = []
    if not _string_list(gaps):
        errors.append("envelope.gaps: 必须是字符串数组")
        gaps = []
    actual_conflicts = {item_id for item_id, item in item_by_id.items() if item.get("evidence_class") == "conflict"}
    actual_gaps = {item_id for item_id, item in item_by_id.items() if item.get("evidence_class") == "gap"}
    if set(conflicts) != actual_conflicts:
        errors.append("envelope.conflicts: 必须逐项保留所有冲突")
    if set(gaps) != actual_gaps:
        errors.append("envelope.gaps: 必须逐项保留所有缺口")
    if not _nonempty(envelope.get("stop_reason")):
        errors.append("envelope.stop_reason: 不能为空")
    errors.extend(_private_errors(envelope, "envelope"))
    return sorted(set(errors))


def validate_response(
    request: dict[str, Any], envelope: dict[str, Any], response: dict[str, Any], compatibility: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    required = (
        "schema", "request_id", "task_id", "project_id", "upstream_owner", "status", "evidence_envelope",
        "sufficiency", "negative_hits", "conflicts", "gaps", "stop_reason",
        "upstream_does_not_adjudicate_strategy", "fulfilled_does_not_equal_accepted",
    )
    if not _required(response, required, "response", errors):
        return errors
    if response.get("schema") != RESPONSE_SCHEMA:
        errors.append("response.schema: 必须为 residential.upstream_response.v0.2")
    for field in ("request_id", "task_id", "project_id"):
        if response.get(field) != request.get(field) or response.get(field) != envelope.get(field):
            errors.append(f"response.{field}: 请求、证据包和回传必须一致")
    if response.get("status") not in UPSTREAM_STATUSES:
        errors.append("response.status: 无效")
    if response.get("status") != "stopped" and response.get("status") != envelope.get("upstream_status"):
        errors.append("response.status: 必须与证据包上游状态一致")
    if response.get("upstream_does_not_adjudicate_strategy") is not True:
        errors.append("response: 上游不得裁定直接竞品、价值锚点或SC")
    if response.get("fulfilled_does_not_equal_accepted") is not True:
        errors.append("response: fulfilled不得冒充下游accepted")

    envelope_ref = response.get("evidence_envelope")
    if not isinstance(envelope_ref, dict):
        errors.append("response.evidence_envelope: 必须是对象")
    else:
        if envelope_ref.get("schema") != ENVELOPE_SCHEMA or envelope_ref.get("package_id") != envelope.get("package_id"):
            errors.append("response.evidence_envelope: Schema或package_id不一致")
        if envelope_ref.get("content_sha256") != canonical_json_sha256(envelope):
            errors.append("response.evidence_envelope.content_sha256: 与证据包内容不一致")
        expected_schema_hash = compatibility.get("upstream_evidence_contract", {}).get("schema_sha256")
        actual_schema_hash = envelope_ref.get("schema_sha256")
        if compatibility.get("status") == "compatible_frozen":
            if not _nonempty(expected_schema_hash) or actual_schema_hash != expected_schema_hash:
                errors.append("response.evidence_envelope.schema_sha256: 未匹配冻结上游Schema")
        elif actual_schema_hash is not None and not SHA256.fullmatch(str(actual_schema_hash)):
            errors.append("response.evidence_envelope.schema_sha256: 必须为空或64位SHA-256")
        if envelope_ref.get("transfer_mode") == "artifact":
            artifact_ref = envelope_ref.get("artifact_ref")
            if not _nonempty(artifact_ref) or PRIVATE_OR_LOCAL.search(artifact_ref):
                errors.append("response.evidence_envelope.artifact_ref: artifact模式只能使用可移植引用")
        elif envelope_ref.get("transfer_mode") == "inline":
            if envelope_ref.get("artifact_ref") is not None:
                errors.append("response.evidence_envelope.artifact_ref: inline模式必须为空")
        else:
            errors.append("response.evidence_envelope.transfer_mode: 无效")

    envelope_negative_ids = [hit.get("negative_hit_id") for hit in envelope.get("negative_hits", []) if isinstance(hit, dict)]
    if response.get("negative_hits") != envelope_negative_ids:
        errors.append("response.negative_hits: 不得丢弃、增补或重排上游负命中")
    if response.get("conflicts") != envelope.get("conflicts"):
        errors.append("response.conflicts: 不得丢弃、增补或重排上游冲突")
    if response.get("gaps") != envelope.get("gaps"):
        errors.append("response.gaps: 不得丢弃、增补或重排上游缺口")
    if response.get("stop_reason") != envelope.get("stop_reason"):
        errors.append("response.stop_reason: 必须原样保留上游停止原因")

    sufficiency = response.get("sufficiency")
    execution = envelope.get("query_execution") or {}
    request_contract = request.get("acceptance_contract") or {}
    if not isinstance(sufficiency, dict):
        errors.append("response.sufficiency: 必须是对象")
    else:
        if sufficiency.get("acceptance_mode") != request_contract.get("acceptance_mode") or sufficiency.get("acceptance_mode") != execution.get("acceptance_mode"):
            errors.append("response.sufficiency.acceptance_mode: 请求与执行口径不一致")
        if sufficiency.get("evidence_sufficiency_status") != execution.get("evidence_sufficiency_status"):
            errors.append("response.sufficiency.evidence_sufficiency_status: 必须来自上游执行回执")
        if sufficiency.get("executed_query_ids") != execution.get("executed_query_ids"):
            errors.append("response.sufficiency.executed_query_ids: 与证据包不一致")
        if sufficiency.get("proposed_incremental_query_ids") != execution.get("proposed_incremental_query_ids"):
            errors.append("response.sufficiency.proposed_incremental_query_ids: 与证据包不一致")
        if sufficiency.get("failure_attribution_complete") is not True:
            errors.append("response.sufficiency.failure_attribution_complete: 必须闭合失败归因")
    errors.extend(_private_errors(response, "response"))
    return sorted(set(errors))


def validate_adoption(
    request: dict[str, Any], envelope: dict[str, Any], response: dict[str, Any], adoption: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    required = (
        "schema", "request_id", "task_id", "project_id", "evidence_package", "upstream_status",
        "downstream_acceptance", "accepted_items", "rejected_items", "unresolved_conflicts", "unresolved_gaps",
        "incremental_decision", "judgment_effect", "accepted_by", "accepted_at",
        "machine_check_does_not_approve_business_quality",
    )
    if not _required(adoption, required, "adoption", errors):
        return errors
    if adoption.get("schema") != ADOPTION_SCHEMA:
        errors.append("adoption.schema: 必须为 residential.upstream_adoption_receipt.v0.2")
    for field in ("request_id", "task_id", "project_id"):
        if adoption.get(field) != request.get(field):
            errors.append(f"adoption.{field}: 必须与原请求一致")
    if adoption.get("upstream_status") != response.get("status"):
        errors.append("adoption.upstream_status: 必须保留上游真实状态")
    if adoption.get("downstream_acceptance") not in {"accepted", "accepted_with_conditions", "rejected"}:
        errors.append("adoption.downstream_acceptance: 必须由下游明确决定")
    if adoption.get("machine_check_does_not_approve_business_quality") is not True:
        errors.append("adoption: 机器检查不得冒充业务质量批准")

    package = adoption.get("evidence_package")
    expected_hash = canonical_json_sha256(envelope)
    if not isinstance(package, dict) or package.get("schema") != ENVELOPE_SCHEMA or package.get("package_id") != envelope.get("package_id") or package.get("content_sha256") != expected_hash:
        errors.append("adoption.evidence_package: 必须绑定实际证据包Schema、ID和内容哈希")

    item_by_id = {item.get("item_id"): item for item in envelope.get("items", []) if isinstance(item, dict) and _nonempty(item.get("item_id"))}
    accepted = adoption.get("accepted_items")
    rejected = adoption.get("rejected_items")
    accepted_ids: set[str] = set()
    rejected_ids: set[str] = set()
    if not isinstance(accepted, list) or not isinstance(rejected, list):
        errors.append("adoption.accepted_items/rejected_items: 必须是数组")
        accepted, rejected = [], []
    for index, row in enumerate(accepted):
        item_id = row.get("item_id") if isinstance(row, dict) else None
        if item_id not in item_by_id or item_id in accepted_ids:
            errors.append(f"adoption.accepted_items[{index}].item_id: 未知或重复")
            continue
        accepted_ids.add(item_id)
        uses = set(row.get("allowed_uses") or [])
        if not uses:
            errors.append(f"adoption.accepted_items[{index}].allowed_uses: 不能为空")
        item = item_by_id[item_id]
        if item.get("evidence_class") in SOFT_CLASSES and uses & HARD_FACT_USES:
            errors.append(f"adoption.accepted_items[{index}]: 软证据不得升级为硬事实、总体结论或SC事实")
        if not uses.issubset(set(item.get("allowed_use") or [])):
            errors.append(f"adoption.accepted_items[{index}]: 采用用途超出上游允许边界")
    for index, row in enumerate(rejected):
        item_id = row.get("item_id") if isinstance(row, dict) else None
        if item_id not in item_by_id or item_id in rejected_ids:
            errors.append(f"adoption.rejected_items[{index}].item_id: 未知或重复")
        else:
            rejected_ids.add(item_id)
        if not isinstance(row, dict) or not _nonempty(row.get("reason")):
            errors.append(f"adoption.rejected_items[{index}].reason: 不能为空")
    if accepted_ids & rejected_ids:
        errors.append("adoption: 同一证据项不得同时接受和拒绝")
    adjudicable = {
        item_id for item_id, item in item_by_id.items() if item.get("evidence_class") not in {"conflict", "gap"}
    }
    if accepted_ids | rejected_ids != adjudicable:
        errors.append("adoption: 每个事实或观察项都必须明确接受或拒绝")
    if set(adoption.get("unresolved_conflicts") or []) != set(envelope.get("conflicts") or []):
        errors.append("adoption.unresolved_conflicts: 本轮必须保留所有未解冲突")
    if set(adoption.get("unresolved_gaps") or []) != set(envelope.get("gaps") or []):
        errors.append("adoption.unresolved_gaps: 本轮必须保留所有未解缺口")

    decision = adoption.get("incremental_decision")
    if not isinstance(decision, dict):
        errors.append("adoption.incremental_decision: 必须是对象")
    else:
        proposed = set((response.get("sufficiency") or {}).get("proposed_incremental_query_ids") or [])
        authorized = set(decision.get("authorized_query_ids") or [])
        if decision.get("decision") == "authorize_incremental":
            if not authorized or not authorized.issubset(proposed):
                errors.append("adoption.incremental_decision: 只能授权上游已提出的增量查询")
            if not (request.get("incremental_policy") or {}).get("proposal_allowed"):
                errors.append("adoption.incremental_decision: 原请求未允许上游提出增量方案")
        elif authorized:
            errors.append("adoption.incremental_decision: 非授权决定不得携带查询ID")
    errors.extend(_private_errors(adoption, "adoption"))
    return sorted(set(errors))


def validate_exchange(
    request: dict[str, Any],
    envelope: dict[str, Any],
    response: dict[str, Any],
    adoption: dict[str, Any] | None = None,
    compatibility: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if compatibility is None:
        compatibility = json.loads(COMPATIBILITY_PATH.read_text(encoding="utf-8"))
    errors = validate_request(request)
    errors.extend(validate_envelope(envelope))
    errors.extend(validate_response(request, envelope, response, compatibility))
    if adoption is not None:
        errors.extend(validate_adoption(request, envelope, response, adoption))
    errors = sorted(set(errors))
    return {
        "schema": "residential.upstream_exchange_validation_receipt.v0.2",
        "status": "pass" if not errors else "fail",
        "error_count": len(errors),
        "errors": errors,
        "request_id": request.get("request_id"),
        "package_id": envelope.get("package_id"),
        "adoption_checked": adoption is not None,
        "compatibility_status": compatibility.get("status"),
        "machine_check_does_not_approve_business_quality": True,
    }


def _load(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON根节点必须为对象")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--envelope", required=True)
    parser.add_argument("--response", required=True)
    parser.add_argument("--adoption")
    parser.add_argument("--compatibility", default=str(COMPATIBILITY_PATH))
    args = parser.parse_args()
    receipt = validate_exchange(
        _load(args.request),
        _load(args.envelope),
        _load(args.response),
        _load(args.adoption) if args.adoption else None,
        _load(args.compatibility),
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
