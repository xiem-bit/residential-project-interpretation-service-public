#!/usr/bin/env python3
"""Verify a real WorkBuddy adapter return and emit the external cold-start receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_environment import check_environment  # noqa: E402
from scripts.run_rc1_demo import (  # noqa: E402
    install_node_dependencies,
    output_record,
    run,
    scan_generated_tree,
)
from tools.rc1.build_demo_contracts import load_json, write_json  # noqa: E402
from tools.rc1.validate_rc1_contracts import (  # noqa: E402
    ContractError,
    assert_no_private_paths,
    assert_safe_relative_path,
    sha256_file,
    validate_presentation_request,
    validate_presentation_response,
)


DEFAULT_WORKSPACE = ROOT / "verification-tmp/external-cold-start"
EXPECTED_REPOSITORY = "https://github.com/xiem-bit/residential-project-interpretation-service-public"
EXPECTED_TAG = "v0.1.0-rc.1"


def require_workspace(path: Path) -> Path:
    resolved = path.resolve()
    allowed_root = (ROOT / "verification-tmp").resolve()
    if resolved.parent != allowed_root or resolved.name != "external-cold-start":
        raise ContractError("外部冷启动工作区必须是verification-tmp/external-cold-start")
    return resolved


def assert_external_platform_claim(response: dict[str, Any]) -> None:
    if response.get("status") != "complete":
        raise ContractError("WorkBuddy回传status必须为complete，测试适配器或gap不能通过")
    producer = response.get("producer", {})
    if "workbuddy" not in str(producer.get("platform", "")).lower():
        raise ContractError("producer.platform必须明确为WorkBuddy")
    if producer.get("formal_visual_renderer") is not True:
        raise ContractError("WorkBuddy回传必须确认使用正式视觉生产能力")
    if any(item.get("blocking_for_real_client_delivery") is True for item in response.get("gaps", [])):
        raise ContractError("平台仍有阻塞真实交付的gap")


def validate_observation(observation: dict[str, Any]) -> None:
    if observation.get("schema") != "residential.external_cold_start_observation.v0.1":
        raise ContractError("冷启动观察记录schema不匹配")
    if observation.get("status") != "complete":
        raise ContractError("冷启动观察记录尚未完成")
    acquisition = observation.get("acquisition", {})
    if acquisition.get("repository") != EXPECTED_REPOSITORY or acquisition.get("tag") != EXPECTED_TAG:
        raise ContractError("冷启动不是从指定GitHub仓库固定tag取得")
    required_true = {"obtained_from_github": True}
    required_false = {
        "private_source_repository_access": False,
        "local_rc_directory_provided": False,
        "history_chat_provided": False,
    }
    for field, expected in {**required_true, **required_false}.items():
        if acquisition.get(field) is not expected:
            raise ContractError(f"冷启动获取边界不成立：{field}")
    platform = observation.get("platform", {})
    if platform.get("workbuddy_used") is not True or not platform.get("skills_selected_by_workbuddy"):
        raise ContractError("未证明WorkBuddy自主选择并使用平台能力")
    assistance = observation.get("assistance", {})
    if assistance.get("content_guidance_count") != 0:
        raise ContractError("首次正式冷启动出现了工程内容指导")
    if not str(observation.get("tester_attestation", "")).strip():
        raise ContractError("测试者尚未填写确认说明")
    assert_no_private_paths(observation)


def validate_presentation_visual_review(
    review: dict[str, Any], presentation_dir: Path, expected_page_ids: list[str]
) -> None:
    if review.get("schema") != "residential.presentation_visual_review.v0.1":
        raise ContractError("PPT视觉复核schema不匹配")
    if review.get("status") != "pass" or review.get("formal_visual_review") != "pass":
        raise ContractError("PPT正式视觉复核未通过")
    if "workbuddy" not in str(review.get("platform", "")).lower():
        raise ContractError("PPT视觉证据不是由WorkBuddy流程返回")
    pages = review.get("pages", [])
    page_ids = [item.get("page_id") for item in pages]
    if page_ids != expected_page_ids:
        raise ContractError("逐页视觉证据与请求页面不一致")
    for item in pages:
        if item.get("status") != "pass" or item.get("overflow") not in {"none", "pass"}:
            raise ContractError(f"页面{item.get('page_id')}视觉或溢出检查未通过")
        relative = str(item.get("preview_path", ""))
        assert_safe_relative_path(relative, f"{item.get('page_id')}.preview_path")
        preview = presentation_dir / relative
        if not preview.is_file() or preview.stat().st_size == 0:
            raise ContractError(f"页面{item.get('page_id')}预览不存在")
    assert_no_private_paths(review)


def validate_product5_visual_review(review: dict[str, Any], product5_dir: Path) -> None:
    if review.get("schema") != "residential.product5_visual_review.v0.1":
        raise ContractError("产物5视觉复核schema不匹配")
    if review.get("status") != "pass" or review.get("formal_visual_review") != "pass":
        raise ContractError("产物5正式视觉复核未通过")
    if "workbuddy" not in str(review.get("platform", "")).lower():
        raise ContractError("产物5视觉证据不是由WorkBuddy流程返回")
    views = review.get("views", [])
    if [item.get("view") for item in views] != ["desktop", "mobile"]:
        raise ContractError("产物5必须按桌面、手机顺序完成两种视图复核")
    for item in views:
        if item.get("status") != "pass":
            raise ContractError(f"产物5 {item.get('view')} 视图未通过")
        relative = str(item.get("screenshot_path", ""))
        assert_safe_relative_path(relative, f"product5.{item.get('view')}.screenshot_path")
        screenshot = product5_dir / relative
        if not screenshot.is_file() or screenshot.stat().st_size == 0:
            raise ContractError(f"产物5 {item.get('view')} 截图不存在")
    if review.get("relative_navigation") != "pass" or review.get("external_resource_scan") != "pass":
        raise ContractError("产物5相对导航或外部资源检查未通过")
    assert_no_private_paths(review)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-node-deps", action="store_true")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    args = parser.parse_args()
    workspace = require_workspace(args.workspace)
    environment = check_environment()
    if environment["status"] != "pass":
        raise ContractError("标准Python/Node环境检查未通过")
    install_node_dependencies(args.install_node_deps)

    handoff = load_json(workspace / "handoff.json")
    if handoff.get("status") != "awaiting_workbuddy_platform_adapter":
        raise ContractError("外部交接包状态不正确")
    request_path = workspace / handoff["presentation_request"]
    request = load_json(request_path)
    validate_presentation_request(request)
    if sha256_file(request_path) != handoff.get("presentation_request_sha256"):
        raise ContractError("平台请求已在交接后发生变化")

    presentation_dir = workspace / "presentation"
    response_path = presentation_dir / "platform-response.json"
    response = load_json(response_path)
    assert_external_platform_claim(response)
    if response.get("request_sha256") != sha256_file(request_path):
        raise ContractError("WorkBuddy回传没有消费当前平台请求")
    validate_presentation_response(response, request, presentation_dir)

    visual_path = presentation_dir / response["visual_evidence"]["path"]
    if response["visual_evidence"].get("sha256") != sha256_file(visual_path):
        raise ContractError("PPT视觉证据哈希不一致")
    presentation_review = load_json(visual_path)
    expected_page_ids = handoff["expected_page_ids"]
    validate_presentation_visual_review(presentation_review, presentation_dir, expected_page_ids)

    pptx_path = presentation_dir / response["artifact"]["path"]
    package_report = json.loads(
        run(
            [
                "node",
                "tools/product3_ppt_pipeline/automizer_adapter/verify_pptx_package.mjs",
                "--pptx",
                str(pptx_path),
                "--expected-slides",
                str(len(expected_page_ids)),
            ]
        )
    )
    if package_report.get("status") != "pass":
        raise ContractError("WorkBuddy PPTX结构安全检查未通过")
    package_report_path = presentation_dir / "pptx-package-qa-external.json"
    write_json(package_report_path, package_report)

    product5_dir = workspace / "product5"
    product5_review_path = product5_dir / "product5-visual-review.json"
    product5_review = load_json(product5_review_path)
    validate_product5_visual_review(product5_review, product5_dir)
    static_manifest_path = product5_dir / "bundle-manifest.json"
    static_verify = json.loads(
        run(
            [
                "node",
                "tools/ue_static_bundle/verify_manifest.mjs",
                str(static_manifest_path),
                str(product5_dir / "site"),
            ]
        )
    )
    if static_verify.get("status") != "pass":
        raise ContractError("产物5静态包复核未通过")

    observation_path = workspace / "cold-start-observation.json"
    observation = load_json(observation_path)
    validate_observation(observation)

    outputs = {
        "presentation_request": output_record(request_path, workspace),
        "platform_response": output_record(response_path, workspace),
        "editable_pptx": output_record(pptx_path, workspace),
        "presentation_visual_review": output_record(visual_path, workspace),
        "pptx_package_qa": output_record(package_report_path, workspace),
        "product5_static_manifest": output_record(static_manifest_path, workspace),
        "product5_visual_review": output_record(product5_review_path, workspace),
        "cold_start_observation": output_record(observation_path, workspace),
    }
    aggregate_input = "".join(f"{key}:{item['sha256']}\n" for key, item in sorted(outputs.items()))
    receipt = {
        "schema": "residential.public_delivery_receipt.v0.1",
        "status": "workbuddy_fictional_e2e_pass",
        "project_id": handoff["project_id"],
        "fixture_notice": handoff["fixture_notice"],
        "source": {"repository": EXPECTED_REPOSITORY, "tag": EXPECTED_TAG},
        "environment": environment,
        "verification": {
            "method_contracts": "pass",
            "platform_roundtrip": "pass",
            "pptx_structure": "pass",
            "product5_static_bundle": "pass",
            "formal_visual": "pass",
            "cross_machine": "pass",
            "workbuddy": "pass",
        },
        "assistance": observation["assistance"],
        "outputs": outputs,
        "aggregate_output_sha256": hashlib.sha256(aggregate_input.encode("utf-8")).hexdigest(),
        "gaps": [
            {
                "code": "REAL_PROJECT_EFFECT_NOT_VALIDATED_BY_THIS_FIXTURE",
                "blocking_for_fictional_cold_start": False,
                "blocking_for_real_project_claim": True,
            },
        ],
        "publication": {
            "authorized": True,
            "license_selected": True,
            "license": "Apache-2.0",
            "public_repository_created": True,
            "repository": EXPECTED_REPOSITORY,
        },
    }
    assert_no_private_paths(receipt)
    receipt_path = workspace / "external-delivery-receipt.json"
    write_json(receipt_path, receipt)
    scan_generated_tree(workspace)
    print("EXTERNAL PLATFORM COLD START: PASS")
    print("receipt: verification-tmp/external-cold-start/external-delivery-receipt.json")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContractError, RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"EXTERNAL PLATFORM COLD START: FAIL\n{exc}", file=sys.stderr)
        raise SystemExit(1)
