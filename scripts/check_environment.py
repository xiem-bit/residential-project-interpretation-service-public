#!/usr/bin/env python3
"""Doctor for the public residential production package and optional carriers."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRODUCT5_ROOT = ROOT / "tools" / "product5_shell"
PRODUCT3_GOLD_ROOT = ROOT / "examples" / "gold-product3-public-safe"
PRODUCT3_AUTHORITY = PRODUCT3_GOLD_ROOT / "gold-authority.json"
AUTHORIZED_ASSET_MANIFEST = ROOT / "references" / "authorized-reference-assets.json"


def _version(command: str) -> str | None:
    executable = shutil.which(command)
    if not executable:
        return None
    result = subprocess.run([executable, "--version"], check=False, capture_output=True, text=True)
    return (result.stdout or result.stderr).strip() or None


def _major(value: str | None) -> int | None:
    if not value:
        return None
    digits = "".join(character if character.isdigit() else " " for character in value).split()
    return int(digits[0]) if digits else None


def _check(status: str, detail: str, action: str = "") -> dict[str, str]:
    return {"status": status, "detail": detail, "action": action}


def _run(name: str, command: list[str], cwd: Path = ROOT) -> tuple[str, dict[str, str]]:
    completed = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    output = (completed.stdout + completed.stderr).strip()
    if completed.returncode == 0:
        return name, _check("pass", output.splitlines()[-1] if output else "command completed")
    return name, _check("fail", output[-1200:] or f"exit code {completed.returncode}", "按输出修复后重新运行doctor")


def _core_file_check() -> dict[str, str]:
    required = [
        "AGENTS.md",
        "START_HERE.md",
        "AGENT_RULES.md",
        "RELEASE_STATUS.md",
        "CAPABILITY_PARITY_CONTRACT.md",
        "CAPABILITY_PARITY_MANIFEST.json",
        "PRODUCTION_PATH_MANIFEST.json",
        "references/production-reference-index.json",
        "workflows/residential-production-orchestrator/SKILL.md",
        "scripts/init_production_run.py",
        "scripts/verify_production_run.py",
    ]
    missing = [relative for relative in required if not (ROOT / relative).is_file()]
    if missing:
        return _check("fail", "missing: " + ", ".join(missing), "重新取得完整发行包")
    try:
        for relative in (
            "CAPABILITY_PARITY_MANIFEST.json",
            "PRODUCTION_PATH_MANIFEST.json",
            "references/production-reference-index.json",
        ):
            json.loads((ROOT / relative).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _check("fail", f"invalid JSON: {exc}", "重新取得完整发行包或恢复被改坏的清单")
    return _check("pass", f"{len(required)} required entrypoints present and key JSON parsed")


def _product3_check() -> dict[str, str]:
    try:
        authority = json.loads(PRODUCT3_AUTHORITY.read_text(encoding="utf-8"))
        gold = PRODUCT3_GOLD_ROOT / authority["authority_file"]
        inspect = gold.with_suffix(gold.suffix + ".inspect.ndjson")
        expected_slides = int(authority["slide_count"])
        expected_notes = int(authority["notes_sources_count"])
        expected_sha256 = authority["authority_sha256"]
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return _check("fail", f"Product 3 gold authority is invalid: {exc}", "恢复发行包中的gold-authority.json")
    if not gold.is_file() or not inspect.is_file():
        return _check("fail", "Product 3 gold deck or inspect record is missing", "重新取得包含公开安全黄金参考的完整发行包")
    if not zipfile.is_zipfile(gold):
        return _check("fail", "Product 3 gold deck is not a valid PPTX package", "恢复发行包中的黄金PPTX")
    actual_sha256 = hashlib.sha256(gold.read_bytes()).hexdigest()
    if actual_sha256 != expected_sha256:
        return _check("fail", "Product 3 gold deck hash does not match its authority", "恢复未经改动的黄金PPTX")
    with zipfile.ZipFile(gold) as archive:
        slide_names = {
            name
            for name in archive.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml") and "/_rels/" not in name
        }
        note_names = {
            name
            for name in archive.namelist()
            if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml") and "/_rels/" not in name
        }
    try:
        inspect_records = [json.loads(line) for line in inspect.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        return _check("fail", f"Product 3 inspect record is invalid: {exc}", "恢复黄金参考的inspect记录")
    inspect_slides = sum(record.get("kind") == "slide" for record in inspect_records)
    inspect_notes = sum(record.get("kind") == "notes" for record in inspect_records)
    if (
        len(slide_names) != expected_slides
        or len(note_names) != expected_notes
        or inspect_slides != expected_slides
        or inspect_notes != expected_notes
    ):
        return _check(
            "fail",
            "Product 3 gold reference incomplete: "
            f"slides={len(slide_names)}, notes={len(note_names)}, "
            f"inspect_slides={inspect_slides}, inspect_notes={inspect_notes}",
            f"恢复{expected_slides}页授权公开黄金参考、逐页备注与检查记录",
        )
    try:
        assets = json.loads(AUTHORIZED_ASSET_MANIFEST.read_text(encoding="utf-8"))
        page_library = ROOT / assets["page_template_library"]["path"]
        case_library = ROOT / assets["case_asset_library"]["path"]
        writing_library = ROOT / assets["writing_library"]["path"]
        page_files = sum(path.is_file() for path in page_library.rglob("*"))
        case_files = sum(path.is_file() for path in case_library.rglob("*"))
        source_decks = list((page_library / "source_decks").glob("*.pptx"))
        required_writing = (
            ROOT / "workflows/chinese-research-report-editor/SKILL.md",
            ROOT / "workflows/chinese-affirmative-business-editor/SKILL.md",
            writing_library / "16-断言式书写规范_v1.0.md",
            writing_library / "human-revision-style-samples.json",
        )
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return _check("fail", f"authorized Product 3 assets are invalid: {exc}", "恢复授权参考资产清单")
    expected_pages = int(assets["page_template_library"]["file_count"])
    expected_cases = int(assets["case_asset_library"]["file_count"])
    expected_decks = int(assets["page_template_library"]["source_deck_count"])
    if page_files != expected_pages or case_files != expected_cases or len(source_decks) != expected_decks:
        return _check(
            "fail",
            f"authorized Product 3 assets incomplete: page_files={page_files}, case_files={case_files}, source_decks={len(source_decks)}",
            "重新取得包含页面模板、案例图和三份历史原稿的完整发行包",
        )
    missing_writing = [str(path.relative_to(ROOT)) for path in required_writing if not path.is_file()]
    if missing_writing:
        return _check("fail", "writing capability incomplete: " + ", ".join(missing_writing), "恢复中文写作与断言写作能力")
    return _check(
        "pass",
        f"editable gold: {len(slide_names)} slides; authorized assets: {page_files} page files, {case_files} case files, {len(source_decks)} source decks; writing skills present",
    )


def _product5_source_check() -> dict[str, str]:
    required = [
        "package.json",
        "package-lock.json",
        "src/App.jsx",
        "src/data.js",
        "src/styles.css",
        "public/project-data.js",
        "tests/gold-implementation.test.mjs",
    ]
    missing = [relative for relative in required if not (PRODUCT5_ROOT / relative).is_file()]
    if missing:
        return _check("fail", "missing Product 5 source: " + ", ".join(missing), "重新取得完整发行包")
    return _check("pass", f"{len(required)} Product 5 runtime files present")


def _install_product5_dependencies() -> tuple[str, dict[str, str]]:
    if not shutil.which("npm"):
        return "product5_dependencies", _check("fail", "npm is missing", "安装Node.js 20+和npm")
    return _run("product5_dependencies", ["npm", "ci", "--ignore-scripts"], cwd=PRODUCT5_ROOT)


def check_environment(
    profile: str = "legacy-rc1",
    *,
    run_tests: bool = False,
    install_node_dependencies: bool = False,
) -> dict[str, Any]:
    checks: dict[str, dict[str, str]] = {}
    python_version = ".".join(str(item) for item in sys.version_info[:3])
    checks["python"] = _check(
        "pass" if sys.version_info >= (3, 9) else "fail",
        f"{python_version}; minimum 3.9",
        "安装Python 3.9或更高版本" if sys.version_info < (3, 9) else "",
    )
    checks["package_entrypoints"] = _core_file_check()

    needs_product3 = profile in {"product3", "full"}
    needs_product5 = profile in {"product5", "full", "legacy-rc1"}
    if needs_product3:
        checks["product3_gold_reference"] = _product3_check()
    if needs_product5:
        node_version = _version("node")
        npm_version = _version("npm")
        checks["node"] = _check(
            "pass" if (_major(node_version) or 0) >= 20 else "fail",
            f"{node_version or 'missing'}; minimum 20",
            "安装Node.js 20或更高版本" if (_major(node_version) or 0) < 20 else "",
        )
        checks["npm"] = _check("pass" if npm_version else "fail", npm_version or "missing", "安装npm" if not npm_version else "")
        checks["product5_source"] = _product5_source_check()
        if profile == "legacy-rc1":
            pass
        elif install_node_dependencies and checks["node"]["status"] == checks["npm"]["status"] == "pass":
            name, result = _install_product5_dependencies()
            checks[name] = result
        elif not (PRODUCT5_ROOT / "node_modules" / "vite").is_dir():
            checks["product5_dependencies"] = _check(
                "fail",
                "Product 5 dependencies are not installed",
                "重新运行并增加 --install-node-deps，或在tools/product5_shell执行npm ci --ignore-scripts",
            )
        else:
            checks["product5_dependencies"] = _check("pass", "Product 5 dependencies are present")

    if run_tests:
        for name, command, cwd in (
            ("public_tests", [sys.executable, "tests/run_public_tests.py"], ROOT),
            ("capability_parity", [sys.executable, "scripts/verify_capability_parity.py"], ROOT),
            ("release_manifest", [sys.executable, "scripts/build_release_manifest.py", "--check"], ROOT),
        ):
            check_name, result = _run(name, command, cwd)
            checks[check_name] = result
        if profile in {"product5", "full"} and checks.get("product5_dependencies", {}).get("status") == "pass":
            check_name, result = _run("product5_runtime_tests", ["npm", "test"], PRODUCT5_ROOT)
            checks[check_name] = result

    failures = [name for name, result in checks.items() if result["status"] == "fail"]
    gaps = [
        {"code": f"INSTALL-{name.upper().replace('-', '_')}", "scope": name, "action": checks[name]["action"]}
        for name in failures
    ]
    return {
        "schema": "residential.public_installation_doctor.v1",
        "profile": profile,
        "status": "pass" if not failures else "fail",
        "checks": checks,
        "gaps": gaps,
        "manual_boundaries": {
            "codex_workspace": "打开仓库根目录后由AGENTS.md和现行Skill路由；脚本不证明Agent已理解业务",
            "product3_generation": "黄金PPTX、历史原稿、模板与案例资产随包；演示文稿引擎由终端用户自行安装并现场确认",
            "grist_console": "本机Grist装配控制台不随包迁移；需要可视装配时由终端用户自行安装Grist",
            "external_channels": "Computer Use、浏览器、地图、微信、小红书等平台能力及账号登录态不随包迁移；由终端用户自行安装或登录",
            "human_business_acceptance": "机器doctor通过不代表真人业务接受、发布或业务效果",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--profile",
        choices=["production-core", "product3", "product5", "full", "legacy-rc1"],
        default="production-core",
    )
    parser.add_argument("--run-tests", action="store_true", help="run the package-level regression checks")
    parser.add_argument("--install-node-deps", action="store_true", help="run npm ci for the Product 5 adapter")
    args = parser.parse_args()
    report = check_environment(
        args.profile,
        run_tests=args.run_tests,
        install_node_dependencies=args.install_node_deps,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for name, item in report["checks"].items():
            print(f"{name}: {item['status']} - {item['detail']}")
            if item["action"]:
                print(f"  action: {item['action']}")
        print(f"doctor: {report['status']}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
