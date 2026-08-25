#!/usr/bin/env python3
"""检查中文业务文档中的否定式转折与不完整否定框架。

本工具只定位问题，不自动改写。语义完整性必须由编辑者根据上下文判断。
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rule:
    rule_id: str
    pattern: re.Pattern[str]
    guidance: str


RULES = (
    Rule(
        "topic-heading",
        re.compile(
            r"^#{1,6}\s+(?:[一二三四五六七八九十0-9]+[、.｜|\s]*)?"
            r"(?:一句话结论|核心结论|结论|[^。！？]{0,40}(?:分析|概览|综述|要求|方向|启示|机制|任务))$"
        ),
        "把话题标签改成包含主语、断言与机制或条件的action title，并执行so-what测试。",
    ),
    Rule(
        "negative-heading",
        re.compile(r"^#{1,6}\s+.*(?:不是|不能|不会|并非|没有|难以|无法|不按|不只|不仅|但|然而|却|虽然|可是)"),
        "标题必须写成完整机制断言，并通过 so-what 测试。",
    ),
    Rule(
        "negative-contrast",
        re.compile(r"(?:不是|并非|未必是)[^。；\n]{0,100}(?:而是|而应|而要|却是|而在于)"),
        "锁定后半句结论，改成肯定句；若前半句包含独立语义，用并列陈述保留。",
    ),
    Rule(
        "escalating-contrast",
        re.compile(r"(?:不只|不仅)[^。；\n]{0,100}(?:更|还|也)"),
        "直接陈述完整结果，避免用否定式递进搭桥。",
    ),
    Rule(
        "restriction-contrast",
        re.compile(r"(?:不能只|不可只)[^。；\n]{0,100}(?:而要|而应|还要|必须|需要)"),
        "改写为动作、条件或结果的肯定式组合。",
    ),
    Rule(
        "location-contrast",
        re.compile(r"不在[^。；\n]{0,100}而在(?:于)?"),
        "直接陈述真正成立的位置、原因或机制。",
    ),
    Rule(
        "transition-word",
        re.compile(r"(?:但|但是|然而|却|虽然|可是)"),
        "识别入场与胜出、条件与结果、基础与裁定等层次，用分层或分工句式重写。",
    ),
    Rule(
        "bare-negative",
        re.compile(r"(?:不是|不能|不会|并非|没有|难以|无法)"),
        "回答世界实际怎样、成立条件是什么或由谁完成裁定，用正向断言接住原否定语义。",
    ),
)


def load_allowlist(path: Path | None) -> tuple[str, ...]:
    if path is None:
        return ()
    phrases: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            phrases.append(line)
    return tuple(phrases)


def mask_allowed(text: str, allowlist: tuple[str, ...]) -> str:
    masked = text
    for phrase in allowlist:
        masked = masked.replace(phrase, "" if len(phrase) < 2 else "＿" * len(phrase))
    return masked


def scan_file(path: Path, allowlist: tuple[str, ...]) -> list[tuple[int, Rule, str]]:
    findings: list[tuple[int, Rule, str]] = []
    in_fence = False
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped:
            continue

        candidate = re.sub(r"`[^`]*`", "", raw)
        candidate = mask_allowed(candidate, allowlist)
        for rule in RULES:
            if rule.pattern.search(candidate):
                findings.append((line_no, rule, raw.strip()))
                break
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="检查中文业务文档中的否定式转折、否定式标题和程序化转场。"
    )
    parser.add_argument("paths", nargs="+", type=Path, help="待检查的 Markdown 或文本文件")
    parser.add_argument(
        "--allow-file",
        type=Path,
        help="已由用户裁定保留的完整短语，一行一条；仅屏蔽精确短语。",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="只输出诊断结果；即使命中也返回成功。适用于B/C级正文复核。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    allowlist = load_allowlist(args.allow_file)
    total = 0
    for path in args.paths:
        if not path.is_file():
            print(f"ERROR: 文件不存在：{path}", file=sys.stderr)
            return 2
        findings = scan_file(path, allowlist)
        total += len(findings)
        for line_no, rule, source in findings:
            print(f"{path}:{line_no}: [{rule.rule_id}] {source}")
            print(f"  建议：{rule.guidance}")

    if total:
        print(f"\n发现 {total} 处需进行肯定式语义复核。", file=sys.stderr)
        return 0 if args.report_only else 1
    print("肯定式表达检查通过：未发现命中项。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
