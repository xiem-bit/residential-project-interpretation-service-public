# 从这里开始

这套公共核心用于复刻住宅项目的业务生产流程，而不是复刻某种 PPT 风格。

最终目标是让一个没有私有工程历史的使用者或 Agent，仅凭公开仓和自己有权使用的项目材料，完成：

```text
原始材料与项目身份
→ 事实／冲突／缺口
→ 产物1竞争态势研究
→ 按需产物2购买决策研究
→ 统一业务语义核
→ 3—4条成立的超级竞争力
→ 产物启用与高成本生产准入
→ 产物3／4／5的UE业务投影
→ 变更回写与定向重投影
```

## 一、Agent 必读顺序

1. `START_HERE.md`；
2. `AGENT_RULES.md`；
3. `RELEASE_STATUS.md`；
4. `core/00-权威生产路径.md`；
5. `PRODUCTION_PATH_MANIFEST.json`；
6. `workflows/residential-production-orchestrator/SKILL.md`；
7. 当前任务的原始材料；
8. 仅按 Skill 路由读取本轮需要的核心规范、模板和 Schema。

不得先读取教程的 `expected/` 再声称独立发现了战略答案。教程答案只用于完成首次独立尝试后的对照和结构测试。

## 二、开始一个新项目

先声明任务模式：

- `real_project_delivery`：从一开始消费全部已授权资料；
- `hidden_answer_replay`：只消费冻结的盲态输入，产出后再揭晓参考答案；
- `non_research_task`：纯转译、导出、排版或发布，继承既有业务语义，不重开研究。

初始化一个空白工作目录：

```bash
python3 scripts/init_production_run.py \
  --input-dir examples/production-path-tutorial/input \
  --output-dir verification-tmp/my-production-run
```

随后按 `workflows/residential-production-orchestrator/SKILL.md` 完成工作目录中的必需输出。统一语义核是本流程的产出，不能由初始化脚本或下游载体适配器代写。

## 三、必需生产输出

一个完整研究型任务至少具有：

```text
project-contract.md
fact-conflict-gap-register.json
product1-competition-study.md
product2-buyer-decision-study.md
semantic-core.json
super-competitiveness-plan.json
product-enablement-matrix.json
product3-chapter2-contract.json
product3-chapter3-contract.json
ue-solution-handoff.json
change-impact-registry.json
production-receipt.json
```

产物 2 未启用时仍保留同名 Markdown，并在机器摘要中明确 `not_enabled` 及理由。产物 3—5 未启用时由启用矩阵记录，不为凑齐形式生产空载体。三个 Markdown 文件都包含一个可由公共校验器读取的 JSON 摘要块，同时保留面向人的完整正文。

## 四、验证一次生产运行

```bash
python3 scripts/verify_production_run.py verification-tmp/my-production-run
```

机器校验只证明：文件、字段、引用、状态、数量、五项检查和跨产物编号关系符合合同。它不能判断竞争结论是否真正专业。

业务能力通过还需要隐藏答案盲审：只给一套未公开的虚构原始材料，由未参与发行工程的使用者或 Agent 独立完成，然后由真人按 `evaluation/hidden-answer/rubric.json` 评分。验收协议见 `BUSINESS_COLD_START_PROTOCOL.md`。

## 五、业务通过与载体通过分开记录

业务主链状态：

- `rules_loaded`
- `project_identity_closed`
- `product1_complete`
- `product2_complete_or_not_enabled`
- `semantic_core_frozen`
- `minimum_three_sc_pass`
- `business_judgment_blind_review_pass`
- `ue_solution_bridge_pass`
- `cross_product_consistency_pass`
- `production_path_replication_pass`

PPTX、网页、XMind、发布和视觉复核使用独立的 adapter 状态。任何 adapter pass 都不能替代上述业务状态。

## 六、必须停下的情形

- 输入包含无权使用的资料、个人信息或受限资产；
- 项目身份、权益、价格、学区、交付等关键事实冲突会改变结论，且现有材料无法定级；
- 少于三条不同机制的 `established` 超级竞争力；
- 竞争结论没有真实替代关系、购买任务或项目事实承接；
- 专业平台试图改写冻结的价值锚点、竞争边界或超级竞争力；
- 外部发送、发布、覆盖、权限变更或不可逆动作超出当前授权。

本仓库按 Apache-2.0 公开发行。使用自己的真实项目资料前，请自行确认资料使用权和保密边界。
