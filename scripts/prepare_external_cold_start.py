#!/usr/bin/env python3
"""Prepare a deterministic handoff workspace for an external Agent platform."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_environment import check_environment  # noqa: E402
from scripts.run_rc1_demo import (  # noqa: E402
    CORE_PATH,
    FIXTURE,
    GAPS_PATH,
    build_site,
    run,
    validate_business_pages,
    validate_input_friction,
    write_static_qa,
)
from tools.rc1.build_demo_contracts import build_all, load_json, write_json  # noqa: E402
from tools.rc1.validate_rc1_contracts import (  # noqa: E402
    ContractError,
    assert_no_private_paths,
    sha256_file,
    validate_presentation_request,
    validate_product5_config,
    validate_semantic_core,
)


WORKSPACE = ROOT / "verification-tmp/external-cold-start"


def main() -> int:
    environment = check_environment()
    if environment["status"] != "pass":
        raise ContractError("标准Python/Node环境检查未通过")
    if WORKSPACE.exists():
        if WORKSPACE.parent != ROOT / "verification-tmp":
            raise ContractError("拒绝覆盖verification-tmp以外的目录")
        shutil.rmtree(WORKSPACE)

    contracts_dir = WORKSPACE / "contracts"
    presentation_dir = WORKSPACE / "presentation"
    product5_dir = WORKSPACE / "product5"
    presentation_dir.mkdir(parents=True)
    product5_dir.mkdir(parents=True)
    (presentation_dir / "previews").mkdir()
    (product5_dir / "previews").mkdir()

    core = load_json(CORE_PATH)
    validate_semantic_core(core)
    friction = validate_input_friction()
    outputs = build_all(CORE_PATH, GAPS_PATH, contracts_dir)
    run([sys.executable, "tools/product3_chapter2/validate_chapter2_contract.py", str(outputs["chapter2"]), "--final"])
    run([sys.executable, "tools/product3_chapter3/validate_chapter3_contract.py", str(outputs["chapter3"])])
    run([sys.executable, "tools/product3_chapter23/validate_chapter23_bridge.py", str(outputs["chapter2"]), str(outputs["chapter3"])])

    request = load_json(outputs["presentation_request"])
    validate_presentation_request(request)
    sc_ids = set(request["semantic_core"]["super_competitiveness_ids"])
    product5_config = load_json(outputs["product5_config"])
    validate_product5_config(product5_config, sc_ids)
    validate_business_pages(request, presentation_dir / "business-qa.json")

    site_dir = product5_dir / "site"
    build_site(outputs["product5_config"], site_dir)
    static_qa = product5_dir / "delivery-qa.md"
    write_static_qa(static_qa, product5_config)
    static_manifest = product5_dir / "bundle-manifest.json"
    run(
        [
            "node",
            "tools/ue_static_bundle/create_manifest.mjs",
            str(site_dir),
            str(static_manifest),
            core["project"]["id"],
            str(static_qa),
            "m/index.html",
        ]
    )
    run(["node", "tools/ue_static_bundle/verify_manifest.mjs", str(static_manifest), str(site_dir)])

    shutil.copy2(ROOT / "cold-start/observation.template.json", WORKSPACE / "cold-start-observation.json")
    shutil.copy2(
        ROOT / "cold-start/presentation-visual-review.template.json",
        presentation_dir / "presentation-visual-review.json",
    )
    shutil.copy2(
        ROOT / "cold-start/product5-visual-review.template.json",
        product5_dir / "product5-visual-review.json",
    )

    handoff = {
        "schema": "residential.external_platform_handoff.v0.1",
        "status": "awaiting_workbuddy_platform_adapter",
        "project_id": core["project"]["id"],
        "fixture_notice": core["fixture_notice"],
        "source_repository": "https://github.com/xiem-bit/residential-project-interpretation-service-public",
        "source_tag": "v0.1.0-rc.1",
        "presentation_request": "contracts/presentation-request.json",
        "presentation_request_sha256": sha256_file(outputs["presentation_request"]),
        "expected_page_ids": [item["page_id"] for item in request["pages"]],
        "expected_super_competitiveness_ids": sorted(sc_ids),
        "required_platform_response": "presentation/platform-response.json",
        "required_presentation_visual_review": "presentation/presentation-visual-review.json",
        "required_product5_visual_review": "product5/product5-visual-review.json",
        "required_observation": "cold-start-observation.json",
        "fixture_friction": friction,
        "local_reference_test_double_is_external_pass": False,
    }
    assert_no_private_paths(handoff)
    write_json(WORKSPACE / "handoff.json", handoff)
    print("EXTERNAL COLD START HANDOFF: READY")
    print("workspace: verification-tmp/external-cold-start")
    print("next: WorkBuddy must produce platform-response.json, PPTX, previews and visual-review evidence")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContractError, RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"EXTERNAL COLD START HANDOFF: FAIL\n{exc}", file=sys.stderr)
        raise SystemExit(1)
