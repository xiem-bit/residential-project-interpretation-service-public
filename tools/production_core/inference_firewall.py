#!/usr/bin/env python3
"""Validate explicit evidence-to-claim links without keyword-based semantics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RELATIONSHIP_PATH = ROOT / "contracts" / "inference-relationships.json"
ALLOWED_DECISIONS = {"allowed_bounded", "allowed_with_bridge", "rejected"}


def load_relationships(path: Path = RELATIONSHIP_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("inference relationship table must be an object")
    return value


def relationship_index(table: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["id"]: item
        for item in table.get("relations", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def validate_inference_register(register: dict[str, Any], errors: list[str]) -> set[str]:
    try:
        table = load_relationships()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"inference relationship table: {exc}")
        return set()

    allowed_roles = set(table.get("evidence_roles") or [])
    relations = relationship_index(table)
    entries = {
        item.get("id"): item
        for item in register.get("entries") or []
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for entry_id, entry in entries.items():
        roles = entry.get("evidence_roles")
        if not isinstance(roles, list) or not roles:
            errors.append(f"fact-conflict-gap-register.json.entries.{entry_id}.evidence_roles: 至少一项")
            continue
        unknown_roles = set(roles) - allowed_roles
        if unknown_roles:
            errors.append(f"fact-conflict-gap-register.json.entries.{entry_id}.evidence_roles: 未知角色 {sorted(unknown_roles)}")

    link_ids: set[str] = set()
    links = register.get("inference_links")
    if not isinstance(links, list) or not links:
        errors.append("fact-conflict-gap-register.json.inference_links: 至少登记一条证据到主张的推导关系")
        return set()

    for index, link in enumerate(links):
        path = f"fact-conflict-gap-register.json.inference_links[{index}]"
        if not isinstance(link, dict):
            errors.append(f"{path}: 必须是对象")
            continue
        link_id = link.get("id")
        if not isinstance(link_id, str) or not link_id.strip():
            errors.append(f"{path}.id: 不能为空")
        elif link_id in link_ids:
            errors.append(f"{path}.id: 重复ID {link_id}")
        else:
            link_ids.add(link_id)

        relation = relations.get(link.get("relation_id"))
        if relation is None:
            errors.append(f"{path}.relation_id: 未知关系")
            continue
        source_refs = link.get("source_refs")
        if not isinstance(source_refs, list) or not source_refs:
            errors.append(f"{path}.source_refs: 至少一项")
            source_refs = []
        missing_sources = set(source_refs) - set(entries)
        if missing_sources:
            errors.append(f"{path}.source_refs: 无效引用 {sorted(missing_sources)}")
        source_roles = {
            role
            for ref in source_refs
            for role in (entries.get(ref, {}).get("evidence_roles") or [])
        }
        if not source_roles.intersection(relation.get("source_roles") or []):
            errors.append(f"{path}: 来源角色不满足{relation.get('id')}")

        target_level = link.get("target_level")
        permitted = set(relation.get("permitted_targets") or [])
        bridge_required = set(relation.get("bridge_required_targets") or [])
        prohibited = set(relation.get("prohibited_targets") or [])
        if target_level not in permitted | bridge_required | prohibited:
            errors.append(f"{path}.target_level: 不属于所选关系的允许、补桥或禁止目标")
        decision = link.get("decision")
        if decision not in ALLOWED_DECISIONS:
            errors.append(f"{path}.decision: 无效")
        if target_level in prohibited and decision != "rejected":
            errors.append(f"{path}: 禁止推导必须rejected")
        if target_level in permitted and decision not in {"allowed_bounded", "rejected"}:
            errors.append(f"{path}: 直接允许目标只能allowed_bounded或rejected")
        if target_level in bridge_required:
            bridge_refs = link.get("bridge_refs")
            if decision != "allowed_with_bridge":
                errors.append(f"{path}: 该目标必须allowed_with_bridge")
            if not isinstance(bridge_refs, list) or not bridge_refs:
                errors.append(f"{path}.bridge_refs: 补桥目标必须有额外证据")
            else:
                missing_bridges = set(bridge_refs) - set(entries)
                if missing_bridges:
                    errors.append(f"{path}.bridge_refs: 无效引用 {sorted(missing_bridges)}")
                valid_bridge_roles = {
                    role
                    for ref in bridge_refs
                    for role in (entries.get(ref, {}).get("evidence_roles") or [])
                }
                if valid_bridge_roles and valid_bridge_roles.issubset(set(relation.get("source_roles") or [])):
                    errors.append(f"{path}.bridge_refs: 不能只用同类高风险来源自我补桥")
        for field in ("target_claim", "boundary"):
            if not isinstance(link.get(field), str) or not link[field].strip():
                errors.append(f"{path}.{field}: 不能为空")
        if decision != "rejected" and (not isinstance(link.get("target_refs"), list) or not link["target_refs"]):
            errors.append(f"{path}.target_refs: 接受的推导必须登记去向")
    return link_ids


def evaluate_case(case: dict[str, Any], table: dict[str, Any] | None = None) -> str:
    """Return the expected machine decision for a compact regression case."""
    table = table or load_relationships()
    relation = relationship_index(table).get(case.get("relation_id"), {})
    target = case.get("target_level")
    if target in set(relation.get("prohibited_targets") or []):
        return "rejected"
    if target in set(relation.get("bridge_required_targets") or []):
        return "allowed_with_bridge" if case.get("has_independent_bridge") is True else "rejected"
    if target in set(relation.get("permitted_targets") or []):
        return "allowed_bounded"
    return "rejected"
