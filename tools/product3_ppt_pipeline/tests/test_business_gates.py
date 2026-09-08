from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PIPELINE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PIPELINE_DIR.parents[1]
sys.path.insert(0, str(PIPELINE_DIR))

from business_gates import is_audience_portrait, rank_portrait_assets, required_portrait_count, chapter2_basis, changed_basis_review, internal_method_hits, locked_quote_errors  # noqa: E402
from validate_production_input import validate_payload  # noqa: E402
sys.path.insert(0, str(PROJECT_ROOT / "tools/product3_assembly_console/scripts"))
from export_approved_blueprint import build_payload, markdown  # noqa: E402


SEMANTIC_DATASET = json.loads(
    (PROJECT_ROOT / "references/product3/assets/产物3页面模板库/datasets/page_semantic_dataset.v0.3.json").read_text(
        encoding="utf-8"
    )
)
SOURCE_DATASET = json.loads(
    (PROJECT_ROOT / "references/product3/assets/产物3页面模板库/datasets/source_page_semantic_annotations.v0.3.json").read_text(
        encoding="utf-8"
    )
)


def page(
    order: int,
    page_id: str,
    name: str,
    copy: str,
    semantic_id: str,
    source_id: str,
    visual: str,
) -> dict[str, object]:
    return {
        "页序": order,
        "页面ID": page_id,
        "页面名称": name,
        "页面文案": copy,
        "这一页只负责": name,
        "演讲动作": "指出关系 → 解释客户获得 → 回收项目判断。",
        "转场": "进入下一页。",
        "视觉结构": visual,
        "页面语义ID": semantic_id,
        "来源页ID": source_id,
        "视觉参考页ID": source_id,
        "视觉变体ID": "",
        "素材编号": "",
        "裁定状态": "approved",
        "进入PPT生产": True,
        "装配动作": "recompose_by_semantic",
    }


class BusinessGateTests(unittest.TestCase):
    def test_cross_project_contamination_failure_modes_are_blocked(self) -> None:
        pages = [
            page(
                1,
                "P3-TEST-001",
                "当前项目把成熟生活转成家庭换新的直接进步",
                "当前项目承接既有生活半径，让家庭在熟悉日常中完成居住升级。",
                "P3-VALUE-ANCHOR",
                "GT-08",
                "一句价值锚点＋三条当前项目支撑",
            ),
            page(
                2,
                "P3-TEST-002",
                "家庭一日路径把生活连续转成改善收益",
                "接送、通勤、购物与归家保持连续，新增空间完成居住升级。",
                "P3-SC-PROOF",
                "QJ-13",
                "标题与聚焦说明＋上方递进卡＋下方案例参考",
            ),
            page(
                3,
                "P3-TEST-003",
                "得到与代价进入同一价值账，原地改善形成净进步",
                "调整家庭优先级，把四种选择放进同一价值账重新排序。",
                "P3-SC-PROOF",
                "QJ-13",
                "标题与聚焦说明＋上方递进卡＋下方案例参考",
            ),
            page(
                4,
                "P3-TEST-004",
                "三类换新家庭找到各自的产品入口",
                "三类家庭从熟悉生活、空间变化与长期品质判断进入不同产品内容。",
                "P3-FAMILY-SEGMENT",
                "GT-16",
                "三类家庭肖像＋家庭任务＋产品入口",
            ),
        ]
        pages[-1]["case_slots"] = [{"id": f"person-{i}", "asset_id": "", "purpose": "家庭角色"} for i in range(3)]
        payload = {
            "schema": "product3.assembly_blueprint.v0.1",
            "export_status": "approved_for_ppt_production",
            "fixture_only": False,
            "project_id": "P3-TEST-CROSS-PROJECT",
            "project_name": "跨项目污染回归夹具",
            "assembly_version": "test-business-gates",
            "page_count": len(pages),
            "pages": pages,
        }
        errors, evidence = validate_payload(
            payload, SEMANTIC_DATASET, SOURCE_DATASET, [], allow_test_fixture=False
        )
        joined = "\n".join(errors)
        self.assertIn("价值账", joined)
        self.assertNotIn("相邻页复用同一页面语义", joined)
        self.assertIn("需要3张按业务语义匹配的肖像图", joined)
        self.assertEqual(evidence["family_asset_selection"][0]["result"], "generation_required")

    def test_continuous_maps_do_not_use_layout_or_filename_as_duplicate_verdict(self):
        from copy import deepcopy
        from validate_production_input import parse_asset_bindings
        for binding in ("", None, [], "[]", '{"proof": []}', {"proof": []}):
            self.assertEqual(parse_asset_bindings(binding), ([], None))
            for different_map in (False, True):
                pages = [page(i, f"MAP-{i}", "工作与生活联系", "两处工作安排需要同时兼顾。", "P3-COMPETITION-MAP", "", "全屏地图与两侧卡片") for i in (1, 2)]
                for i, record in enumerate(pages):
                    record["素材编号"] = binding
                    record["视觉变体ID"] = "MAP-OSM-STANDARD"
                    record["视觉参考页ID"] = "当前认可地图版式"
                    record["本项目图形"] = [f"MAP-{i if different_map else 0}"]
                for different_copy in (False, True):
                    sample = deepcopy(pages)
                    if different_copy:
                        sample[1]["页面文案"] = "现有接送安排在南侧，换房仍需保留这段联系。"
                    payload = {"schema": "product3.assembly_blueprint.v0.1", "export_status": "approved_for_ppt_production", "fixture_only": False, "project_id": "MAP-TEST", "project_name": "局部检查", "assembly_version": "maps", "page_count": 2, "pages": sample}
                    errors, _ = validate_payload(payload, SEMANTIC_DATASET, SOURCE_DATASET, [], False)
                    self.assertEqual(errors, [])

    def test_family_slots_are_required_and_bound_to_real_portrait_assets(self):
        record = page(1, "FAMILY", "三类家庭", "各有实际生活安排。", "P3-FAMILY-SEGMENT", "", "已选两个人物版位")
        payload = {"schema": "product3.assembly_blueprint.v0.1", "export_status": "approved_for_ppt_production", "fixture_only": False, "project_id": "FAMILY-TEST", "project_name": "局部检查", "assembly_version": "family", "page_count": 1, "pages": [record]}
        errors, _ = validate_payload(payload, SEMANTIC_DATASET, SOURCE_DATASET, [], False)
        self.assertTrue(any("家庭总览必须" in error for error in errors))
        record["case_slots"] = [{"id": f"portrait-{i}", "asset_id": f"CASE-{i}", "purpose": "家庭角色"} for i in range(2)]
        self.assertEqual(required_portrait_count(record), 2)  # 不由“三类家庭”猜数量
        record["素材编号"] = {"proof": ["CASE-0", "CASE-1"]}
        assets = [{"asset_id": f"CASE-{i}", "asset_class": "audience_portrait", "effective_business_semantic": "家庭人物肖像", "original_asset": f"portrait-{i}.png", "status": "approved"} for i in range(2)]
        with tempfile.TemporaryDirectory() as folder:
            for i in range(2):
                file = Path(folder) / f"portrait-{i}.png"
                file.write_bytes(bytes([i]))
                assets[i]["original_asset"] = str(file)
            errors, evidence = validate_payload(payload, SEMANTIC_DATASET, SOURCE_DATASET, assets, False)
            self.assertEqual(errors, [])
            self.assertEqual(evidence["family_asset_selection"][0]["result"], "bound")
            assets[1]["asset_class"] = "case_reference"
            errors, _ = validate_payload(payload, SEMANTIC_DATASET, SOURCE_DATASET, assets, False)
            self.assertTrue(any("需要2张" in error for error in errors))
            assets[1]["asset_class"] = "audience_portrait"
            record["case_slots"][1]["asset_id"] = "CASE-0"
            errors, _ = validate_payload(payload, SEMANTIC_DATASET, SOURCE_DATASET, assets, False)
            self.assertTrue(any("需要2张" in error for error in errors))

    def test_portrait_routing_uses_semantics_not_any_person_image(self) -> None:
        assets = [
            {
                "asset_id": "CASE-TEAM",
                "effective_business_semantic": "设计团队人物与机构背书",
                "asset_class": "case_reference",
            },
            {
                "asset_id": "CASE-FAMILY",
                "effective_business_semantic": "年轻夫妻与亲子家庭肖像，表达换新家庭角色",
                "asset_class": "audience_portrait",
            },
        ]
        self.assertFalse(is_audience_portrait(assets[0]))
        self.assertTrue(is_audience_portrait(assets[1]))
        ranked = rank_portrait_assets(
            {
                "页面名称": "年轻夫妻换新家庭",
                "页面文案": "亲子家庭在成熟生活圈内完成居住升级",
                "这一页只负责": "识别换新家庭角色",
                "视觉结构": "家庭肖像卡",
            },
            assets,
        )
        self.assertEqual([item["asset_id"] for item in ranked], ["CASE-FAMILY"])

    def test_formal_plan_never_uses_whole_source_slide_route(self) -> None:
        payload = {
            "schema": "product3.assembly_blueprint.v0.1",
            "export_status": "approved_for_ppt_production",
            "fixture_only": False,
            "project_id": "P3-TEST-PLAN",
            "project_name": "正式项目",
            "assembly_version": "test-route",
            "page_count": 1,
            "pages": [
                page(
                    1,
                    "P3-TEST-PLAN-001",
                    "当前项目价值锚点",
                    "当前项目以自己的事实、竞争关系和家庭收益形成价值锚点。",
                    "P3-VALUE-ANCHOR",
                    "GT-08",
                    "一句价值锚点＋三条当前项目支撑",
                )
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blueprint = root / "blueprint.json"
            output = root / "plan.json"
            blueprint.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            subprocess.run(
                [
                    sys.executable,
                    str(PIPELINE_DIR / "plan_production.py"),
                    str(blueprint),
                    "--out",
                    str(output),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            plan = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(
            plan["pages"][0]["production_route"], "reuse_structure_rewrite_copy"
        )
        self.assertEqual(
            plan["pages"][0]["source_reuse_boundary"],
            "structure_only_current_project_copy_required",
        )

    def test_export_and_plan_preserve_ue_relationships_in_existing_fields(self) -> None:
        record = page(
            1, "P3-TEST-REFS", "项目展示范围", "区域与项目内容共同承接本轮讲解。",
            "P3-UE-BLUEPRINT", "", "系统内容关系图",
        )
        record.update({
            "有效": True, "grist_row_id": 1, "项目ID": "TEST-REFS",
            "项目名称": "内部接口检查", "装配版本": "test-refs",
            "这一页只负责": "解释采购范围；第三章合同#SC-PLANNING；UE-PAGE-REGION、UE-PAGE-GARDEN",
            "视觉结构": "共用ITEM-REGION与ITEM-GARDEN；底图定位，面板解释取舍",
            "演讲动作": "ROUTE-01详讲固定目的地；ROUTE-02详讲区域生活；共用页序",
        })
        payload = build_payload([record], is_draft=False)
        exported_text = markdown(payload)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "blueprint.json"
            target = root / "plan.json"
            source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            subprocess.run(
                [sys.executable, str(PIPELINE_DIR / "plan_production.py"), str(source), "--out", str(target)],
                cwd=PROJECT_ROOT, check=True, capture_output=True, text=True,
            )
            output = json.loads(target.read_text(encoding="utf-8"))["pages"][0]
        for original, derived in (("这一页只负责", "responsibility"), ("视觉结构", "visual_structure"), ("演讲动作", "speaking_action")):
            self.assertEqual(output[derived], record[original])
            self.assertIn(record[original], exported_text)
        self.assertEqual(output["visible_copy"], record["页面文案"])
        self.assertNotIn("UE-PAGE", output["visible_copy"])


class ContinuationRegressionTests(unittest.TestCase):
    def test_exact_identified_quote_is_preserved_but_own_method_sentence_is_not_exempt(self):
        quoted = page(1, "QUOTE", "购房者怎样做选择", "原文标题：《四个WHY选房记》。这位作者最后选择保留原有通勤。", "P3-CUSTOMER-CHOICE", "", "原声")
        self.assertTrue(internal_method_hits(quoted))  # 引号不是身份
        quoted["原文引文"] = [{"field": "页面文案", "text": "《四个WHY选房记》", "source": "原作者文章标题，归档原文第1行", "purpose": "辨认所引选择事件"}]
        original = quoted["页面文案"]
        self.assertEqual(locked_quote_errors(quoted), [])
        self.assertEqual(internal_method_hits(quoted), [])
        self.assertEqual(quoted["页面文案"], original)
        quoted["页面名称"] = "用四个WHY重排家庭优先级"
        self.assertTrue(internal_method_hits(quoted))
        quoted["原文引文"][0]["source"] = ""
        self.assertTrue(locked_quote_errors(quoted))
        self.assertTrue(internal_method_hits(quoted))

    def test_fact_change_returns_only_dependent_pages_to_existing_export_review(self):
        from copy import deepcopy
        contract = {"chapter2": {"dimensions": [{"subject": {"strengths": [{"id": "FACT-UNIT", "text": "住宅采用环幕公区", "factor_id": "采光", "evidence_refs": ["E-PLAN"]}]}, "conclusions": [{"id": "CON-UNIT", "fact_refs": ["FACT-UNIT"]}]}], "advantage_matrix": {"columns": [{"items": [{"id": "ADV-UNIT", "conclusion_refs": ["CON-UNIT"]}], "super_competitiveness": {"id": "SC-UNIT", "advantage_item_refs": ["ADV-UNIT"]}}]}}}
        records = [page(i, name, title, "现有正文", "P3-SC-PROOF", "", "内容页") for i, name, title in [(1, "PAGE-UNIT", "室内天光"), (2, "PAGE-CITY", "城市联系")]]
        for record, role in zip(records, ["SC-UNIT", "SC-CITY"]):
            record.update({"有效": True, "项目ID": "CHANGE-TEST", "项目名称": "离线订正对照", "装配版本": "test", "上游冻结状态": "frozen", "这一页只负责": role})
        payload = build_payload(records, False)
        payload["reviewed_chapter2_basis"] = chapter2_basis(contract)
        wrapped = deepcopy(contract)
        wrapped["chapter2"]["dimensions"][0]["subject"]["strengths"][0]["text"] = "住宅采用\n环幕公区"
        self.assertEqual(changed_basis_review(payload, wrapped)["changed_facts"], [])
        changed = deepcopy(contract)
        changed["chapter2"]["dimensions"][0]["subject"]["strengths"][0]["text"] = "原环幕公区方案已取消"
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            basis_path, source = root / "chapter2.json", root / "approved.json"
            payload["chapter2_contract_path"] = str(basis_path)
            source.write_text(json.dumps(payload, ensure_ascii=False))
            before = source.read_bytes()
            basis_path.write_text(json.dumps(changed, ensure_ascii=False))
            result = subprocess.run([sys.executable, str(PROJECT_ROOT / "tools/product3_assembly_console/scripts/export_approved_blueprint.py"), str(source), "--out-dir", str(root / "review")], cwd=PROJECT_ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            draft = json.loads((root / "review/draft_装配清单.json").read_text())
            self.assertEqual(draft["pages"][0]["裁定状态"], "draft")
            self.assertFalse(draft["pages"][0]["进入PPT生产"])
            self.assertIn("FACT-UNIT", draft["pages"][0]["裁定说明"])
            self.assertEqual(draft["pages"][1]["裁定状态"], "approved")
            self.assertEqual(source.read_bytes(), before)  # 已交付快照不被覆盖
            self.assertFalse((root / "review/approved_装配清单.json").exists())
            # 单纯换行和同用途换图继续通过当前导出，不把局部操作升级为研究。
            basis_path.write_text(json.dumps(wrapped, ensure_ascii=False))
            payload["pages"][0]["素材编号"] = ["CASE-REPLACEMENT"]
            source.write_text(json.dumps(payload, ensure_ascii=False))
            result = subprocess.run([sys.executable, str(PROJECT_ROOT / "tools/product3_assembly_console/scripts/export_approved_blueprint.py"), str(source), "--out-dir", str(root / "layout-only")], cwd=PROJECT_ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_live_asset_check_is_limited_to_used_shared_material(self):
        from copy import deepcopy
        from unittest.mock import patch
        import build_case_asset_inventory as inventory
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shared_path, project_path = root / "shared.json", root / "project/snapshot.json"
            project_path.parent.mkdir()
            assets = [
                {"asset_id": "CASE-USED", "original_asset": str(root / "original/used.png"), "status": "approved", "asset_class": "case_reference", "effective_business_semantic": "厅堂空间"},
                {"asset_id": "CASE-UNUSED", "original_asset": str(root / "original/unused.png"), "status": "approved", "asset_class": "case_reference", "effective_business_semantic": "建筑空间"},
                {"asset_id": "CASE-PROJECT", "original_asset": str(root / "project/portrait.png"), "status": "approved", "asset_class": "audience_portrait", "effective_business_semantic": "一家人在住宅中使用空间"},
            ]
            project_path.write_text(json.dumps(assets))
            original = project_path.read_bytes()
            with patch.object(inventory, "DEFAULT_OUTPUT", shared_path), patch.object(inventory, "DEFAULT_ORIGINAL_DIR", root / "original"):
                shared_path.write_text(json.dumps(assets[:2]))
                current = inventory.load_current_inventory(project_path, {"CASE-USED", "CASE-PROJECT"})
                self.assertTrue(all("current_inventory_difference" not in x for x in current))
                changed = deepcopy(assets[:2]); changed[0]["effective_business_semantic"] = "仅能说明立面材质"
                changed[1]["status"] = "disabled"
                shared_path.write_text(json.dumps(changed))
                current = inventory.load_current_inventory(project_path, {"CASE-USED", "CASE-PROJECT"})
                self.assertIn("订正", current[0]["current_inventory_difference"])
                self.assertNotIn("current_inventory_difference", current[1])  # 未使用，不增加工作
                self.assertNotIn("current_inventory_difference", current[2])  # 项目新增保持
                changed[0]["status"] = "disabled"
                shared_path.write_text(json.dumps(changed))
                self.assertIn("退出", inventory.load_current_inventory(project_path, {"CASE-USED"})[0]["current_inventory_difference"])
                self.assertEqual(project_path.read_bytes(), original)


class ActualCopyRoundtripTest(unittest.TestCase):
    def test_reads_subtitle_footer_but_not_notes_and_detects_copy_change(self):
        from zipfile import ZipFile
        from verify_production import read_visible_copy, copy_errors
        from xml.sax.saxutils import escape
        page = {"page_id":"P1", "render_content":{}, "visible_copy":"本案判断\n超过原定预算\n案例不代表本案配置"}
        page["render_content"] = {"layout":"gallery"}
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp)/"actual.pptx"
            shapes = "".join(f'<p:sp><p:nvSpPr><p:cNvPr name="P1-{role}"/></p:nvSpPr><p:txBody><a:p><a:r><a:t>{escape(text)}</a:t></a:r></a:p></p:txBody></p:sp>' for role,text in [("title","本案判断"),("subtitle","超过原定预算"),("footer","案例不代表本案配置"),("page_number","1 / 1")])
            with ZipFile(file,"w") as z:
                z.writestr("ppt/slides/slide1.xml",'<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'+shapes+'</p:sld>')
                z.writestr("ppt/notesSlides/notesSlide1.xml","内部：后续资料装载与制作安排")
            records = read_visible_copy(file,[page])
        self.assertEqual(len(records),4)
        self.assertEqual(copy_errors([page],records),[])
        records[1]["text"]="没有购买能力"
        self.assertTrue(copy_errors([page],records))
        records[1]["text"]="超过原定\n预算"
        self.assertEqual(copy_errors([page],records),[])
        records.append({"page":1,"page_id":"P1","role":"generated-note","text":"待图纸确认后深化"})
        self.assertTrue(copy_errors([page],records))


if __name__ == "__main__":
    unittest.main()
