#!/usr/bin/env python3
"""Dependency-free semantic and platform-contract validation for RC1."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


ABSOLUTE_OR_PRIVATE = re.compile(
    r"(?:/Users/|/home/|/Applications/|file://|(?<![A-Za-z])[A-Za-z]:[\\/]|\$\{?CODEX_WORKSPACE\}?|@oai/artifact-tool)",
    re.IGNORECASE,
)


class ContractError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _walk_strings(value: Any, prefix: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield prefix, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_strings(child, f"{prefix}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_strings(child, f"{prefix}[{index}]")


def assert_no_private_paths(value: Any) -> None:
    hits = [f"{path}={text}" for path, text in _walk_strings(value) if ABSOLUTE_OR_PRIVATE.search(text)]
    if hits:
        raise ContractError("发现本机或私有运行时痕迹：" + "; ".join(hits[:5]))


def assert_safe_relative_path(value: str, label: str) -> None:
    normalized = value.replace("\\", "/")
    if not normalized or normalized.startswith("/") or ".." in normalized.split("/"):
        raise ContractError(f"{label}必须是安全相对路径：{value!r}")
    if ABSOLUTE_OR_PRIVATE.search(normalized):
        raise ContractError(f"{label}包含本机路径：{value!r}")


def validate_semantic_core(core: dict[str, Any]) -> None:
    if core.get("schema") != "residential.semantic_core.v0.1":
        raise ContractError("semantic core schema不匹配")
    if core.get("status") != "approved_for_fictional_demo":
        raise ContractError("虚构语义核未批准用于示例")
    if "虚构" not in str(core.get("fixture_notice", "")):
        raise ContractError("缺少全量虚构声明")
    project_id = str(core.get("project", {}).get("id", ""))
    if not project_id.startswith("fictional-"):
        raise ContractError("示例项目ID必须以fictional-开头")
    evidence_ids = {item.get("id") for item in core.get("evidence_registry", [])}
    if len(evidence_ids) < 5 or None in evidence_ids:
        raise ContractError("证据登记不完整")
    decisions = core.get("customer_decisions", [])
    decision_ids = {item.get("id") for item in decisions}
    if len(decision_ids) < 3:
        raise ContractError("至少需要三项客户选择机制")
    dimensions = core.get("dimensions", [])
    if not 3 <= len(dimensions) <= 4:
        raise ContractError("必须形成3—4个竞争维度")
    sc_ids = []
    for dimension in dimensions:
        if len(dimension.get("subject_strengths", [])) != 3:
            raise ContractError(f"{dimension.get('id')}必须有三项本案价值")
        if not dimension.get("competitors") or not dimension.get("conclusions"):
            raise ContractError(f"{dimension.get('id')}缺少竞品或结论")
        sc = dimension.get("super_competitiveness", {})
        sc_ids.append(sc.get("id"))
        bounded = sc.get("bounded_superlative", {})
        if not all(bounded.get(key) for key in ("comparison_set", "purchase_task", "claim")):
            raise ContractError(f"{sc.get('id')}缺少比较边界")
        unknown = set(sc.get("evidence_refs", [])) - evidence_ids
        if unknown:
            raise ContractError(f"{sc.get('id')}引用未知证据：{sorted(unknown)}")
        unknown_decisions = set(sc.get("customer_decision_refs", [])) - decision_ids
        if unknown_decisions:
            raise ContractError(f"{sc.get('id')}引用未知客户机制：{sorted(unknown_decisions)}")
    if len(set(sc_ids)) != len(sc_ids) or None in sc_ids:
        raise ContractError("超级竞争力ID重复或缺失")
    if set(core.get("value_anchor", {}).get("super_competitiveness_refs", [])) != set(sc_ids):
        raise ContractError("价值锚点未完整引用超级竞争力")
    pages = core.get("presentation_pages", [])
    page_ids = [item.get("page_id") for item in pages]
    if len(pages) < 7 or len(set(page_ids)) != len(page_ids):
        raise ContractError("生产页面不足或页面ID重复")
    assert_no_private_paths(core)


def validate_presentation_request(request: dict[str, Any]) -> None:
    if request.get("schema") != "residential.presentation_request.v0.1":
        raise ContractError("presentation request schema不匹配")
    artifact = request.get("artifact_requirements", {})
    if artifact.get("format") != "pptx" or artifact.get("editable") is not True:
        raise ContractError("平台请求必须要求可编辑PPTX")
    if artifact.get("formal_visual_generation_owner") != "platform_adapter":
        raise ContractError("正式视觉责任必须属于platform_adapter")
    sc_ids = request.get("semantic_core", {}).get("super_competitiveness_ids", [])
    if not 3 <= len(sc_ids) <= 4 or len(set(sc_ids)) != len(sc_ids):
        raise ContractError("平台请求必须带3—4个唯一超级竞争力ID")
    pages = request.get("pages", [])
    page_ids = [item.get("page_id") for item in pages]
    if not pages or len(set(page_ids)) != len(page_ids):
        raise ContractError("平台请求页面为空或ID重复")
    for page in pages:
        for field in ("page_id", "role", "title", "key_message", "visual_brief"):
            if not str(page.get(field, "")).strip():
                raise ContractError(f"页面{page.get('page_id')}缺少{field}")
        if not page.get("evidence_refs") or not page.get("acceptance"):
            raise ContractError(f"页面{page.get('page_id')}缺少证据或验收要求")
        unknown = set(page.get("super_competitiveness_refs", [])) - set(sc_ids)
        if unknown:
            raise ContractError(f"页面{page.get('page_id')}引用未知超级竞争力：{sorted(unknown)}")
    required_returns = set(request.get("return_requirements", []))
    expected_returns = {
        "editable_artifact",
        "page_mapping",
        "object_mapping",
        "page_preview_or_equivalent_visual_evidence",
        "qa_evidence",
        "explicit_gaps",
    }
    if not expected_returns.issubset(required_returns):
        raise ContractError("平台回传要求不完整")
    assert_no_private_paths(request)


def validate_presentation_response(
    response: dict[str, Any], request: dict[str, Any], response_dir: Path
) -> None:
    if response.get("schema") != "residential.presentation_response.v0.1":
        raise ContractError("presentation response schema不匹配")
    if response.get("status") not in {"complete", "test_double_complete"}:
        raise ContractError("平台未返回可验收产物")
    artifact = response.get("artifact", {})
    artifact_path = str(artifact.get("path", ""))
    assert_safe_relative_path(artifact_path, "artifact.path")
    actual_artifact = response_dir / artifact_path
    if not actual_artifact.is_file():
        raise ContractError("平台产物文件不存在")
    if artifact.get("editable") is not True or artifact.get("sha256") != sha256_file(actual_artifact):
        raise ContractError("平台产物不可编辑或哈希不一致")
    request_ids = [page["page_id"] for page in request["pages"]]
    mapped_ids = [item.get("page_id") for item in response.get("page_mapping", [])]
    if request_ids != mapped_ids:
        raise ContractError("平台页面映射与请求顺序不一致")
    if artifact.get("slide_count") != len(request_ids):
        raise ContractError("平台产物页数与请求不一致")
    for item in response.get("page_mapping", []):
        if not item.get("object_ids"):
            raise ContractError(f"页面{item.get('page_id')}缺少对象映射")
    visual = response.get("visual_evidence", {})
    visual_path = str(visual.get("path", ""))
    assert_safe_relative_path(visual_path, "visual_evidence.path")
    if not (response_dir / visual_path).is_file():
        raise ContractError("平台视觉证据不存在")
    if response.get("status") == "test_double_complete":
        codes = {item.get("code") for item in response.get("gaps", [])}
        if "FORMAL_VISUAL_REVIEW_REQUIRED" not in codes:
            raise ContractError("测试适配器必须显式保留正式视觉复核gap")
        if visual.get("formal_visual_review") != "not_evaluated_test_double":
            raise ContractError("测试适配器不得声称正式视觉已复核")
    assert_no_private_paths(response)


def validate_product5_config(config: dict[str, Any], expected_sc_ids: set[str]) -> None:
    if config.get("schema") != "residential.product5_config.v0.1":
        raise ContractError("product5 config schema不匹配")
    if "虚构" not in str(config.get("project", {}).get("fixture_notice", "")):
        raise ContractError("产物5缺少虚构声明")
    actual_sc_ids = {item.get("id") for item in config.get("super_competitiveness", [])}
    if actual_sc_ids != expected_sc_ids:
        raise ContractError("产物5未完整消费同一超级竞争力集合")
    if not config.get("family_routes") or not config.get("evidence_gaps"):
        raise ContractError("产物5缺少家庭路径或证据缺口")
    if config.get("publication_state") != "not_published":
        raise ContractError("RC1产物5必须保持未发布")
    experience = config.get("experience", {})
    chapters = experience.get("chapters", [])
    if [item.get("id") for item in chapters] != ["home", "city", "community", "living", "advisor"]:
        raise ContractError("产物5缺少完整桌面章节与AI推荐入口")
    advisor = experience.get("advisor", {})
    if len(advisor.get("questions", [])) != 4 or len(advisor.get("routes", [])) < 3:
        raise ContractError("产物5推荐官缺少四问分流或三类专属路线")
    for route in advisor.get("routes", []):
        if (
            len(route.get("reasons", [])) != 3
            or len(route.get("visit", [])) != 3
            or len(route.get("compare", [])) != 2
            or not str(route.get("next", "")).strip()
        ):
            raise ContractError(f"产物5路线信息密度不足：{route.get('slug')}")
        if not str(route.get("image", "")).startswith("/assets/"):
            raise ContractError(f"产物5路线素材必须使用包内相对资产：{route.get('slug')}")
    assert_no_private_paths(config)


def validate_delivery_receipt(receipt: dict[str, Any], receipt_dir: Path) -> None:
    if receipt.get("schema") != "residential.public_delivery_receipt.v0.1":
        raise ContractError("delivery receipt schema不匹配")
    if receipt.get("status") != "local_fictional_e2e_pass":
        raise ContractError("本地虚构闭环未通过")
    verification = receipt.get("verification", {})
    required_pass = ("method_contracts", "platform_roundtrip", "pptx_structure", "product5_static_bundle")
    if any(verification.get(key) != "pass" for key in required_pass):
        raise ContractError("交付回执的公共核心验证未全部通过")
    if verification.get("cross_machine") != "not_run" or verification.get("workbuddy") != "not_run":
        raise ContractError("本地回执不得冒充跨机器或WorkBuddy验证")
    if verification.get("formal_visual") != "platform_review_required":
        raise ContractError("本地回执必须保留正式视觉责任")
    publication = receipt.get("publication", {})
    if any(
        publication.get(key) is not True
        for key in ("authorized", "license_selected", "public_repository_created")
    ):
        raise ContractError("公共RC回执缺少公开发行状态")
    if publication.get("license") != "Apache-2.0":
        raise ContractError("公共RC回执许可证必须为Apache-2.0")
    if publication.get("repository") != (
        "https://github.com/xiem-bit/residential-project-interpretation-service-public"
    ):
        raise ContractError("公共RC回执仓库地址不匹配")
    for label, item in receipt.get("outputs", {}).items():
        relative = str(item.get("path", ""))
        assert_safe_relative_path(relative, f"outputs.{label}.path")
        path = receipt_dir / relative
        if not path.is_file() or item.get("sha256") != sha256_file(path):
            raise ContractError(f"交付输出不存在或哈希不一致：{label}")
    assert_no_private_paths(receipt)
