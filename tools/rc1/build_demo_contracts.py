#!/usr/bin/env python3
"""Build deterministic public contracts from the approved fictional semantic core."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


VISUAL_SOURCE_POLICY = {
    "allowed": [
        "semantic_company_case_library",
        "system_made_map_or_data_chart",
        "system_made_logic_diagram",
        "semantically_reviewed_generated_visual",
        "client_render_derivative_only_after_separate_authorization_and_local_render_owner",
    ],
    "prohibited": [
        "raw_client_pdf_screenshot",
        "raw_client_wechat_image",
        "raw_client_proposal_screenshot",
        "cropped_recolored_masked_recaptioned_or_lightly_redrawn_client_original",
    ],
    "client_material_usage": "internal_understanding_fact_extraction_visual_reference_and_search_index_only",
    "client_render_derivative_default": "off",
    "required_asset_registry_fields": [
        "source_type",
        "asset_identity",
        "business_semantics",
        "proof_purpose",
        "page_destination",
    ],
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _chapter2_dimension(dimension: dict[str, Any]) -> dict[str, Any]:
    result = {
        "id": dimension["id"],
        "name": dimension["name"],
        "order": dimension["order"],
        "customer_question": dimension["customer_question"],
        "customer_decision_refs": copy.deepcopy(dimension["customer_decision_refs"]),
        "comparison_factors": copy.deepcopy(dimension["comparison_factors"]),
        "advantage_column_id": dimension["advantage_column_id"],
        "map": copy.deepcopy(dimension["map"]),
        "subject": {"id": "SUBJECT", "strengths": copy.deepcopy(dimension["subject_strengths"])},
        "competitors": copy.deepcopy(dimension["competitors"]),
        "conclusions": copy.deepcopy(dimension["conclusions"]),
    }
    result["map"]["competitor_ids"] = [item["id"] for item in dimension["competitors"]]
    result["map"].setdefault("spatial_annotations", ["合成示例只表达相对关系，不提供真实地图结论"])
    result["map"].setdefault("supporting_visual_assets", [])
    return result


def build_chapter2(core: dict[str, Any]) -> dict[str, Any]:
    columns = []
    for dimension in core["dimensions"]:
        columns.append(
            {
                "id": dimension["advantage_column_id"],
                "label": f"{dimension['name']}优势",
                "items": copy.deepcopy(dimension["advantages"]),
                "super_competitiveness": {
                    key: copy.deepcopy(value)
                    for key, value in dimension["super_competitiveness"].items()
                    if key
                    in {
                        "id",
                        "text",
                        "range",
                        "super_trait",
                        "form",
                        "bounded_superlative",
                    }
                },
            }
        )
        columns[-1]["super_competitiveness"]["advantage_item_refs"] = [
            item["id"] for item in dimension["advantages"]
        ]

    super_ids = [item["super_competitiveness"]["id"] for item in core["dimensions"]]
    return {
        "meta": {
            "project_id": core["project"]["id"],
            "status": "final",
            "main_consumption_contract": "contracts/住宅竞争力方法与生产合同.md",
            "super_competitiveness_requirement": {
                "minimum": 3,
                "maximum": 4,
                "high_cost_admission": "all_established_and_internally_validated",
            },
            "chapter_structure": {
                "template_chapters": [1, 4],
                "project_generated_chapters": [2, 3],
            },
            "dimension_plan": {"default_order_used": True, "change_reason": ""},
            "fixture_notice": core["fixture_notice"],
        },
        "visual_source_policy": copy.deepcopy(VISUAL_SOURCE_POLICY),
        "evidence_registry": copy.deepcopy(core["evidence_registry"]),
        "customer_decision_registry": copy.deepcopy(core["customer_decisions"]),
        "chapter2": {
            "communication_outcomes": [
                "甲方认可本案真实竞争局面已经被准确理解",
                "甲方认可价值锚点与本案超级竞争力来自同口径比较",
            ],
            "candidate_and_substitute_relations": {
                "visible_claim": "客户在成熟通勤、低密体验与继续等待之间比较，再决定青岚澄境是否进入下一步",
                "relations": copy.deepcopy(core["relations"]),
            },
            "dimensions": [_chapter2_dimension(item) for item in core["dimensions"]],
            "advantage_matrix": {"columns": columns},
            "value_anchor": copy.deepcopy(core["value_anchor"]),
            "display_strategy": copy.deepcopy(core["display_strategy"]),
            "handoff_to_chapter3": {
                "value_anchor_ref": "VALUE-ANCHOR",
                "value_anchor_usage": "textual_recap_only",
                "value_anchor_visualization_service": False,
                "super_competitiveness_refs": super_ids,
                "display_strategy_usage": "internal_creative_brief",
                "required_chapter3_contract": "chapter3-contract.json",
                "required_bridge_validator": "tools/product3_chapter23/validate_chapter23_bridge.py",
            },
        },
    }


def build_chapter3(core: dict[str, Any]) -> dict[str, Any]:
    sections = []
    for index, dimension in enumerate(core["dimensions"], start=1):
        sc = dimension["super_competitiveness"]
        sections.append(
            {
                "source_ref": sc["id"],
                "text": sc["text"],
                "bounded_superlative": copy.deepcopy(sc["bounded_superlative"]),
                "customer_gain": sc["customer_gain"],
                "project_fact_refs": copy.deepcopy(sc["evidence_refs"]),
                "competition_relation_refs": copy.deepcopy(sc["relation_refs"]),
                "customer_question_refs": copy.deepcopy(sc["customer_decision_refs"]),
                "ue_scenes": [copy.deepcopy(sc["scene"])],
                "case_slots": [
                    {
                        "id": f"CASE-SC{index}-01",
                        "purpose": "系统制作的逻辑图证明本条关系",
                        "status": "fictional_system_visual_only",
                    },
                    {
                        "id": f"CASE-SC{index}-02",
                        "purpose": "平台生成的合成示意补充家庭使用情境",
                        "status": "platform_adapter_required",
                    },
                ],
            }
        )

    return {
        "meta": {
            "project_id": core["project"]["id"],
            "status": "final",
            "main_consumption_contract": "contracts/住宅竞争力方法与生产合同.md",
            "super_competitiveness_requirement": {
                "minimum": 3,
                "maximum": 4,
                "high_cost_admission": "all_established_and_internally_validated",
            },
            "source_chapter2_contract": "chapter2-contract.json",
            "visible_copy_mode": "client_marketing_team",
            "value_anchor_visualization_service": False,
            "fixture_notice": core["fixture_notice"],
        },
        "visual_source_policy": copy.deepcopy(VISUAL_SOURCE_POLICY),
        "chapter3": {
            "value_anchor": {
                "source_ref": "VALUE-ANCHOR",
                "text": core["value_anchor"]["text"],
                "usage": "textual_recap_only",
                "scene_id": "COMMON-01",
            },
            "common_project_answer": {
                "visible_claim": core["common_project_answer"],
                "super_competitiveness_sections": sections,
                "closing_scene": {
                    "id": "COMMON-CLOSE-01",
                    "visible_claim": core["common_project_answer"],
                    "product5_target": "view-overview",
                },
            },
            "family_routes": copy.deepcopy(core["family_routes"]),
            "system_modules": copy.deepcopy(core["system_modules"]),
            "system_scope_close": copy.deepcopy(core["system_scope_close"]),
        },
    }


def build_presentation_request(core: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "residential.presentation_request.v0.1",
        "project_id": core["project"]["id"],
        "fixture_notice": core["fixture_notice"],
        "semantic_core": {
            "status": core["status"],
            "value_anchor": core["value_anchor"]["text"],
            "super_competitiveness_ids": [
                item["super_competitiveness"]["id"] for item in core["dimensions"]
            ],
        },
        "artifact_requirements": {
            "format": "pptx",
            "editable": True,
            "formal_visual_generation_owner": "platform_adapter",
            "page_size": "16:9",
            "language": "zh-CN",
            "preview_required_for_formal_delivery": True,
            "page_object_mapping_required": True,
        },
        "pages": copy.deepcopy(core["presentation_pages"]),
        "prohibited_content": [
            "real customer or project assets",
            "client source screenshots",
            "unverified school price delivery or transit promises",
            "absolute local paths credentials internal domains and publication profiles",
        ],
        "return_requirements": [
            "editable_artifact",
            "page_mapping",
            "object_mapping",
            "page_preview_or_equivalent_visual_evidence",
            "qa_evidence",
            "explicit_gaps",
        ],
        "gap_policy": {
            "unsupported_capability": "return status=gap with no fabricated artifact",
            "semantic_change": "reject; platform must preserve project page and super-competitiveness IDs",
            "formal_visual_not_reviewed": "return FORMAL_VISUAL_REVIEW_REQUIRED",
        },
    }


def build_product5_config(core: dict[str, Any], gaps: dict[str, Any]) -> dict[str, Any]:
    template_text = (ROOT / "tools/product5_shell/public/project-data.js").read_text(encoding="utf-8")
    template_payload = template_text.split("=", 1)[1].strip().removesuffix(";")
    template = json.loads(template_payload)
    return {
        "schema": "residential.product5_config.v0.1",
        "project": {
            "id": core["project"]["id"],
            "name": core["project"]["name"],
            "city": core["project"]["city"],
            "district": core["project"]["district"],
            "fixture_notice": core["fixture_notice"],
        },
        "value_anchor": core["value_anchor"]["text"],
        "super_competitiveness": [
            {
                "id": item["super_competitiveness"]["id"],
                "title": item["super_competitiveness"]["scene"]["visible_title"],
                "claim": item["super_competitiveness"]["text"],
                "customer_gain": item["super_competitiveness"]["customer_gain"],
                "target": item["super_competitiveness"]["scene"]["product5_target"],
            }
            for item in core["dimensions"]
        ],
        "family_routes": copy.deepcopy(core["family_routes"]),
        "modules": copy.deepcopy(core["system_modules"]),
        "evidence_gaps": copy.deepcopy(gaps["gaps"]),
        "navigation": [
            {"id": "overview", "label": "项目总览"},
            {"id": "competitiveness", "label": "三项选择价值"},
            {"id": "family", "label": "家庭路线"},
            {"id": "gaps", "label": "事实边界"},
        ],
        "mobile_path": "m/index.html",
        "publication_state": "not_published",
        "experience": copy.deepcopy(template["experience"]),
    }


def build_all(core_path: Path, gaps_path: Path, output_dir: Path) -> dict[str, Path]:
    core = load_json(core_path)
    gaps = load_json(gaps_path)
    outputs = {
        "chapter2": output_dir / "chapter2-contract.json",
        "chapter3": output_dir / "chapter3-contract.json",
        "presentation_request": output_dir / "presentation-request.json",
        "product5_config": output_dir / "product5-config.json",
    }
    write_json(outputs["chapter2"], build_chapter2(core))
    write_json(outputs["chapter3"], build_chapter3(core))
    write_json(outputs["presentation_request"], build_presentation_request(core))
    write_json(outputs["product5_config"], build_product5_config(core, gaps))
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--gaps", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    outputs = build_all(args.core.resolve(), args.gaps.resolve(), args.out.resolve())
    for label, path in outputs.items():
        print(f"{label}: {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
