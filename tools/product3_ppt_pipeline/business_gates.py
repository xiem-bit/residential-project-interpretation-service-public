#!/usr/bin/env python3
"""产物3正式生产的客户前台与素材业务门禁。"""

from __future__ import annotations

import re
import hashlib
import json
from collections.abc import Iterable
from typing import Any


INTERNAL_METHOD_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("价值账", re.compile(r"价值账")),
    ("家庭优先级调整", re.compile(r"家庭优先级.{0,8}(调整|重排|重算|排序|变化)")),
    ("得到与代价比较法", re.compile(r"得到与代价.{0,12}(同一|一张|比较框架)")),
    ("四个WHY内部推导", re.compile(r"四个\s*(?:WHY|[“\"]?为什么买[”\"]?)", re.IGNORECASE)),
    ("候选门禁", re.compile(r"(候选收敛|视角门禁|逐条过门禁)")),
)

PORTRAIT_MARKERS = (
    "肖像",
    "人物肖像",
    "家庭角色",
    "家庭人物",
    "客群形象",
    "夫妻",
    "亲子",
    "三口之家",
    "三代家庭",
)

FAMILY_SEGMENT_SEMANTICS = {"P3-FAMILY-SEGMENT"}


def chapter2_basis(contract: dict[str, Any]) -> dict[str, str]:
    """给已有事实编号保留审阅指纹；不判断事实真假，纯空白变更保持同值。"""
    result = {}
    for dimension in contract.get("chapter2", {}).get("dimensions", []):
        parties = [dimension.get("subject", {}), *dimension.get("competitors", [])]
        for party in parties:
            for fact in [*party.get("strengths", []), *party.get("limitations", [])]:
                value = {key: fact.get(key) for key in ("text", "factor_id", "evidence_refs")}
                value["text"] = re.sub(r"\s+", "", str(value["text"] or ""))
                result[fact["id"]] = hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return result


def changed_basis_review(payload: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    current = chapter2_basis(contract)
    previous = payload.get("reviewed_chapter2_basis")
    if previous is None:
        return {"current_basis": current, "changed_facts": [], "affected_ids": [], "page_ids": []}
    changed = {key for key in set(previous) | set(current) if previous.get(key) != current.get(key)}
    affected = set(changed)
    objects = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("id"):
                refs = set()
                for key, item in value.items():
                    if key.endswith(("_refs", "_ref")):
                        refs.update(item if isinstance(item, list) else [item] if isinstance(item, str) else [])
                objects.append((value["id"], refs))
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(contract.get("chapter2", {}))
    while True:
        added = {item_id for item_id, refs in objects if refs & affected} - affected
        if not added:
            break
        affected.update(added)
    pages = []
    for page in payload.get("pages", []):
        # 复用后台职责和讲稿中的合同引用，不另建一份页面关系表。
        text = "\n".join(str(page.get(key) or "") for key in ("这一页只负责", "演讲动作", "关系来源页面ID"))
        ids = set(re.findall(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+", text))
        if ids & affected:
            pages.append(page["页面ID"])
    return {"current_basis": current, "changed_facts": sorted(changed), "affected_ids": sorted(affected), "page_ids": pages}


def visible_text(page: dict[str, Any]) -> str:
    """只读取会进入甲方页面的标题与可见文案。"""
    return "\n".join(
        str(page.get(label) or "").strip()
        for label in ("页面名称", "页面文案")
        if str(page.get(label) or "").strip()
    )


def page_business_query(page: dict[str, Any]) -> str:
    return "\n".join(
        str(page.get(label) or "").strip()
        for label in ("页面名称", "页面文案", "这一页只负责", "视觉结构")
        if str(page.get(label) or "").strip()
    )


def locked_quote_errors(page: dict[str, Any]) -> list[str]:
    """核对既有引文身份的装配传递，不鉴定来源真假或决定引文用途。"""
    errors = []
    quotes = page.get("原文引文", [])
    if not isinstance(quotes, list):
        return ["原文引文须为逐段记录"]
    for quote in quotes:
        if not isinstance(quote, dict):
            errors.append("原文引文缺少文字及来源身份")
            continue
        field = quote.get("field", "页面文案")
        text = str(quote.get("text") or "")
        if field not in {"页面名称", "页面文案"} or not text or text not in str(page.get(field) or ""):
            errors.append("锁定引文与指定可见文字不一致")
        if not str(quote.get("source") or "").strip() or not str(quote.get("purpose") or "").strip():
            errors.append("锁定引文缺少来源身份或本页引用用途；引号本身不构成豁免")
    return errors


def internal_method_hits(page: dict[str, Any]) -> list[str]:
    fields = {key: str(page.get(key) or "") for key in ("页面名称", "页面文案")}
    if not locked_quote_errors(page):
        # 只扣除已装载、具来源和用途的精确引文。自写分析及相同词语的其他出现仍检查。
        for quote in page.get("原文引文", []):
            field = quote.get("field", "页面文案")
            fields[field] = fields[field].replace(quote["text"], "", 1)
    text = "\n".join(fields.values())
    return [label for label, pattern in INTERNAL_METHOD_PATTERNS if pattern.search(text)]


def asset_semantic_text(asset: dict[str, Any]) -> str:
    return " ".join(
        str(asset.get(label) or "").strip()
        for label in (
            "effective_business_semantic",
            "product3_recommended_use",
            "visual_form",
            "asset_class",
        )
        if str(asset.get(label) or "").strip()
    )


def is_audience_portrait(asset: dict[str, Any]) -> bool:
    if asset.get("asset_class"):
        return asset["asset_class"] == "audience_portrait"
    text = asset_semantic_text(asset)
    return any(marker in text for marker in PORTRAIT_MARKERS)


def required_portrait_count(page: dict[str, Any]) -> int:
    if str(page.get("页面语义ID") or "") not in FAMILY_SEGMENT_SEMANTICS:
        return 0
    # Count the selected layout's explicit slots, never words in its copy.
    slots = page.get("case_slots")
    return len(slots) if isinstance(slots, list) else 0


def _semantic_bigrams(value: str) -> set[str]:
    cleaned = re.sub(r"[\s，。；：、＋+｜|／/（）()【】\[\]‘’“”\"'—_-]+", "", value)
    return {cleaned[index : index + 2] for index in range(max(len(cleaned) - 1, 0))}


def rank_portrait_assets(
    page: dict[str, Any], assets: Iterable[dict[str, Any]], limit: int = 6
) -> list[dict[str, Any]]:
    query = page_business_query(page)
    query_pairs = _semantic_bigrams(query)
    ranked: list[tuple[int, str, dict[str, Any]]] = []
    for asset in assets:
        if not is_audience_portrait(asset):
            continue
        text = asset_semantic_text(asset)
        overlap = len(query_pairs & _semantic_bigrams(text))
        marker_score = sum(3 for marker in PORTRAIT_MARKERS if marker in query and marker in text)
        score = overlap + marker_score
        ranked.append((score, str(asset.get("asset_id") or ""), asset))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [
        {
            "asset_id": str(asset.get("asset_id") or ""),
            "score": score,
            "effective_business_semantic": str(
                asset.get("effective_business_semantic") or ""
            ),
            "status": str(asset.get("status") or ""),
        }
        for score, _, asset in ranked[:limit]
    ]
