#!/usr/bin/env python3
"""汇总产物3下半程技术夹具回执，不把技术验证冒充真实项目验收。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    stage = args.stage_dir.resolve()
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    def add_json_check(name: str, relative: str, predicate, evidence) -> None:
        path = stage / relative
        if not path.exists():
            errors.append(f"{name}缺少回执：{path}")
            checks.append({"name": name, "status": "fail", "receipt": str(path)})
            return
        payload = load_json(path)
        passed = bool(predicate(payload))
        checks.append(
            {
                "name": name,
                "status": "pass" if passed else "fail",
                "receipt": str(path),
                "evidence": evidence(payload),
            }
        )
        if not passed:
            errors.append(f"{name}回执未达到技术夹具通过条件")

    add_json_check(
        "single_source_create",
        "qj/qa/production_receipt.json",
        lambda p: p.get("result") == "pass" and p.get("technical_fixture_passed") is True,
        lambda p: {"page_count": p.get("page_count"), "visual_drift": p.get("visual_drift")},
    )
    add_json_check(
        "targeted_patch",
        "qj/patch/qa/patch_receipt.json",
        lambda p: p.get("status") == "pass" and p.get("unaffected_pages_unchanged") is True,
        lambda p: {
            "changed_pages": p.get("changed_pages"),
            "moved_pages": p.get("moved_pages"),
            "unaffected_page_count": p.get("unaffected_page_count"),
        },
    )
    add_json_check(
        "structure_change",
        "qj/structure/qa/production_receipt.json",
        lambda p: p.get("result") == "pass" and p.get("technical_fixture_passed") is True,
        lambda p: {"page_count": p.get("page_count"), "visual_drift": p.get("visual_drift")},
    )
    add_json_check(
        "external_parent_refresh_equivalent",
        "qj/external-refresh/qa/external_parent_diff_receipt.json",
        lambda p: str(p.get("status") or "").startswith("pass") and not p.get("errors"),
        lambda p: {
            "changed_pages": p.get("changed_pages"),
            "moved_pages": p.get("moved_pages"),
            "unchanged_page_count": p.get("unchanged_page_count"),
            "note": "等价外部父版技术夹具，不等于真人WPS或PowerPoint实测",
        },
    )
    add_json_check(
        "multisource_starter_adapter",
        "multisource/qa/automizer/automizer_starter_receipt.json",
        lambda p: p.get("status") == "pass" and p.get("slide_count") == 3,
        lambda p: {
            "adapter": p.get("adapter"),
            "adapter_version": p.get("adapter_version"),
            "slide_count": p.get("slide_count"),
            "source_count": len(p.get("source_deck_sha256s") or {}),
        },
    )
    add_json_check(
        "multisource_presentations_qa",
        "multisource/qa/production_receipt.json",
        lambda p: p.get("result") == "pass"
        and p.get("technical_fixture_passed") is True
        and all(float(item.get("rms") or 0) == 0 for item in p.get("visual_drift") or []),
        lambda p: {"page_count": p.get("page_count"), "visual_drift": p.get("visual_drift")},
    )

    slides_test_path = stage / "multisource/qa/slides_test.txt"
    slides_test_passed = slides_test_path.exists() and "Test passed" in slides_test_path.read_text(encoding="utf-8")
    checks.append(
        {
            "name": "multisource_overflow_check",
            "status": "pass" if slides_test_passed else "fail",
            "receipt": str(slides_test_path),
        }
    )
    if not slides_test_passed:
        errors.append("多来源输出未通过画布溢出检查")

    result = {
        "schema": "product3.technical_fixture_matrix.v0.1",
        "status": "technical_fixture_matrix_passed" if not errors else "fail",
        "formal_project_status": "not_assessed_by_fixture_matrix",
        "scope": "非生产技术夹具；不生产第一章和第四章",
        "checks": checks,
        "remaining_formal_gates": [
            "真实项目状态需读取独立production_receipt与真人审阅结论",
            "真实项目页面语义重组与内容装载",
            "真人实际在WPS或PowerPoint改稿后的接续",
            "拆分或合并页面的真实操作",
            "整套真人终审",
        ],
        "errors": errors,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS" if not errors else "FAIL")
    print(args.out)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
