#!/usr/bin/env python3
"""产物3正式生产的客户前台与素材业务门禁。"""

from __future__ import annotations

import re
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


def internal_method_hits(page: dict[str, Any]) -> list[str]:
    text = visible_text(page)
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
