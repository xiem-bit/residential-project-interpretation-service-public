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

## 一、按当前任务读取

先读当前用户材料、`AGENT_RULES.md`与对应任务规范；首次安装或发行状态再读安装、发行文件。`references/production-reference-index.json`帮助按问题取用样例，不要求每个任务重读返工历史。公开教程只提供方法与完成度，其事实不成为本案事实。

## 二、开始一个新项目

首次在新电脑使用时，先按`INSTALL.md`完成对应层级的doctor。doctor只验证包与环境，不替代业务理解和真人验收。

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

`--products`默认仅启用产物1；本次公开发行只支持产物1、2、3、5，产物1、2可分别启用，其他产物按实际需要加入。产物4不在本次发行范围内。发生实质语义变化时再增加`--include-change-registry`。

随后按 `workflows/residential-production-orchestrator/SKILL.md` 完成工作目录中的必需输出。统一语义核是本流程的产出，不能由初始化脚本或下游载体适配器代写。

## 三、按启用范围生成内容

初始化器保留项目合同、事实／冲突／缺口、启用矩阵与回执。产物1、2分别生成自己的甲方报告与后台摘要；完整深化及方案任务再保留必要语义核和竞争力，UE合同及原型输入仅在启用时生成。未启用部分不填空表。文件对应以`PRODUCTION_PATH_MANIFEST.json`为准。

`--products 1`可独立生产竞争态势研究；`--products 2`可直接消费已有竞争研究并生产购买决策报告。产物3的实际页面生产使用`tools/product3_ppt_pipeline/README.md`，产物1、2导出使用`tools/product12_reports/README.md`。原有确认及实际页面检查保持，Grist无需安装。

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
  --adoption <adoption-receipt.json> \
  --sufficiency-input <sufficiency-input.json>
```

新回包须绑定原请求与实际充分性输入，旧包先保留材料并按原合同重包。不得降低原请求门槛来迁就回包。该检查确认请求、证据、回传和采用回执没有丢失边界，不会替住宅生产 Owner 判断证据是否足以形成商业结论。

## 五、业务通过与载体通过分开记录

按当前启用部分登记相应业务状态，以下不构成所有任务的必经序列：

- `rules_loaded`
- `project_identity_closed`
- `product1_complete`
- `semantic_core_frozen`
- `minimum_three_sc_pass`
- `cross_product_consistency_pass`

条件状态只在相应产物启用时出现：`product2_complete`、`ue_solution_bridge_pass`、`product5_blueprint_pass`。机器合同通过、真人业务接受、载体完成、发布和业务效果继续分开记录。

PPTX、网页、发布和视觉复核使用独立的 adapter 状态。任何 adapter pass 都不能替代上述业务状态。

## 六、完成边界与暂停情形

对原始授权范围内的完整深化版产物2及完整竞争力方案，少于三条机制不同、比较清楚且本案实际承接的已成立超级竞争力时，不得宣告整体完成，也不得进入以此为前提的正式制作；应继续针对缺口研究、补查和推演。独立产物1及原本限定范围的修改任务不适用该数量门槛，不得临时缩改完整任务范围绕过下限。

以下情况暂停受影响部分：

- 输入包含无权使用的资料、个人信息或受限资产；
- 项目身份、权益、价格、学区、交付等关键事实冲突会改变结论，且现有材料无法定级；
- 竞争结论没有真实替代关系、购买任务或项目事实承接；
- 专业平台试图改写冻结的价值锚点、竞争边界或超级竞争力；
- 外部发送、发布、覆盖、权限变更或不可逆动作超出当前授权。

本仓库按 Apache-2.0 公开发行。使用自己的真实项目资料前，请自行确认资料使用权和保密边界。
