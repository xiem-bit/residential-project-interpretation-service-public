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

from business_gates import is_audience_portrait, rank_portrait_assets  # noqa: E402
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
        self.assertIn("相邻页复用同一页面语义", joined)
        self.assertIn("需要3张按业务语义匹配的肖像图", joined)
        self.assertEqual(evidence["family_asset_selection"][0]["result"], "generation_required")

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
