# 从这里开始

这套公共核心用于复刻住宅项目的业务生产流程，而不是复刻某种 PPT 风格。

最终目标是让一个没有私有工程历史的使用者或 Agent，仅凭公开仓和自己有权使用的项目材料，完成：

```text
原始材料与项目身份
→ 事实／冲突／缺口
→ 按缺口形成上游任务、证据回传与采用／拒绝回执
→ 产物1竞争态势研究
→ 按需产物2购买决策研究
→ 统一业务语义核
→ 3—4条成立的超级竞争力
→ 产物启用与高成本生产准入
→ 产物3／5的UE业务投影
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

教程的 `expected/` 是公开安全生产参考，可用于理解完整路径、字段关系和交付水位；不得把其中的项目事实、竞品、客群或SC复制为当前项目事实。

## 二、开始一个新项目

先声明任务模式：

- `real_project_delivery`：从一开始消费全部已授权资料；
- `non_research_task`：纯转译、导出、排版或发布，继承既有业务语义，不重开研究。
- `tutorial`：运行公开安全样例与回归，不代表真实客户接受。

初始化一个空白工作目录：

```bash
python3 scripts/init_production_run.py \
  --input-dir examples/production-path-tutorial/input \
  --output-dir verification-tmp/my-production-run \
  --products 1,2,3,5
```

`--products`默认仅启用产物1；本次公开发行只支持产物1、2、3、5，只有任务确实需要时才加入产物2、3或5。产物4不在本次发行范围内。发生实质语义变化时再增加`--include-change-registry`。

随后按 `workflows/residential-production-orchestrator/SKILL.md` 完成工作目录中的必需输出。统一语义核是本流程的产出，不能由初始化脚本或下游载体适配器代写。

## 三、必需生产输出

一个完整研究型任务至少具有：

```text
project-contract.md
fact-conflict-gap-register.json
product1-competition-study.md
product1-competition-summary.json
semantic-core.json
super-competitiveness-plan.json
product-enablement-matrix.json
production-receipt.json
```

产物2、3、5只在启用时增加各自产物文件；未启用时只在项目合同和启用矩阵中记录理由，不生成空占位。`change-impact-registry.json`只在发生实质语义变化时生成。产物1、2的甲方正式报告与机器摘要物理分开：Markdown只承载甲方正文，配对JSON侧车只供校验、引用和跨产物消费。

## 四、验证一次生产运行

```bash
python3 scripts/verify_production_run.py verification-tmp/my-production-run
```

机器校验只证明：实际启用文件、字段、引用、状态、数量、成立检查和跨产物编号关系符合合同。它拥有否决权，但不能单独证明竞争结论专业或甲方接受；正式业务判断仍需专业语义审查，客户成果仍按任务完成真人验收。

任务消费公开信息证据包时，再运行：

```bash
python3 tools/production_core/validate_upstream_exchange.py \
  --request <request.json> \
  --envelope <public-evidence-envelope.json> \
  --response <response.json> \
  --adoption <adoption-receipt.json>
```

该检查确认请求、证据、回传和采用回执没有丢失边界，不会替住宅生产 Owner 判断证据是否足以形成商业结论。

## 五、业务通过与载体通过分开记录

业务主链状态：

- `rules_loaded`
- `project_identity_closed`
- `product1_complete`
- `semantic_core_frozen`
- `minimum_three_sc_pass`
- `cross_product_consistency_pass`

条件状态只在相应产物启用时出现：`product2_complete`、`ue_solution_bridge_pass`、`product5_blueprint_pass`。机器合同通过、真人业务接受、载体完成、发布和业务效果继续分开记录。

PPTX、网页、发布和视觉复核使用独立的 adapter 状态。任何 adapter pass 都不能替代上述业务状态。

## 六、必须停下的情形

- 输入包含无权使用的资料、个人信息或受限资产；
- 项目身份、权益、价格、学区、交付等关键事实冲突会改变结论，且现有材料无法定级；
- 少于三条不同机制的 `established` 超级竞争力；
- 竞争结论没有真实替代关系、购买任务或项目事实承接；
- 专业平台试图改写冻结的价值锚点、竞争边界或超级竞争力；
- 外部发送、发布、覆盖、权限变更或不可逆动作超出当前授权。

本仓库按 Apache-2.0 公开发行。使用自己的真实项目资料前，请自行确认资料使用权和保密边界。
