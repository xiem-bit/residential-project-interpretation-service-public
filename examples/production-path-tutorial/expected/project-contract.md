# 青岚澄境完整生产路径教程任务合同

```json
{
  "schema": "residential.project_contract.v0.2",
  "task_id": "TUTORIAL-QC-001",
  "mode": "tutorial",
  "business_question": "青岚澄境面对什么真实替代，怎样形成三条能够进入候选、赢得比较并促进行动的竞争武器，并落到住宅UE售前方案",
  "primary_audience": "虚构甲方营销与销售团队",
  "use_case": "住宅UE售前提案的业务输入",
  "business_stage": "prelaunch_presales",
  "project": {
    "id": "fictional-qinglan-chengjing-production",
    "canonical_name": "青岚澄境（全量虚构）",
    "aliases": [],
    "city": "澄川市（虚构）",
    "district_or_area": "青岚新区东岸生活带（虚构）",
    "location": "东岸生活带单一整体项目，不含其他分期（虚构）",
    "developer": "澄川青岚置业有限公司（虚构）",
    "land_and_phase_relation": "本轮只研究一个整体宗地与单一项目，不建立跨期关系",
    "lifecycle": "prelaunch",
    "fact_cutoff": "2026-08-01",
    "identity_status": "closed"
  },
  "authorized_inputs": [
    {"id": "INPUT-TASK", "path": "input/task-brief.md", "role": "formal_material", "authorization": "synthetic_public_fixture"},
    {"id": "INPUT-FORMAL", "path": "input/formal-material.md", "role": "formal_material", "authorization": "synthetic_public_fixture"},
    {"id": "INPUT-MARKET", "path": "input/market-material.json", "role": "public_evidence", "authorization": "synthetic_public_fixture"},
    {"id": "INPUT-VOICES", "path": "input/customer-voices.md", "role": "customer_voice", "authorization": "synthetic_public_fixture"},
    {"id": "INPUT-GAPS", "path": "input/facts-conflicts-gaps.json", "role": "formal_material", "authorization": "synthetic_public_fixture"},
    {"id": "INPUT-UE", "path": "input/ue-notes.json", "role": "formal_material", "authorization": "synthetic_public_fixture"}
  ],
  "enabled_products": [1, 2, 3, 5],
  "disabled_products": [],
  "current_decisions": [
    {"id": "DEC-AREA", "decision": "教程分析采用较高用地数值62300平方米，同时保留61800平方米原始差异"},
    {"id": "DEC-RAIL", "decision": "只使用2.4公里直线距离，2.1公里步行距离保持待核实"}
  ],
  "superseded_decisions": [],
  "explicit_non_goals": ["制作PPTX", "制作正式网页", "真实客户效果验证", "外部发布"],
  "external_actions_authorized": [],
  "status": "project_identity_closed"
}
```

## 业务目标

本轮首先形成甲方可读的竞争答案，再把同一答案交给 UE 售前方案。视觉载体不在教程评分范围。

## 输入职责

正式材料提供项目底盘；合成市场材料只提供候选事实；合成客户声音提供有限选择事件；UE说明只定义可证明的空间关系。任何一类输入都不直接给出最终竞争武器。

## 使用边界

全部事实和判断只在虚构教程内成立。价格、学校、交付、未核步行路线和正式图片保持 gap，不转成客户承诺。
