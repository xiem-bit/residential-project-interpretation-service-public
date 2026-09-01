#!/usr/bin/env python3
"""First-pass audit for Chinese business/research report prose.

This script is intentionally conservative. It locates likely readability issues;
the Codex skill remains responsible for editorial judgment.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


SENTENCE_SPLIT = re.compile(r"(?<=[。！？!?；;])")
CHINESE_CHAR = re.compile(r"[\u4e00-\u9fff]")

INTERNAL_TERMS = [
    "可填回答",
    "集团问题",
    "输出契约",
    "验证层级",
    "工程化规则",
    "schema",
    "fixture",
    "prompt",
    "lint",
    "AI 味",
    "人机对话",
    "知识库摄入",
    "规则引擎",
]

PRODUCT_LIKE_TERMS = [
    "主板四套",
    "云链",
    "渠道风控",
    "智能工牌",
    "智能话机",
    "智能收款",
    "AI 云店",
    "广告",
    "数字展厅",
    "营销服务",
    "代运营",
    "视频营销",
    "Agent",
    "客研",
    "风控",
    "工牌",
    "话机",
]


def chinese_len(text: str) -> int:
    return len(CHINESE_CHAR.findall(text))


def iter_sentences(line: str):
    parts = [p.strip() for p in SENTENCE_SPLIT.split(line) if p.strip()]
    for part in parts:
        yield part


def short(text: str, limit: int = 110) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def non_overlapping_hits(terms: list[str], sentence: str) -> list[str]:
    hits: list[str] = []
    for term in sorted(terms, key=len, reverse=True):
        if term not in sentence:
            continue
        if any(term in existing for existing in hits):
            continue
        hits.append(term)
    return sorted(hits, key=lambda item: sentence.find(item))


def audit_line(line_no: int, line: str):
    stripped = line.strip()
    if not stripped or stripped.startswith("```"):
        return

    if stripped.startswith("|"):
        return

    for sentence in iter_sentences(stripped):
        clen = chinese_len(sentence)
        dunhao_count = sentence.count("、")
        comma_count = sentence.count("，")
        slash_count = sentence.count("/")
        product_hits = non_overlapping_hits(PRODUCT_LIKE_TERMS, sentence)
        internal_hits = [term for term in INTERNAL_TERMS if term in sentence]

        if clen >= 90:
            yield ("长句过载", "high", line_no, f"{clen} 个中文字符", sentence)
        elif clen >= 70:
            yield ("长句偏长", "medium", line_no, f"{clen} 个中文字符", sentence)

        if dunhao_count >= 5:
            yield ("顿号过载", "high", line_no, f"{dunhao_count} 个顿号", sentence)
        elif dunhao_count >= 3:
            yield ("顿号偏多", "medium", line_no, f"{dunhao_count} 个顿号", sentence)

        if comma_count >= 5 and clen >= 55:
            yield ("逗号链条过长", "medium", line_no, f"{comma_count} 个逗号", sentence)

        if slash_count >= 3:
            yield ("斜杠并列过多", "medium", line_no, f"{slash_count} 个斜杠", sentence)

        if len(product_hits) >= 5:
            yield (
                "产品名堆叠",
                "medium",
                line_no,
                "、".join(product_hits),
                sentence,
            )

        if internal_hits:
            yield (
                "内部/工程化词汇",
                "high",
                line_no,
                "、".join(internal_hits),
                sentence,
            )

        if "：" in sentence or ":" in sentence:
            if not re.match(r"^\s*\|", sentence):
                yield ("冒号脚手架", "low", line_no, "含冒号", sentence)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Markdown or text file to audit")
    parser.add_argument("--max", type=int, default=80, help="maximum findings")
    args = parser.parse_args()

    path = Path(args.file).expanduser()
    if not path.exists():
        raise SystemExit(f"file not found: {path}")

    findings = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        findings.extend(audit_line(line_no, line) or [])

    print(f"# 中文研究报告文本质检")
    print()
    print(f"- 文件: {path}")
    print(f"- 发现: {len(findings)} 条候选问题")
    print()

    for idx, (kind, severity, line_no, detail, sentence) in enumerate(findings[: args.max], 1):
        print(f"## {idx}. {kind} [{severity}]")
        print()
        print(f"- 行号: {line_no}")
        print(f"- 细节: {detail}")
        print(f"- 原句: {short(sentence)}")
        print()

    if len(findings) > args.max:
        print(f"... 已截断，仍有 {len(findings) - args.max} 条未显示")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
