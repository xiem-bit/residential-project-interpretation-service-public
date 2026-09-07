#!/usr/bin/env python3
"""检查产物3PPT生产结果并形成机器回执。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from zipfile import ZipFile

from PIL import Image, ImageChops, ImageDraw, ImageStat


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_visible_copy(pptx: Path, pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Read real slide text, excluding notes; retain generator-added copy too."""
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
          "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
    records = []
    with ZipFile(pptx) as archive:
        for index, page in enumerate(pages, 1):
            root = ElementTree.fromstring(archive.read(f"ppt/slides/slide{index}.xml"))
            for shape in root.findall(".//p:sp", ns):
                paragraphs = ["".join(n.text or "" for n in para.findall(".//a:t", ns)) for para in shape.findall(".//a:p", ns)]
                text = "\n".join(paragraphs)
                if not text.strip():
                    continue
                identity = shape.find(".//p:cNvPr", ns)
                name = identity.get("name", "") if identity is not None else ""
                prefix = page["page_id"] + "-"
                role = name[len(prefix):] if name.startswith(prefix) else name
                records.append({"page": index, "page_id": page["page_id"], "role": role, "text": text})
    return records


def copy_errors(pages: list[dict[str, Any]], records: list[dict[str, Any]]) -> list[str]:
    normalize = lambda s: re.sub(r"\s+", "", s)
    errors = []
    for page in pages:
        if not page.get("render_content"):
            continue  # Historical technical-fixture and patch paths retain their checks.
        actual = "".join(r["text"] for r in records if r["page_id"] == page["page_id"] and r["role"] != "page_number")
        if normalize(actual) != normalize(page["visible_copy"]):
            errors.append(f"{page['page_id']}实际PPTX文字与已编辑全文不一致（含副标题、卡片、地图标注及页底说明）")
    return errors


def rms_difference(left_path: Path, right_path: Path) -> float:
    with Image.open(left_path).convert("RGB") as left, Image.open(right_path).convert("RGB") as right:
        if left.size != right.size:
            right = right.resize(left.size)
        stat = ImageStat.Stat(ImageChops.difference(left, right))
        squares = sum(value * value for value in stat.rms)
        return math.sqrt(squares / max(len(stat.rms), 1))


def build_montage(previews: list[Path], output: Path, columns: int = 4) -> None:
    if not previews:
        return
    slide_width = 480
    slide_height = 270
    label_height = 28
    gap = 12
    padding = 16
    rows = math.ceil(len(previews) / columns)
    canvas = Image.new(
        "RGB",
        (
            padding * 2 + columns * slide_width + (columns - 1) * gap,
            padding * 2 + rows * (slide_height + label_height) + (rows - 1) * gap,
        ),
        "#f3f4f6",
    )
    draw = ImageDraw.Draw(canvas)
    for index, preview in enumerate(previews):
        with Image.open(preview).convert("RGB") as image:
            image.thumbnail((slide_width, slide_height))
            col = index % columns
            row = index // columns
            left = padding + col * (slide_width + gap)
            top = padding + row * (slide_height + label_height + gap)
            canvas.paste(image, (left, top))
            draw.text((left + 4, top + slide_height + 5), f"{index + 1}", fill="#111827")
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--pptx", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--montage", type=Path)
    parser.add_argument("--source-preview-dir", type=Path)
    parser.add_argument("--allowed-rms", type=float, default=1.0)
    parser.add_argument("--pdf", type=Path, help="由同版PPTX预览生成PDF，不另行排版")
    args = parser.parse_args()

    plan = load_json(args.plan)
    mapping = load_json(args.mapping)
    errors: list[str] = []
    warnings: list[str] = []
    drift: list[dict[str, Any]] = []
    case_assets = [
        item
        for item in mapping.get("applied_assets", [])
        if Path(str(item.get("path") or "")).name.startswith("CASE-")
    ]
    case_hashes = [str(item.get("sha256") or "") for item in case_assets if item.get("sha256")]
    case_media_references: dict[str, int] = {}
    if not args.pptx.exists():
        errors.append(f"PPTX不存在：{args.pptx}")
    elif mapping.get("output_deck_sha256") != sha256_file(args.pptx):
        errors.append("PPTX哈希与生产映射不一致")
    if case_assets:
        if len(case_hashes) != len(case_assets) or len(set(case_hashes)) != len(case_assets):
            errors.append("案例图清单存在重复文件或缺少文件指纹")
        if args.pptx.exists():
            media_by_hash: dict[str, list[str]] = {}
            relationship_counts: dict[str, int] = {}
            with ZipFile(args.pptx, "r") as archive:
                for name in archive.namelist():
                    if name.startswith("ppt/media/"):
                        digest = hashlib.sha256(archive.read(name)).hexdigest()
                        media_by_hash.setdefault(digest, []).append(Path(name).name)
                for name in archive.namelist():
                    if not name.startswith("ppt/slides/_rels/slide") or not name.endswith(".xml.rels"):
                        continue
                    root = ElementTree.fromstring(archive.read(name))
                    for relation in root:
                        relation_type = str(relation.attrib.get("Type") or "")
                        if not relation_type.endswith("/image"):
                            continue
                        target_name = Path(str(relation.attrib.get("Target") or "")).name
                        relationship_counts[target_name] = relationship_counts.get(target_name, 0) + 1
            for digest in sorted(set(case_hashes)):
                media_names = media_by_hash.get(digest, [])
                reference_count = sum(relationship_counts.get(name, 0) for name in media_names)
                case_media_references[digest] = reference_count
                if len(media_names) != 1 or reference_count != 1:
                    errors.append(
                        f"案例图未满足单页单次使用：{digest[:12]}，媒体文件={len(media_names)}，页面引用={reference_count}"
                    )
    if plan.get("blueprint_sha256") != mapping.get("blueprint_sha256"):
        errors.append("装配清单哈希与生产映射不一致")
    if plan.get("page_count") != mapping.get("page_count"):
        errors.append("生产计划与映射页数不一致")
    plan_pages = plan.get("pages") or []
    mapped_pages = mapping.get("pages") or []
    actual_copy = []
    if args.pptx.exists() and any(p.get("render_content") for p in plan_pages):
        actual_copy = read_visible_copy(args.pptx, plan_pages)
        errors.extend(copy_errors(plan_pages, actual_copy))
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        (args.receipt.parent / "实际可见文案.json").write_text(json.dumps(actual_copy,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        for name, selected in [
            ("A级标题与核心判断.txt", [r for r in actual_copy if not r["role"].startswith("quote") and any(k in r["role"] for k in ["title", "subtitle", "conclusion"])]),
            ("B级实际可见全文.txt", [r for r in actual_copy if not r["role"].startswith("quote")]),
            ("全部实际可见文字.md", actual_copy),
        ]:
            (args.receipt.parent / name).write_text("\n\n".join(f"第{r['page']}页 {r['text']}" for r in selected)+"\n",encoding="utf-8")
    preview_paths: list[Path] = []
    for index, page in enumerate(plan_pages):
        if index >= len(mapped_pages):
            errors.append(f"缺少第{index + 1}页映射")
            continue
        mapped = mapped_pages[index]
        if mapped.get("page_id") != page.get("page_id") or mapped.get("order") != index + 1:
            errors.append(f"第{index + 1}页页面ID或顺序不一致")
        if not plan.get("fixture_only"):
            if page.get("production_route") == "reuse_source_slide":
                errors.append(f"{page.get('page_id')}正式项目仍在整页复用历史来源页")
            if mapped.get("current_project_copy_status") != "loaded_and_source_copy_cleared":
                errors.append(
                    f"{page.get('page_id')}缺少当前项目文案装载回执，无法证明历史来源文案已清除"
                )
        for file_label in ("preview_path", "layout_path"):
            file_path = Path(str(mapped.get(file_label) or ""))
            if not file_path.exists():
                errors.append(f"{page.get('page_id')}缺少{file_label}")
        preview_path = Path(str(mapped.get("preview_path") or ""))
        if preview_path.exists():
            preview_paths.append(preview_path)
        layout_path = Path(str(mapped.get("layout_path") or ""))
        if layout_path.exists():
            layout = load_json(layout_path)
            frame = layout.get("slide", {}).get("frame", {})
            width = float(frame.get("width") or 0)
            height = float(frame.get("height") or 0)
            for element in layout.get("elements", []):
                bbox = element.get("bbox") or []
                if len(bbox) != 4:
                    continue
                left, top, box_width, box_height = map(float, bbox)
                if left < -1 or top < -1 or left + box_width > width + 1 or top + box_height > height + 1:
                    errors.append(f"{page.get('page_id')}对象越出画布：{element.get('aid') or element.get('name')}")
        roles = mapped.get("objects") or {}
        if "title" in page.get("expected_object_roles", []) and not roles.get("title"):
            errors.append(f"{page.get('page_id')}未识别标题对象")
        if page.get("semantic_id") == "P3-COMPETITION-MAP" and not roles.get("map"):
            errors.append(f"{page.get('page_id')}未识别地图对象")
        if args.source_preview_dir:
            source_slide = int(page.get("source_slide") or 0)
            source_ids = page.get("source_page_ids") or []
            by_source_id = args.source_preview_dir / f"{source_ids[0]}.png" if source_ids else Path()
            by_slide_number = args.source_preview_dir / f"source-slide-{source_slide:02d}.png"
            source_preview = by_source_id if source_ids and by_source_id.exists() else by_slide_number
            output_preview = Path(str(mapped.get("preview_path") or ""))
            if source_preview.exists() and output_preview.exists():
                value = rms_difference(source_preview, output_preview)
                drift.append({"page_id": page.get("page_id"), "rms": round(value, 4)})
                if value > args.allowed_rms:
                    errors.append(f"{page.get('page_id')}视觉漂移RMS={value:.4f}>{args.allowed_rms}")
            else:
                warnings.append(f"{page.get('page_id')}缺少来源预览，未执行视觉漂移比较")

    if args.montage and len(preview_paths) == len(mapped_pages):
        build_montage(preview_paths, args.montage)
    elif args.montage:
        errors.append("逐页预览不完整，无法生成整套缩略图")

    if args.pdf and not errors:
        from reportlab.pdfgen import canvas
        args.pdf.parent.mkdir(parents=True, exist_ok=True)
        pdf = canvas.Canvas(str(args.pdf))
        for preview in preview_paths:
            with Image.open(preview) as im:
                width, height = im.size
            pdf.setPageSize((width * .75, height * .75))
            pdf.drawImage(str(preview), 0, 0, width=width * .75, height=height * .75)
            pdf.showPage()
        pdf.save()

    receipt = {
        "schema": "product3.production_receipt.v0.1",
        "result": "fail" if errors else "pass",
        "mode": "create",
        "change_scope": "create",
        "project_id": plan.get("project_id"),
        "assembly_version": plan.get("assembly_version"),
        "fixture_only": bool(plan.get("fixture_only")),
        "actual_copy_checked": bool(actual_copy),
        "visible_copy_scope": "原生主副标题、正文、卡片、标签和页底；图片自带文字由现有看图检查承担",
        "pdf": str(args.pdf) if args.pdf and not errors else None,
        "pdf_sha256": sha256_file(args.pdf) if args.pdf and not errors else None,
        "page_count": len(mapped_pages),
        "affected_pages": [page.get("page_id") for page in plan_pages],
        "protected_pages": [],
        "human_review_ready": not errors and not plan.get("fixture_only"),
        "technical_fixture_passed": not errors and bool(plan.get("fixture_only")),
        "errors": errors,
        "warnings": warnings,
        "visual_drift": drift,
        "case_asset_count": len(case_assets),
        "case_asset_unique_hashes": len(set(case_hashes)),
        "case_asset_single_use_passed": bool(case_assets) and all(
            count == 1 for count in case_media_references.values()
        ),
        "output_pptx": str(args.pptx.resolve()),
        "montage": str(args.montage.resolve()) if args.montage and args.montage.exists() else "",
        "output_deck_sha256": mapping.get("output_deck_sha256"),
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS" if not errors else "FAIL")
    print(args.receipt)
    for error in errors:
        print(f"- {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
