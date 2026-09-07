#!/usr/bin/env python3
"""把已裁定装配清单转换为机器派生的逐页PPT生产计划。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from validate_production_input import DEFAULT_ASSETS, load_current_inventory, parse_asset_bindings, validate_payload


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEMANTICS = PROJECT_ROOT / "references/product3/assets/产物3页面模板库/datasets/page_semantic_dataset.v0.3.json"
DEFAULT_SOURCES = PROJECT_ROOT / "references/product3/assets/产物3页面模板库/datasets/source_page_semantic_annotations.v0.3.json"
SOURCE_ID_RE = re.compile(r"(?:QJ|B10|GT)-\d{2}")


ROLE_BY_SEMANTIC = {
    "P3-COVER-CLAIM": ["title", "subtitle"],
    "P3-SECTION-PROMISE": ["title", "subtitle"],
    "P3-RESEARCH-CREDIBILITY": ["title", "subtitle", "body", "conclusion", "source_note"],
    "P3-BUYER-VOICE": ["title", "subtitle", "body", "conclusion", "source_note"],
    "P3-CHOICE-SITUATION": ["title", "subtitle", "body", "conclusion"],
    "P3-COMPETITION-MAP": ["title", "subtitle", "map", "body", "conclusion", "source_note"],
    "P3-ADVANTAGE-SYNTHESIS": ["title", "subtitle", "body", "conclusion"],
    "P3-VALUE-ANCHOR": ["title", "subtitle", "body", "conclusion"],
    "P3-SC-OVERVIEW": ["title", "subtitle", "body", "conclusion"],
    "P3-SC-SCENE": ["title", "subtitle", "main_image", "body", "conclusion"],
    "P3-SC-PROOF": ["title", "subtitle", "main_image", "proof_image_1", "proof_image_2", "body", "conclusion", "source_note"],
    "P3-UE-FULLSCREEN": ["title", "subtitle", "main_image", "body", "footer"],
    "P3-FAMILY-SEGMENT": ["title", "subtitle", "main_image", "body", "conclusion"],
    "P3-FAMILY-PATH": ["title", "subtitle", "main_image", "proof_image_1", "body", "conclusion"],
    "P3-UE-BLUEPRINT": ["title", "subtitle", "body", "conclusion"],
    "P3-AI-RECOMMENDER": ["title", "subtitle", "main_image", "body", "conclusion"],
    "P3-CLOSING-OUTCOME": ["title", "subtitle", "body", "conclusion"],
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def source_ids(value: Any) -> list[str]:
    return list(dict.fromkeys(SOURCE_ID_RE.findall(str(value or ""))))


def classify_change(action: str) -> str:
    action = action or "assemble"
    if action in {"move_up", "move_down", "reassign_section", "reorder"}:
        return "order"
    if action in {"replace_case_asset", "add_case_evidence"}:
        return "image"
    if action in {"edit_copy", "rewrite_text"}:
        return "text"
    if action in {"recompose_by_semantic"}:
        return "page"
    if action in {"replace_visual_variant", "replace_visual_reference", "replace_source_template"}:
        return "structure"
    if action in {"insert_by_semantic", "duplicate_page", "split_page", "merge_pages", "soft_delete", "restore_page"}:
        return "structure"
    return "create"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("blueprint", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--frame-map", type=Path)
    parser.add_argument("--semantic-dataset", type=Path, default=DEFAULT_SEMANTICS)
    parser.add_argument("--source-dataset", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--asset-inventory", type=Path, default=DEFAULT_ASSETS)
    parser.add_argument("--content", type=Path, help="当前项目页面内容JSON；与冻结清单按页面ID对应")
    args = parser.parse_args()

    blueprint = load_json(args.blueprint)
    semantic_dataset = load_json(args.semantic_dataset)
    source_dataset = load_json(args.source_dataset)
    validation_errors, _ = validate_payload(
        blueprint,
        semantic_dataset,
        source_dataset,
        load_current_inventory(args.asset_inventory),
        allow_test_fixture=bool(blueprint.get("fixture_only")),
    )
    if validation_errors:
        raise SystemExit(
            "装配清单未通过正式生产门禁：\n- " + "\n- ".join(validation_errors)
        )
    semantics = {item["semanticId"]: item for item in semantic_dataset.get("semantics", [])}
    sources = {item["sourcePageId"]: item for item in source_dataset.get("pages", [])}
    assets = {item["asset_id"]: item for item in load_current_inventory(args.asset_inventory)}
    content = load_json(args.content) if args.content else []
    content_by_id = {item["id"]: item for item in content}
    if args.content and (len(content) != len(content_by_id) or set(content_by_id) != {p["页面ID"] for p in blueprint["pages"]}):
        raise SystemExit("页面内容与冻结清单的页面ID不完全一致")
    pages = []

    for page in blueprint.get("pages", []):
        semantic_id = str(page.get("页面语义ID") or "")
        semantic = semantics.get(semantic_id, {})
        original_ids = source_ids(page.get("来源页ID"))
        reference_ids = source_ids(page.get("视觉参考页ID"))
        preferred_ids = reference_ids or original_ids
        resolved_sources = [sources[item] for item in preferred_ids if item in sources]
        if len(resolved_sources) == 1 and blueprint.get("fixture_only"):
            route = "reuse_source_slide"
        elif len(resolved_sources) == 1:
            route = "reuse_structure_rewrite_copy"
        elif len(resolved_sources) > 1:
            route = "compose_from_layout"
        else:
            route = "compose_from_layout"
        source = resolved_sources[0] if len(resolved_sources) == 1 else {}
        pages.append({
            "order": page.get("页序"),
            "page_id": page.get("页面ID"),
            "page_name": page.get("页面名称"),
            "visible_copy": page.get("页面文案") or "",
            "semantic_id": semantic_id,
            "semantic_name": semantic.get("name", ""),
            "responsibility": page.get("这一页只负责"),
            "speaking_action": page.get("演讲动作"),
            "transition": page.get("转场"),
            "visual_structure": page.get("视觉结构"),
            "visual_reference": page.get("视觉参考页ID") or page.get("来源页ID") or "",
            "visual_variant_id": page.get("视觉变体ID") or "",
            "asset_bindings": page.get("素材编号") or "",
            "case_slots": page.get("case_slots") or [],
            "assembly_action": page.get("装配动作") or "assemble",
            "change_scope": classify_change(str(page.get("装配动作") or "assemble")),
            "production_route": route,
            "source_page_ids": preferred_ids,
            "source_deck": source.get("sourceDeck", ""),
            "source_slide": source.get("sourceSlide"),
            "source_visual_archetype_id": source.get("visualArchetypeId", ""),
            "source_project": source.get("sourceProject", ""),
            "source_reuse_boundary": (
                "technical_fixture_preserve_source_copy"
                if blueprint.get("fixture_only")
                else "structure_only_current_project_copy_required"
            ),
            "expected_object_roles": ROLE_BY_SEMANTIC.get(semantic_id, ["title", "body"]),
        })
        if args.content:
            current = content_by_id[page["页面ID"]]
            if current.get("semantic") != semantic_id or current.get("title") != page["页面名称"]:
                raise SystemExit(f"{page['页面ID']}页面标题或职责与冻结清单不一致")
            # Layout data adds no second content authority: the builder compares all
            # rendered wording to 页面文案 before exporting, then re-reads the PPTX.
            current["order"] = page["页序"]
            if semantic_id == "P3-FAMILY-SEGMENT":
                slot_assets = [slot["asset_id"] for slot in page["case_slots"]]
                pairs = current.get("body", {}).get("pairs", [])
                if current.get("layout") not in {"family", "gallery"} or (current.get("layout") == "gallery" and len(pairs) != 2) or [pair[0] for pair in pairs] != slot_assets:
                    raise SystemExit(f"{page['页面ID']}实际人物版位与已裁定case_slots不一致，不能改版式或少装肖像")
            resolved = []
            case_ids, error = parse_asset_bindings(page.get("素材编号"))
            if error:
                raise SystemExit(error)
            for asset_id in case_ids:
                asset = assets[asset_id]
                file = PROJECT_ROOT / asset["original_asset"]
                resolved.append({"asset_id": asset_id, "path": str(file.resolve()), "sha256": hashlib.sha256(file.read_bytes()).hexdigest(), "usage": asset.get("effective_business_semantic"), "kind": "case"})
            if current.get("map"):
                map_data = current["map"]
                if isinstance(map_data, str):
                    map_data = load_json(args.content.parent / map_data)
                image_path = Path(map_data["image"])
                if not image_path.is_absolute():
                    image_path = args.content.parent / image_path
                asset_id = map_data.get("asset_id")
                if not asset_id or asset_id not in (page.get("本项目图形") or []):
                    raise SystemExit(f"{page['页面ID']}地图须对应既有本项目图形登记")
                map_data["image"] = str(image_path.resolve())
                current["map"] = map_data
                resolved.append({"asset_id": asset_id, "path": str(image_path.resolve()), "sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(), "kind": "map"})
            pages[-1].update(render_content=current, resolved_assets=resolved, production_route="compose_from_layout")

    decks = sorted({page["source_deck"] for page in pages if page["source_deck"]})
    plan = {
        "schema": "product3.production_plan.v0.1",
        "project_id": blueprint.get("project_id"),
        "project_name": blueprint.get("project_name"),
        "assembly_version": blueprint.get("assembly_version"),
        "fixture_only": bool(blueprint.get("fixture_only")),
        "blueprint_path": str(args.blueprint.resolve()),
        "blueprint_sha256": sha256_json(blueprint),
        "asset_inventory_path": str(args.asset_inventory.resolve()),
        "page_count": len(pages),
        "source_decks": decks,
        "requires_multi_source_starter": len(decks) > 1,
        "pages": pages,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.frame_map:
        if plan["requires_multi_source_starter"] or any(page["production_route"] != "reuse_source_slide" for page in pages):
            raise SystemExit("多来源或重新构图计划不能生成单一来源template-frame-map")
        selected = {int(page["source_slide"]) for page in pages}
        deck_id = pages[0]["source_page_ids"][0].split("-")[0] if pages and pages[0]["source_page_ids"] else ""
        source_slide_count = max(
            (int(item["sourceSlide"]) for item in source_dataset.get("pages", []) if item.get("deckId") == deck_id),
            default=max(selected, default=0),
        )
        frame_map = {
            "outputSlides": [
                {
                    "outputSlide": index + 1,
                    "sourceSlide": page["source_slide"],
                    "narrativeRole": "preserve-only technical source slide",
                    "reuseMode": "duplicate-slide",
                    "editTargets": [],
                }
                for index, page in enumerate(pages)
            ],
            "omittedSourceSlides": [
                {"sourceSlide": slide, "reason": "not selected by approved assembly blueprint"}
                for slide in range(1, source_slide_count + 1)
                if slide not in selected
            ],
        }
        args.frame_map.parent.mkdir(parents=True, exist_ok=True)
        args.frame_map.write_text(json.dumps(frame_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.out)
    print(f"pages={len(pages)} source_decks={len(decks)} multi_source={plan['requires_multi_source_starter']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
