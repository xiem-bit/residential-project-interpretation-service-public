# 望川序公开安全生产任务合同

```json
{
  "schema": "residential.project_contract.v0.2",
  "task_id": "TUTORIAL-WCX-001",
  "mode": "tutorial",
  "business_question": "城市核心换新家庭如何在中心二手房、外围大面积新房和继续等待之间建立新的比较标准",
  "primary_audience": "虚构甲方营销与销售团队",
  "use_case": "形成甲方竞争态势研究并冻结可供后续继承的业务语义",
  "business_stage": "presales_research",
  "project": {
    "id": "fictional-wangchuan-xu",
    "canonical_name": "望川序（全量虚构）",
    "aliases": [],
    "city": "澜州市（虚构）",
    "district_or_area": "中城北岸（虚构）",
    "location": "中城北岸单一宗地，不建立跨期关系",
    "developer": "澜州望川置业有限公司（虚构）",
    "land_and_phase_relation": "单一宗地、单一推广名、单一开发主体",
    "lifecycle": "prelaunch",
    "fact_cutoff": "2026-08-20",
    "identity_status": "closed"
  },
  "authorized_inputs": [
    {"id": "INPUT-TASK", "path": "input/task-brief.md", "role": "formal_material", "authorization": "synthetic_public_fixture"},
    {"id": "INPUT-FORMAL", "path": "input/formal-material.md", "role": "formal_material", "authorization": "synthetic_public_fixture"},
    {"id": "INPUT-MARKET", "path": "input/market-material.json", "role": "public_evidence", "authorization": "synthetic_public_fixture"},
    {"id": "INPUT-VOICES", "path": "input/customer-voices.md", "role": "customer_voice", "authorization": "synthetic_public_fixture"}
  ],
  "enabled_products": [1],
  "disabled_products": [
    {"product": 2, "reason": "本轮不需要独立客群报告"},
    {"product": 3, "reason": "本轮不生产UE售前提案"},
    {"product": 5, "reason": "本轮不生产交互蓝图"}
  ],
  "current_decisions": [
    {"id": "DEC-ROUTE", "decision": "单日路线核验只支持本次有边界的路线组合，不写成长周期平均通勤"},
    {"id": "DEC-DELIVERY", "decision": "交付清单只用于说明可核对范围，不升级为品质或按期交付保障"}
  ],
  "superseded_decisions": [],
  "explicit_non_goals": ["生产产物2", "生产PPTX", "生产交互网页", "外部发布", "真实市场效果验证"],
  "external_actions_authorized": [],
  "status": "project_identity_closed"
}
```

## 业务目标

以甲方可直接使用的语言明确本案竞争对象、客户比较标准和三条竞争武器。本轮完整收口于产物1与统一语义核，不为空缺的下游产物生成文件。

## 事实边界

全部名称、数字、客户声音和结论均为虚构。单日路线核验不代表长期通勤，交付清单不代表品质结果，未发布价格和交付日期不进入客户承诺。

