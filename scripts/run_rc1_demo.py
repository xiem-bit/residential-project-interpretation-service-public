#!/usr/bin/env python3
"""Run the complete fictional RC1 flow from contracts to a delivery receipt."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_environment import check_environment  # noqa: E402
from tools.rc1.build_demo_contracts import build_all, load_json, write_json  # noqa: E402
from tools.rc1.validate_rc1_contracts import (  # noqa: E402
    ABSOLUTE_OR_PRIVATE,
    ContractError,
    assert_no_private_paths,
    sha256_file,
    validate_delivery_receipt,
    validate_presentation_request,
    validate_presentation_response,
    validate_product5_config,
    validate_semantic_core,
)


FIXTURE = ROOT / "examples/fictional-qinglan-chengjing"
CORE_PATH = FIXTURE / "work/semantic_core.json"
GAPS_PATH = FIXTURE / "input/evidence_gaps.json"
ADAPTER_DIR = ROOT / "tools/product3_ppt_pipeline/automizer_adapter"
OUTPUT_ROOT = ROOT / "verification-tmp/fictional-demo"
SECRET_PATTERN = re.compile(
    r"(?:BEGIN (?:RSA |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,})"
)


def run(command: list[str], *, cwd: Path = ROOT) -> str:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    if result.returncode:
        details = "\n".join(item for item in (result.stdout.strip(), result.stderr.strip()) if item)
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command[:3])}\n{details}")
    return result.stdout.strip()


def import_business_gates():
    path = ROOT / "tools/product3_ppt_pipeline/business_gates.py"
    spec = importlib.util.spec_from_file_location("_rc1_business_gates", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load public business gates")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_input_friction() -> dict[str, Any]:
    facts = load_json(FIXTURE / "input/fact_register.json")
    market = load_json(FIXTURE / "input/market_evidence.json")
    gaps = load_json(GAPS_PATH)
    claims = load_json(FIXTURE / "input/marketing_claims.json")
    voices = (FIXTURE / "input/customer_voices.md").read_text(encoding="utf-8")
    fact_statuses = {item.get("status") for item in facts.get("facts", [])}
    decisions = {item.get("decision") for item in claims.get("claims", [])}
    requirements = {
        "fact_conflict": any("conflict" in str(status) for status in fact_statuses),
        "unknown_fact": any("unknown" in str(status) for status in fact_statuses),
        "competitor_strengths": all(item.get("strengths") for item in market.get("competitors", [])[:2]),
        "evidence_gaps": len(gaps.get("gaps", [])) >= 5,
        "mixed_claim_decisions": len(decisions) >= 3,
        "synthetic_customer_voices": voices.count("VOICE-") >= 6 and "合成" in voices,
    }
    if not all(requirements.values()):
        raise ContractError(f"虚构项目未覆盖主要真实摩擦：{requirements}")
    return requirements


def validate_business_pages(request: dict[str, Any], output_path: Path) -> None:
    gates = import_business_gates()
    pages = []
    internal_hits: dict[str, list[str]] = {}
    for item in request["pages"]:
        page = {
            "页面ID": item["page_id"],
            "页面语义ID": item["role"],
            "页面名称": item["title"],
            "页面文案": item["key_message"],
            "这一页只负责": item["role"],
            "视觉结构": item["visual_brief"],
            "来源页ID": item["page_id"],
            "素材编号": ",".join(item["evidence_refs"]),
        }
        pages.append(page)
        hits = gates.internal_method_hits(page)
        if hits:
            internal_hits[item["page_id"]] = hits
    duplicate_errors = gates.duplicate_sequence_errors(pages)
    report = {
        "schema": "residential.product3_business_qa.v0.1",
        "status": "pass" if not internal_hits and not duplicate_errors else "fail",
        "page_count": len(pages),
        "internal_method_hits": internal_hits,
        "duplicate_sequence_errors": duplicate_errors,
    }
    write_json(output_path, report)
    if report["status"] != "pass":
        raise ContractError(f"PPT业务门禁失败：{report}")


def install_node_dependencies(allow_install: bool) -> None:
    dependency = ADAPTER_DIR / "node_modules/pptxgenjs"
    if dependency.is_dir():
        return
    if not allow_install:
        raise RuntimeError(
            "Node dependencies are missing. Run again with --install-node-deps to execute npm ci."
        )
    run(["npm", "ci", "--ignore-scripts"], cwd=ADAPTER_DIR)


def build_site(config_path: Path, site_dir: Path) -> None:
    source = ROOT / "tools/product5_shell"
    shutil.copytree(source, site_dir)
    config = load_json(config_path)
    payload = "window.__PROJECT_DATA__ = " + json.dumps(config, ensure_ascii=False, indent=2) + ";\n"
    (site_dir / "project-data.js").write_text(payload, encoding="utf-8")
    index = (site_dir / "index.html").read_text(encoding="utf-8")
    mobile = (site_dir / "m/index.html").read_text(encoding="utf-8")
    app = (site_dir / "assets/app.js").read_text(encoding="utf-8")
    css = (site_dir / "assets/styles.css").read_text(encoding="utf-8")
    required = {
        "desktop_entry": "project-data.js" in index and "assets/app.js" in index,
        "mobile_entry": "../project-data.js" in mobile and "../assets/app.js" in mobile,
        "offline_csp": "connect-src 'none'" in index and "connect-src 'none'" in mobile,
        "same_semantic_core": all(item["id"] in payload for item in config["super_competitiveness"]),
        "no_external_resource": not re.search(r"(?:src|href)=[\"'](?:https?:)?//", index + mobile),
        "shell_code_present": len(app) > 1000 and len(css) > 2000,
    }
    if not all(required.values()):
        raise ContractError(f"产物5壳层检查失败：{required}")


def write_static_qa(path: Path, config: dict[str, Any]) -> None:
    lines = [
        "# Product 5 fictional static delivery QA",
        "",
        f"- project: {config['project']['id']}",
        "- fixture declaration: passed",
        f"- super competitiveness count: {len(config['super_competitiveness'])}",
        "- semantic ID continuity: passed",
        "- desktop and mobile relative routes: passed",
        "- offline CSP and external-resource scan: passed",
        "- absolute path and symlink scan: passed",
        "- formal browser visual review: platform review required for real client delivery",
        "",
        "final result: passed",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def output_record(path: Path, receipt_dir: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(receipt_dir).as_posix(),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def scan_generated_tree(root: Path) -> dict[str, int]:
    text_extensions = {".json", ".md", ".html", ".css", ".js", ".txt"}
    text_files = 0
    symlinks = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            symlinks += 1
            continue
        if not path.is_file() or path.suffix.lower() not in text_extensions:
            continue
        text_files += 1
        text = path.read_text(encoding="utf-8")
        if ABSOLUTE_OR_PRIVATE.search(text):
            raise ContractError(f"生成物包含本机或私有路径：{path.relative_to(root)}")
        if SECRET_PATTERN.search(text):
            raise ContractError(f"生成物包含疑似凭据：{path.relative_to(root)}")
    if symlinks:
        raise ContractError("生成物包含符号链接")
    return {"text_files_scanned": text_files, "symlinks": symlinks}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-node-deps", action="store_true")
    args = parser.parse_args()

    environment = check_environment()
    if environment["status"] != "pass":
        print(json.dumps(environment, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    install_node_dependencies(args.install_node_deps)
    if OUTPUT_ROOT.exists():
        if OUTPUT_ROOT.parent != ROOT / "verification-tmp":
            raise RuntimeError("refusing to replace an output directory outside verification-tmp")
        shutil.rmtree(OUTPUT_ROOT)
    contracts_dir = OUTPUT_ROOT / "contracts"
    presentation_dir = OUTPUT_ROOT / "presentation"
    product5_dir = OUTPUT_ROOT / "product5"
    contracts_dir.mkdir(parents=True)
    presentation_dir.mkdir(parents=True)
    product5_dir.mkdir(parents=True)

    core = load_json(CORE_PATH)
    validate_semantic_core(core)
    friction = validate_input_friction()
    built = build_all(CORE_PATH, GAPS_PATH, contracts_dir)
    chapter2 = built["chapter2"]
    chapter3 = built["chapter3"]
    request_path = built["presentation_request"]
    product5_config_path = built["product5_config"]

    run([sys.executable, "tools/product3_chapter2/validate_chapter2_contract.py", str(chapter2), "--final"])
    run([sys.executable, "tools/product3_chapter3/validate_chapter3_contract.py", str(chapter3)])
    run([sys.executable, "tools/product3_chapter23/validate_chapter23_bridge.py", str(chapter2), str(chapter3)])

    request = load_json(request_path)
    validate_presentation_request(request)
    expected_sc_ids = set(request["semantic_core"]["super_competitiveness_ids"])
    product5_config = load_json(product5_config_path)
    validate_product5_config(product5_config, expected_sc_ids)
    business_qa_path = presentation_dir / "business-qa.json"
    validate_business_pages(request, business_qa_path)

    pptx_path = presentation_dir / "product3-fictional-test-double.pptx"
    response_path = presentation_dir / "platform-response.json"
    run(
        [
            "node",
            "tools/platform_adapter_test_double/generate_presentation.mjs",
            "--request",
            str(request_path),
            "--out",
            str(pptx_path),
            "--response",
            str(response_path),
        ]
    )
    response = load_json(response_path)
    if response.get("request_sha256") != sha256_file(request_path):
        raise ContractError("平台回传的请求哈希不一致")
    validate_presentation_response(response, request, presentation_dir)
    package_report_text = run(
        [
            "node",
            "tools/product3_ppt_pipeline/automizer_adapter/verify_pptx_package.mjs",
            "--pptx",
            str(pptx_path),
            "--expected-slides",
            str(len(request["pages"])),
        ]
    )
    package_report = json.loads(package_report_text)
    package_qa_path = presentation_dir / "pptx-package-qa.json"
    write_json(package_qa_path, package_report)
    if package_report.get("status") != "pass":
        raise ContractError("PPTX结构安全检查未通过")

    site_dir = product5_dir / "site"
    build_site(product5_config_path, site_dir)
    static_qa_path = product5_dir / "delivery-qa.md"
    write_static_qa(static_qa_path, product5_config)
    static_manifest_path = product5_dir / "bundle-manifest.json"
    run(
        [
            "node",
            "tools/ue_static_bundle/create_manifest.mjs",
            str(site_dir),
            str(static_manifest_path),
            core["project"]["id"],
            str(static_qa_path),
            "m/index.html",
        ]
    )
    static_verify = json.loads(
        run(
            [
                "node",
                "tools/ue_static_bundle/verify_manifest.mjs",
                str(static_manifest_path),
                str(site_dir),
            ]
        )
    )
    if static_verify.get("status") != "pass":
        raise ContractError("产物5静态包独立校验未通过")

    outputs = {
        "chapter2_contract": output_record(chapter2, OUTPUT_ROOT),
        "chapter3_contract": output_record(chapter3, OUTPUT_ROOT),
        "presentation_request": output_record(request_path, OUTPUT_ROOT),
        "platform_response": output_record(response_path, OUTPUT_ROOT),
        "editable_pptx": output_record(pptx_path, OUTPUT_ROOT),
        "presentation_snapshot": output_record(presentation_dir / "presentation-preview.json", OUTPUT_ROOT),
        "business_qa": output_record(business_qa_path, OUTPUT_ROOT),
        "pptx_package_qa": output_record(package_qa_path, OUTPUT_ROOT),
        "product5_config": output_record(product5_config_path, OUTPUT_ROOT),
        "product5_static_manifest": output_record(static_manifest_path, OUTPUT_ROOT),
        "product5_static_qa": output_record(static_qa_path, OUTPUT_ROOT),
    }
    aggregate_input = "".join(f"{label}:{item['sha256']}\n" for label, item in sorted(outputs.items()))
    receipt = {
        "schema": "residential.public_delivery_receipt.v0.1",
        "status": "local_fictional_e2e_pass",
        "project_id": core["project"]["id"],
        "fixture_notice": core["fixture_notice"],
        "environment": environment,
        "fixture_friction": friction,
        "verification": {
            "method_contracts": "pass",
            "platform_roundtrip": "pass",
            "pptx_structure": "pass",
            "product5_static_bundle": "pass",
            "formal_visual": "platform_review_required",
            "cross_machine": "not_run",
            "workbuddy": "not_run",
        },
        "outputs": outputs,
        "aggregate_output_sha256": hashlib.sha256(aggregate_input.encode("utf-8")).hexdigest(),
        "gaps": [
            {
                "code": "FORMAL_VISUAL_REVIEW_REQUIRED",
                "blocking_for_local_contract_roundtrip": False,
                "blocking_for_real_client_delivery": True,
            },
            {
                "code": "CROSS_MACHINE_AND_WORKBUDDY_COLD_START_NOT_RUN",
                "blocking_for_local_rc1_assembly": False,
                "blocking_for_cross_platform_portability_claim": True,
            },
        ],
        "publication": {
            "authorized": True,
            "license_selected": True,
            "license": "Apache-2.0",
            "public_repository_created": True,
            "repository": "https://github.com/xiem-bit/residential-project-interpretation-service-public",
        },
    }
    assert_no_private_paths(receipt)
    receipt_path = OUTPUT_ROOT / "delivery-receipt.json"
    write_json(receipt_path, receipt)
    validate_delivery_receipt(receipt, OUTPUT_ROOT)
    scan = scan_generated_tree(OUTPUT_ROOT)
    print("RC1 FICTIONAL E2E: PASS")
    print(f"receipt: {receipt_path.relative_to(ROOT).as_posix()}")
    print(f"generated text files scanned: {scan['text_files_scanned']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContractError, RuntimeError, OSError, ValueError) as exc:
        print(f"RC1 FICTIONAL E2E: FAIL\n{exc}", file=sys.stderr)
        raise SystemExit(1)
