#!/usr/bin/env python3
"""从现有结构化页面输入导出产物3装配清单；兼容历史 .grist 文件。

默认只导出已完成约定装配确认的当前版本，不新增逐页真人审批。
`--allow-draft` 仅用于试跑和审阅，不得作为正式 PPT 的消费输入。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
import sys
from pathlib import Path


REQUIRED_LABELS = {
    "页序",
    "页面名称",
    "页面文案",
    "这一页只负责",
    "演讲动作",
    "裁定状态",
    "进入PPT生产",
    "项目ID",
    "装配版本",
    "上游冻结状态",
    "页面ID",
    "有效",
}


def quote_ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def slug(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z._-]+", "-", value.strip())
    return cleaned.strip("-") or "unnamed"


def find_assembly_table(conn: sqlite3.Connection) -> tuple[str, dict[str, str]]:
    rows = conn.execute(
        """
        SELECT t.tableId, c.colId, c.label
        FROM _grist_Tables AS t
        JOIN _grist_Tables_column AS c ON c.parentId = t.id
        WHERE t.tableId NOT LIKE '_grist%'
        ORDER BY t.id, c.parentPos
        """
    ).fetchall()
    by_table: dict[str, dict[str, str]] = {}
    for table_id, col_id, label in rows:
        by_table.setdefault(table_id, {})[label] = col_id
    matches = [
        (table_id, labels)
        for table_id, labels in by_table.items()
        if REQUIRED_LABELS.issubset(labels)
    ]
    if len(matches) != 1:
        raise RuntimeError(f"无法唯一识别当前项目装配页，匹配数={len(matches)}")
    return matches[0]


def read_records(
    conn: sqlite3.Connection, table_id: str, labels: dict[str, str]
) -> list[dict[str, object]]:
    ordered_labels = [
        "页序",
        "缩略图URL",
        "页面名称",
        "页面文案",
        "这一页只负责",
        "演讲动作",
        "转场",
        "视觉结构",
        "视觉变体ID",
        "视觉变体名称",
        "视觉参考页ID",
        "章节",
        "关系来源页面ID",
        "来源页ID",
        "页面语义ID",
        "素材编号",
        "补充修改说明",
        "人工修订意见",
        "裁定状态",
        "进入PPT生产",
        "项目ID",
        "项目名称",
        "装配版本",
        "上游冻结状态",
        "页面ID",
        "装配动作",
        "有效",
        "可修改范围",
    ]
    selected_labels = [label for label in ordered_labels if label in labels]
    selected_columns = ", ".join(quote_ident(labels[label]) for label in selected_labels)
    sql = (
        f"SELECT id, {selected_columns} FROM {quote_ident(table_id)} "
        f"ORDER BY {quote_ident(labels['页序'])}, id"
    )
    records = []
    for row in conn.execute(sql):
        record = {"grist_row_id": row[0]}
        record.update(dict(zip(selected_labels, row[1:])))
        records.append(record)
    return records


def validate(records: list[dict[str, object]], allow_draft: bool) -> list[str]:
    errors: list[str] = []
    active = [record for record in records if bool(record.get("有效"))]
    if not active:
        errors.append("没有有效页面")
        return errors

    project_ids = {str(record.get("项目ID") or "").strip() for record in active}
    versions = {str(record.get("装配版本") or "").strip() for record in active}
    if "" in project_ids or len(project_ids) != 1:
        errors.append(f"项目ID不唯一或为空：{sorted(project_ids)}")
    if "" in versions or len(versions) != 1:
        errors.append(f"装配版本不唯一或为空：{sorted(versions)}")

    page_ids = [str(record.get("页面ID") or "").strip() for record in active]
    if "" in page_ids or len(page_ids) != len(set(page_ids)):
        errors.append("有效页面存在空页面ID或重复页面ID")

    orders = [record.get("页序") for record in active]
    if any(order is None for order in orders) or len(orders) != len(set(orders)):
        errors.append("有效页面存在空页序或重复页序")

    for record in active:
        page = record.get("页面ID") or f"row-{record.get('grist_row_id', '?')}"
        freeze = str(record.get("上游冻结状态") or "").lower()
        explicitly_not_frozen = "not_frozen" in freeze or "未冻结" in freeze or "尚未冻结" in freeze
        is_frozen = ("frozen" in freeze or "冻结" in freeze) and not explicitly_not_frozen
        if not allow_draft and not is_frozen:
            errors.append(f"{page}：上游冻结状态不合格")
        if not str(record.get("页面名称") or "").strip():
            errors.append(f"{page}：页面名称为空")
        if not str(record.get("页面文案") or "").strip():
            errors.append(f"{page}：页面文案为空")
        if not str(record.get("这一页只负责") or "").strip():
            errors.append(f"{page}：页面职责为空")
        if not str(record.get("演讲动作") or "").strip():
            errors.append(f"{page}：演讲动作为空")
        if record.get("页面语义ID") == "P3-COMPETITION-MAP":
            if not str(record.get("视觉变体ID") or "").strip():
                errors.append(f"{page}：竞争地图尚未选择视觉变体")
            if not str(record.get("视觉参考页ID") or "").strip():
                errors.append(f"{page}：竞争地图尚未选择视觉参考页")
        if not allow_draft:
            if record.get("裁定状态") != "approved":
                errors.append(f"{page}：尚未 approved")
            if not bool(record.get("进入PPT生产")):
                errors.append(f"{page}：未勾选进入PPT生产")
    return errors


def build_payload(records: list[dict[str, object]], is_draft: bool) -> dict[str, object]:
    active = [record for record in records if bool(record.get("有效"))]
    active.sort(key=lambda record: (float(record.get("页序") or 0), str(record.get("页面ID") or "")))
    project_id = str(active[0]["项目ID"])
    version = str(active[0]["装配版本"])
    project_name = str(active[0].get("项目名称") or "")
    return {
        "schema": "product3.assembly_blueprint.v0.1",
        "export_status": "draft_non_production" if is_draft else "approved_for_ppt_production",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "project_id": project_id,
        "project_name": project_name,
        "assembly_version": version,
        "page_count": len(active),
        "pages": active,
    }


def markdown(payload: dict[str, object]) -> str:
    status = payload["export_status"]
    lines = [
        f"# {payload['project_name']}｜产物3逐页装配蓝图",
        "",
        f"- 项目ID：`{payload['project_id']}`",
        f"- 装配版本：`{payload['assembly_version']}`",
        f"- 导出状态：`{status}`",
        f"- 页面数量：{payload['page_count']}",
        "",
    ]
    if status != "approved_for_ppt_production":
        lines.extend(["> 本文件仅用于试排与真人审阅，不得进入正式 PPT 生产。", ""])
    for page in payload["pages"]:
        lines.extend(
            [
                f"## 第{page['页序']}页｜{page['页面名称']}",
                "",
                f"- 页面ID：`{page['页面ID']}`",
                f"- 页面语义：`{page.get('页面语义ID') or '待补'}`",
                f"- 来源页：`{page.get('来源页ID') or '待选'}`",
                f"- 页面文案：\n\n{page.get('页面文案') or '待Codex按页面语义与当前项目事实补齐'}",
                "",
                f"- 页面职责：{page['这一页只负责']}",
                f"- 演讲动作：{page['演讲动作']}",
                f"- 转场：{page.get('转场') or '待补'}",
                f"- 视觉结构：{page.get('视觉结构') or '待补'}",
                f"- 视觉变体：`{page.get('视觉变体ID') or '通用'}` {page.get('视觉变体名称') or ''}",
                f"- 视觉参考页：`{page.get('视觉参考页ID') or '待选'}`",
                f"- 章节：{page.get('章节') or '待补'}",
                f"- 关系来源页面：`{page.get('关系来源页面ID') or '无'}`",
                f"- 素材编号：`{page.get('素材编号') or '待选'}`",
                f"- 装配动作：`{page.get('装配动作') or 'assemble'}`",
                f"- 真人补充修改说明：{page.get('补充修改说明') or '无'}",
                f"- 人工修订意见：{page.get('人工修订意见') or '无'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=Path, help="当前装配JSON（含pages）或历史.grist文件")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--allow-draft", action="store_true")
    args = parser.parse_args()

    if not args.input_file.exists():
        print(f"装配输入不存在：{args.input_file}", file=sys.stderr)
        return 2
    source = None
    if args.input_file.suffix.lower() == ".json":
        source = json.loads(args.input_file.read_text(encoding="utf-8"))
        records = source["pages"] if isinstance(source, dict) else source
    else:
        with sqlite3.connect(f"file:{args.input_file.resolve()}?mode=ro", uri=True) as conn:
            table_id, labels = find_assembly_table(conn)
            records = read_records(conn, table_id, labels)
    errors = validate(records, args.allow_draft)
    if errors:
        print("装配清单未通过导出门禁：", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    payload = build_payload(records, args.allow_draft)
    if isinstance(source, dict):
        # 保留同一输入中的UE页面、制作引用与讲稿等关系，不把导出降为旧表格列。
        payload = {**source, **payload}
    default_out = (
        Path(__file__).resolve().parents[1]
        / "exports"
        / slug(str(payload["project_id"]))
        / slug(str(payload["assembly_version"]))
    )
    out_dir = args.out_dir or default_out
    out_dir.mkdir(parents=True, exist_ok=True)
    basename = "draft_装配清单" if args.allow_draft else "approved_装配清单"
    json_path = out_dir / f"{basename}.json"
    md_path = out_dir / f"{basename}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown(payload), encoding="utf-8")
    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
