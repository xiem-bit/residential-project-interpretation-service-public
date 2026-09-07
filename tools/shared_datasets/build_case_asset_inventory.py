#!/usr/bin/env python3
"""从共享案例图语义台账生成生产可读的统一JSON清单。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from pathlib import Path
from typing import Any

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = PROJECT_ROOT / "references/product3/assets/产物3案例截图素材库/案例截图素材语义台账.xlsx"
DEFAULT_LEDGER_INSPECT = Path(str(DEFAULT_LEDGER) + ".inspect.ndjson")
DEFAULT_ORIGINAL_DIR = PROJECT_ROOT / "references/product3/assets/产物3案例截图素材库/original"
DEFAULT_OUTPUT = PROJECT_ROOT / "references/product3/assets/产物3案例截图素材库/case_asset_inventory.json"
DEFAULT_LEGACY = DEFAULT_OUTPUT
DISABLED_MARKERS = ("禁用", "停用", "删除", "不可用", "已退出", "disabled", "retired")


def enabled(status: Any) -> bool:
    return not any(word in str(status or "").lower() for word in DISABLED_MARKERS)


def read_workbook_rows(path: Path) -> list[list[Any]]:
    """只读标准XLSX；编号取A列，删行、空单元格和WPS保存均不改变对应关系。"""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(path) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ["".join(t.text or "" for t in s.findall(".//m:t", ns)) for s in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheet = next(s for s in workbook.findall("m:sheets/m:sheet", ns) if s.get("name") == "案例截图语义台账")
        rel_id = sheet.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        rel = next(r for r in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels")) if r.get("Id") == rel_id)
        target = rel.get("Target", "")
        member = target.lstrip("/") if target.startswith("/") else "xl/" + target
        rows = []
        for row in ET.fromstring(archive.read(member)).findall("m:sheetData/m:row", ns):
            values: list[Any] = [None] * 8
            for cell in row:
                col = re.sub(r"\d", "", cell.get("r", ""))
                if col not in "ABCDEFGH" or len(col) != 1:
                    continue
                value = cell.find("m:v", ns)
                if cell.get("t") == "s" and value is not None:
                    text = strings[int(value.text or "0")]
                elif cell.get("t") == "inlineStr":
                    text = "".join(t.text or "" for t in cell.findall(".//m:t", ns))
                else:
                    text = value.text if value is not None else ""
                values[ord(col) - ord("A")] = text
            if str(values[0] or "").startswith("CASE-"):
                rows.append(values)
        if not rows:
            raise RuntimeError("人工台账没有有效CASE行，未覆盖现有生产索引")
        return rows


def load_current_inventory(path: Path) -> list[dict[str, Any]]:
    """当前选择及生产入口共用；台账变更即刷新派生索引，历史索引不复活删项。"""
    ledger = path.parent / DEFAULT_LEDGER.name
    inspect = Path(str(ledger) + ".inspect.ndjson")
    if ledger.is_file():
        digest = hashlib.sha256(ledger.read_bytes()).hexdigest()
        try:
            previous = json.loads(inspect.read_text(encoding="utf-8").splitlines()[0])
        except (OSError, ValueError, IndexError):
            previous = {}
        if not path.is_file() or previous.get("ledger_sha256") != digest or previous.get("inventory_sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
            build_inventory(ledger, path.parent / "original", path, path, inspect)
    return [a for a in json.loads(path.read_text(encoding="utf-8")) if enabled(a.get("status"))]


def load_ledger_rows(path: Path) -> list[list[Any]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        if item.get("kind") == "table" and item.get("sheet") == "案例截图语义台账":
            values = item.get("values") or []
            if len(values) < 4:
                raise RuntimeError("共享案例图语义台账没有有效数据行")
            return values[3:]
    raise RuntimeError("inspect文件中找不到案例截图语义台账")


def build_inventory(ledger: Path, original_dir: Path, output: Path, legacy_path: Path, inspect_path: Path, *, legacy_inspect: bool = False) -> list[dict[str, Any]]:
    legacy = {
        str(item.get("asset_id") or ""): item
        for item in (json.loads(legacy_path.read_text(encoding="utf-8")) if legacy_path.is_file() else [])
    }
    inventory: list[dict[str, Any]] = []
    rows = load_ledger_rows(ledger) if legacy_inspect else read_workbook_rows(ledger)
    for row in rows:
        padded = [*row, *(None for _ in range(max(8 - len(row), 0)))]
        asset_id, _, shape, guess, correction, semantic, recommended, status = padded[:8]
        asset_id = str(asset_id or "").strip()
        if not asset_id or not enabled(status):
            continue
        matches = sorted(original_dir.glob(f"{asset_id}_*"))
        if len(matches) != 1:
            raise RuntimeError(f"{asset_id}共享原图数量异常：{len(matches)}")
        original = matches[0]
        with Image.open(original) as image:
            width, height = image.size
        previous = legacy.get(asset_id, {})
        inventory.append(
            {
                "asset_id": asset_id,
                "asset_class": (
                    "audience_portrait"
                    if any(marker in str(shape or "") for marker in ("家庭肖像", "客群肖像", "家庭人物"))
                    else "case_reference"
                ),
                "source_type": previous.get("source_type") or "shared_case_asset",
                "source_file": previous.get("source_file") or "",
                "source_page": previous.get("source_page") or "",
                "page_value_title": previous.get("page_value_title") or "",
                "original_asset": str(original.relative_to(PROJECT_ROOT)),
                "preview_asset": str(original.relative_to(PROJECT_ROOT)),
                "width_px": width,
                "height_px": height,
                "visual_form": str(shape or "").strip(),
                "business_semantic_guess": str(guess or "").strip(),
                "user_correction": str(correction or "").strip(),
                "product3_recommended_use": str(recommended or "").strip(),
                "status": str(status or "").strip(),
                "effective_business_semantic": str(semantic or "").strip(),
            }
        )

    if len(inventory) != len({item["asset_id"] for item in inventory}):
        raise RuntimeError("共享案例图素材ID重复")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if not legacy_inspect:
        inspect_path.write_text(json.dumps({"kind": "source", "ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(), "inventory_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}, ensure_ascii=False) + "\n" + json.dumps({"kind": "table", "sheet": "案例截图语义台账", "values": [[], [], [], *rows]}, ensure_ascii=False) + "\n", encoding="utf-8")
    return inventory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--ledger-inspect", type=Path, help="仅显式迁移旧索引时使用；现行入口直接读取XLSX")
    parser.add_argument("--original-dir", type=Path, default=DEFAULT_ORIGINAL_DIR)
    parser.add_argument("--legacy-inventory", type=Path, default=DEFAULT_LEGACY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    inventory = build_inventory(args.ledger_inspect or args.ledger, args.original_dir, args.output, args.legacy_inventory, Path(str(args.ledger) + ".inspect.ndjson"), legacy_inspect=bool(args.ledger_inspect))
    print(
        json.dumps(
            {
                "output": str(args.output),
                "assets": len(inventory),
                "audience_portraits": sum(
                    item["asset_class"] == "audience_portrait" for item in inventory
                ),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
