# 完整业务生产路径冷启动协议

## 1. 验证目标

验证陌生使用者或外部 Agent 能否只凭公开固定候选和一套未公开答案的虚构原始材料，独立发现住宅项目的竞争问题、竞争关系、客户购买任务、三至四条超级竞争力及 UE 业务解法。

本协议不评价 PPTX 视觉。不得把旧 `COLD_START_PROTOCOL.md` 的 `formal_visual`、`cross_machine`、`workbuddy`状态当作本协议通过证据。

## 2. 参与角色

- `release_owner`：冻结候选、准备盲态包，不参与答题；
- `participant`：未参与公开包设计，只获得仓库地址、固定提交或候选标签、`START_HERE.md`和盲态原始输入；
- `blind_reviewer`：未看到生产过程，按统一量表评审业务结果；
- `observer`：记录提示、环境协助、时间、gap 和状态，不提供内容答案。

一个人可以兼任 release owner 和 observer，但不能兼任 participant 或独立 reviewer。

## 3. 盲态输入

私密 UAT 包只能包含：

- 完全虚构的项目与任务说明；
- 虚构正式资料、顾问未裁定的市场材料、客户声音／选择事件；
- 有意设置的事实冲突、未知项和反例；
- 当前允许使用的外部能力说明。

不得包含：语义核、价值锚点、SC、竞品角色答案、客户任务答案、UE 场景答案、页面计划、顾问定稿、评分参考答案或文件名中的答案提示。公开仓只提供任务模板和量表，不公开实际 holdout 或答案。

## 4. 操作步骤

1. release owner 记录候选提交、盲态包哈希和参与者身份边界；
2. participant 从干净目录取得固定候选；
3. participant 只按 `START_HERE.md`和公开 Skill 自主路由；
4. participant 从原始输入生产全部必需业务输出；
5. observer 记录基础设施协助和内容指导次数；
6. 运行 `scripts/verify_production_run.py`，机器结构通过后冻结输出哈希；
7. blind reviewer 使用 `evaluation/hidden-answer/rubric.json`评分；
8. 只有结构、盲审、UE桥接、跨产物一致性和诚实边界均通过，才签发 `production_path_replication_pass`。

## 5. 零内容指导

允许的基础设施协助：网络、Git、Python 命令、文件权限和明确的工具故障排除。每次都要记录。

以下计入 `content_guidance_count`：解释住宅方法、指出竞品、建议购买任务、命名价值锚点或 SC、指定某条结论、告诉 participant 该读取哪个答案文件、替其修订业务产出。首次正式冷启动要求 `content_guidance_count = 0`。

## 6. 机器门槛

机器只验证：必需文件、Schema、项目 ID、版本、引用、三至四条 established SC、五项字段、购买推进覆盖、第二／三章连续性、UE 映射、变更引用和状态诚实。机器不得自动判定战略质量。

## 7. 盲审门槛

量表总分 100。以下同时满足才通过：

- 总分至少 80；
- `competition_problem`、`competitor_boundary`、`buyer_tasks`、`super_competitiveness`、`ue_solution`五个核心维度均达到各自最低分；
- 没有把未知写成没有、把顾问推演冒充客户原声、把同距离当直接竞品、把功能清单当 SC 或把视觉载体当战略；
- 三至四条 SC 机制不同，五项成立检查均有实质内容；
- 新事实测试能回写上游并定向重投影。

## 8. 回执状态

结构通过但未盲审：`machine_contract_pass_blind_review_pending`。

盲审未达标：`business_judgment_returned_for_research`，记录具体退回项，不调整量表迁就答案。

全部通过：业务主链写入 `production_path_replication_pass`。PPT、网页或发布状态保留在 `adapter_statuses`，无论通过与否都不改变业务结论。

## 9. 发布规则

只有第二位使用者或外部 Agent 的首次零内容指导冷启动通过后，才允许创建 `v0.2.0-rc.1` 标签。若只完成同机教程、自测或发行作者复核，候选可以提交到分支，但不得标记为已发布 RC。
