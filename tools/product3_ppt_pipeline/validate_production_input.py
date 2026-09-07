#!/usr/bin/env python3
"""验证已裁定装配清单能否进入产物3正式PPT生产。"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from zipfile import ZipFile

from business_gates import (
    duplicate_sequence_errors,
    internal_method_hits,
    is_audience_portrait,
    page_business_query,
    rank_portrait_assets,
    required_portrait_count,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "tools/shared_datasets"))
from build_case_asset_inventory import load_current_inventory
DEFAULT_SEMANTICS = PROJECT_ROOT / "references/product3/assets/产物3页面模板库/datasets/page_semantic_dataset.v0.3.json"
DEFAULT_SOURCES = PROJECT_ROOT / "references/product3/assets/产物3页面模板库/datasets/source_page_semantic_annotations.v0.3.json"
DEFAULT_ASSETS = PROJECT_ROOT / "references/product3/assets/产物3案例截图素材库/case_asset_inventory.json"
SHARED_ASSET_ROOT = PROJECT_ROOT / "references/product3/assets/产物3案例截图素材库/original"
SOURCE_ID_RE = re.compile(r"(?:QJ|B10|GT)-\d{2}")
ASSET_ID_RE = re.compile(r"CASE-[A-Z0-9-]+", re.IGNORECASE)
PLACEHOLDER_MARKERS = ("待补", "待选", "待Codex", "TBD", "TODO")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_source_ids(value: Any) -> list[str]:
    return list(dict.fromkeys(SOURCE_ID_RE.findall(str(value or ""))))


def parse_asset_bindings(value: Any) -> tuple[list[str], str | None]:
    if value is None or value == "":
        return [], None
    if isinstance(value, list):
        values = value[1:] if value and value[0] == "L" else value
        return list(dict.fromkeys(str(item) for item in values if item)), None
    raw = str(value).strip()
    if not raw:
        return [], None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        ids = ASSET_ID_RE.findall(raw)
        return list(dict.fromkeys(item.upper() for item in ids)), None if ids else "素材编号格式无法解析"
    if isinstance(parsed, dict):
        main = parsed.get("main") or parsed.get("主图") or ""
        proof = parsed.get("proof") or parsed.get("proofs") or parsed.get("证明图") or []
        if not isinstance(proof, list):
            proof = [proof]
        ids = [str(main)] if main else []
        ids.extend(str(item) for item in proof if item)
        return list(dict.fromkeys(ids)), None
    if isinstance(parsed, list):
        return list(dict.fromkeys(str(item) for item in parsed if item)), None
    return [], "素材编号JSON必须是对象或数组"


def contains_placeholder(value: Any) -> bool:
    text = str(value or "")
    return any(marker.lower() in text.lower() for marker in PLACEHOLDER_MARKERS)


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def source_slide_text(deck_path: Path, slide_number: int) -> str:
    if slide_number <= 0:
        return ""
    member = f"ppt/slides/slide{slide_number}.xml"
    with ZipFile(deck_path, "r") as archive:
        if member not in archive.namelist():
            return ""
        root = ElementTree.fromstring(archive.read(member))
    return " ".join(
        node.text.strip()
        for node in root.iter()
        if node.tag.endswith("}t") and node.text and node.text.strip()
    )


def normalized_copy(value: Any) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", str(value or "")).lower()


def source_copy_overlap(current_copy: str, historical_copy: str) -> tuple[float, int]:
    current = normalized_copy(current_copy)
    historical = normalized_copy(historical_copy)
    if len(current) < 40 or len(historical) < 40:
        return 0.0, 0
    matcher = difflib.SequenceMatcher(None, current, historical, autojunk=False)
    longest = matcher.find_longest_match(0, len(current), 0, len(historical)).size
    return matcher.ratio(), longest


def validate_payload(
    payload: dict[str, Any],
    semantic_dataset: dict[str, Any],
    source_dataset: dict[str, Any],
    asset_inventory: list[dict[str, Any]],
    allow_test_fixture: bool,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    checked_decks: dict[str, dict[str, str]] = {}
    if payload.get("schema") != "product3.assembly_blueprint.v0.1":
        errors.append("schema不受支持")
    if payload.get("export_status") != "approved_for_ppt_production":
        errors.append("不是已裁定正式导出")
    if payload.get("fixture_only") and not allow_test_fixture:
        errors.append("技术夹具禁止进入正式生产；仅测试时显式使用--allow-test-fixture")

    semantics = {item.get("semanticId"): item for item in semantic_dataset.get("semantics", [])}
    variants = {item.get("visualVariantId"): item for item in semantic_dataset.get("visualVariants", [])}
    sources = {item.get("sourcePageId"): item for item in source_dataset.get("pages", [])}
    assets = {str(item.get("asset_id") or ""): item for item in asset_inventory}
    pages = payload.get("pages") or []
    asset_usage: dict[str, list[str]] = defaultdict(list)
    asset_hash_usage: dict[str, list[tuple[str, str]]] = defaultdict(list)
    family_asset_selection: list[dict[str, Any]] = []
    source_text_cache: dict[tuple[str, int], str] = {}

    if not pages or payload.get("page_count") != len(pages):
        errors.append("页面数量为空或与page_count不一致")
        return errors, {"blueprint_sha256": sha256_json(payload), "checked_decks": checked_decks}

    orders = [page.get("页序") for page in pages]
    expected_orders = list(range(1, len(pages) + 1))
    if orders != expected_orders:
        errors.append(f"有效页序必须连续且按1开始：实际={orders}")
    page_ids = [str(page.get("页面ID") or "").strip() for page in pages]
    if "" in page_ids or len(page_ids) != len(set(page_ids)):
        errors.append("页面ID为空或重复")

    for page in pages:
        page_id = str(page.get("页面ID") or f"第{page.get('页序', '?')}页")
        if page.get("裁定状态") != "approved":
            errors.append(f"{page_id}：未approved")
        if not bool(page.get("进入PPT生产")):
            errors.append(f"{page_id}：未勾选进入PPT生产")
        for label in ("页面名称", "这一页只负责", "演讲动作", "视觉结构", "页面语义ID"):
            if not str(page.get(label) or "").strip():
                errors.append(f"{page_id}：{label}为空")
            elif label in {"页面名称", "这一页只负责", "演讲动作", "视觉结构"} and contains_placeholder(page.get(label)):
                errors.append(f"{page_id}：{label}仍含待补占位语")
        visible_copy = str(page.get("页面文案") or "").strip()
        formal_business_gate = not (payload.get("fixture_only") and allow_test_fixture)
        if not visible_copy and formal_business_gate:
            errors.append(f"{page_id}：页面文案为空；历史来源页只提供结构，正式生产必须装载当前项目文案")
        elif contains_placeholder(visible_copy):
            errors.append(f"{page_id}：页面文案仍含待补占位语")
        method_hits = internal_method_hits(page) if formal_business_gate else []
        if method_hits:
            errors.append(
                f"{page_id}：客户可见标题／文案暴露内部推导方法（{'、'.join(method_hits)}）；"
                "改写为新的项目关系、客户获得或删除该页"
            )

        semantic_id = str(page.get("页面语义ID") or "")
        semantic = semantics.get(semantic_id)
        if not semantic:
            errors.append(f"{page_id}：页面语义ID不存在：{semantic_id}")

        variant_id = str(page.get("视觉变体ID") or "")
        if variant_id:
            variant = variants.get(variant_id)
            if not variant:
                errors.append(f"{page_id}：视觉变体ID不存在：{variant_id}")
            elif semantic_id not in variant.get("appliesToSemanticIds", []):
                errors.append(f"{page_id}：视觉变体{variant_id}不适用于{semantic_id}")
        if semantic_id == "P3-COMPETITION-MAP":
            if not variant_id:
                errors.append(f"{page_id}：竞争地图未选择视觉变体")
            if not str(page.get("视觉参考页ID") or "").strip():
                errors.append(f"{page_id}：竞争地图未选择视觉参考页")

        page_source_ids = parse_source_ids(page.get("来源页ID"))
        reference_ids = parse_source_ids(page.get("视觉参考页ID"))
        for source_id in dict.fromkeys(page_source_ids + reference_ids):
            source = sources.get(source_id)
            if not source:
                errors.append(f"{page_id}：来源页ID不存在：{source_id}")
                continue
            compatible_semantics = {
                str(source.get("primarySemanticId") or ""),
                *(str(item) for item in source.get("secondarySemanticIds", []) if item),
            }
            if semantic_id and semantic_id not in compatible_semantics:
                errors.append(
                    f"{page_id}：来源页{source_id}语义不兼容；"
                    f"页面={semantic_id}，来源主语义={source.get('primarySemanticId') or '空'}"
                )
            deck_value = str(source.get("sourceDeck") or "")
            deck_path = resolve_project_path(deck_value)
            if not deck_path.exists():
                errors.append(f"{page_id}：来源PPT不存在：{deck_value}")
                continue
            if deck_value not in checked_decks:
                actual_hash = sha256_file(deck_path)
                expected_hash = next(
                    (str(item.get("sha256") or "") for item in source_dataset.get("sourceDecks", []) if item.get("path") == deck_value),
                    "",
                )
                checked_decks[deck_value] = {"expected_sha256": expected_hash, "actual_sha256": actual_hash}
                if expected_hash and actual_hash != expected_hash:
                    errors.append(f"来源PPT哈希变化：{deck_value}")

            if visible_copy and formal_business_gate:
                cache_key = (deck_value, int(source.get("sourceSlide") or 0))
                if cache_key not in source_text_cache:
                    source_text_cache[cache_key] = source_slide_text(deck_path, cache_key[1])
                overlap, longest = source_copy_overlap(visible_copy, source_text_cache[cache_key])
                if overlap >= 0.55 or (longest >= 24 and longest / max(len(normalized_copy(visible_copy)), 1) >= 0.25):
                    errors.append(
                        f"{page_id}：页面文案与历史来源页{source_id}可见文字高度重合"
                        f"（相似度={overlap:.2f}，最长连续重合={longest}字）；只可复用结构，须重写当前项目文案"
                    )

        asset_ids, asset_error = parse_asset_bindings(page.get("素材编号"))
        if asset_error:
            errors.append(f"{page_id}：{asset_error}")
        for asset_id in asset_ids:
            asset = assets.get(asset_id)
            if not asset:
                errors.append(f"{page_id}：素材ID不存在：{asset_id}")
                continue
            asset_usage[asset_id].append(page_id)
            status = str(asset.get("status") or "")
            if "待用户复核" in status or "待复核" in status:
                errors.append(f"{page_id}：素材{asset_id}尚未完成真人复核")
            if not str(asset.get("effective_business_semantic") or "").strip():
                errors.append(f"{page_id}：素材{asset_id}缺少生效业务语义")
            original_name = Path(str(asset.get("original_asset") or "")).name
            shared_path = SHARED_ASSET_ROOT / original_name
            if not original_name or not shared_path.exists():
                errors.append(f"{page_id}：素材{asset_id}真实文件不存在：{shared_path}")
            else:
                asset_hash_usage[sha256_file(shared_path)].append((asset_id, page_id))

        portrait_count = required_portrait_count(page) if formal_business_gate else 0
        if portrait_count:
            bound_portraits = [
                asset_id
                for asset_id in asset_ids
                if asset_id in assets and is_audience_portrait(assets[asset_id])
            ]
            candidates = rank_portrait_assets(page, asset_inventory, limit=max(6, portrait_count * 2))
            family_asset_selection.append(
                {
                    "page_id": page_id,
                    "query": page_business_query(page),
                    "required_portraits": portrait_count,
                    "bound_portraits": bound_portraits,
                    "candidates": candidates,
                    "result": (
                        "bound"
                        if len(bound_portraits) >= portrait_count
                        else "reuse_candidates_available"
                        if len(candidates) >= portrait_count
                        else "generation_required"
                    ),
                }
            )
            if len(bound_portraits) < portrait_count:
                if len(candidates) >= portrait_count:
                    suggestions = "、".join(item["asset_id"] for item in candidates[:portrait_count])
                    errors.append(
                        f"{page_id}：客群／家庭页需要{portrait_count}张按业务语义匹配的肖像图，"
                        f"当前已绑定{len(bound_portraits)}张；共享库可复用候选为{suggestions}，先绑定后再生产"
                    )
                else:
                    errors.append(
                        f"{page_id}：客群／家庭页需要{portrait_count}张按业务语义匹配的肖像图，"
                        f"共享库当前只有{len(candidates)}张候选；先按缺口语义新生产、复核并登记CASE编号，禁止空槽进入PPT"
                    )

    if not (payload.get("fixture_only") and allow_test_fixture):
        errors.extend(duplicate_sequence_errors(pages))

    for asset_id, page_ids in sorted(asset_usage.items()):
        if len(page_ids) > 1:
            errors.append(f"案例图{asset_id}跨页重复使用：{'、'.join(page_ids)}")
    for digest, bindings in sorted(asset_hash_usage.items()):
        page_ids = list(dict.fromkeys(page_id for _, page_id in bindings))
        if len(page_ids) > 1:
            labels = "、".join(f"{asset_id}@{page_id}" for asset_id, page_id in bindings)
            errors.append(f"案例图文件内容跨页重复（sha256={digest[:12]}）：{labels}")

    return errors, {
        "blueprint_sha256": sha256_json(payload),
        "checked_decks": checked_decks,
        "case_asset_count": len(asset_usage),
        "case_asset_unique_hashes": len(asset_hash_usage),
        "family_asset_selection": family_asset_selection,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("blueprint", type=Path)
    parser.add_argument("--semantic-dataset", type=Path, default=DEFAULT_SEMANTICS)
    parser.add_argument("--source-dataset", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--asset-inventory", type=Path, default=DEFAULT_ASSETS)
    parser.add_argument("--allow-test-fixture", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    for path in (args.blueprint, args.semantic_dataset, args.source_dataset, args.asset_inventory):
        if not path.exists():
            print(f"FAIL\n- 文件不存在：{path}", file=sys.stderr)
            return 2
    payload = load_json(args.blueprint)
    errors, evidence = validate_payload(
        payload,
        load_json(args.semantic_dataset),
        load_json(args.source_dataset),
        load_current_inventory(args.asset_inventory),
        args.allow_test_fixture,
    )
    report = {
        "schema": "product3.production_input_validation.v0.2",
        "result": "fail" if errors else "pass",
        "project_id": payload.get("project_id"),
        "assembly_version": payload.get("assembly_version"),
        "fixture_only": bool(payload.get("fixture_only")),
        "page_count": len(payload.get("pages") or []),
        "errors": errors,
        **evidence,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"OK｜{payload.get('project_id')}｜{payload.get('assembly_version')}｜{len(payload.get('pages') or [])}页｜{evidence['blueprint_sha256'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
