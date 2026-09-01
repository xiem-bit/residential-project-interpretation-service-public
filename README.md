# 住宅项目竞争力生产核心

本仓库公开的是一条完整的住宅项目业务生产路径：从已授权原始材料出发，识别项目真正的竞争问题、有效竞争圈、客户购买任务和竞争解法，形成三至四条成立的超级竞争力，再把同一业务判断投影到住宅 UE 售前方案、签约后价值框架和交互原型。

PPTX、网页和 XMind 是可替换的下游载体。它们可以由 WorkBuddy、Codex、其他 Agent、专业平台或人工团队制作；载体是否美观不构成本工程住宅战略发现能力的通过证据。

当前 `v0.2.0-rc.1` 分支已完成P0能力同构冻结，正在把现行生产约束、增量检索、业务Harness、黄金参考和产物3／5黄金实现补入公开候选；候选尚未创建标签，也不构成可发布版本。已发布的固定标签 `v0.1.0-rc.1` 保持不可变，并重新界定为“已冻结语义核的下游合同与平台适配演示”。请先读取 [发行状态](RELEASE_STATUS.md) 和 [能力同构合同](CAPABILITY_PARITY_CONTRACT.md)。

本公共仓的固定提交与后续固定标签是唯一发行权威。WorkBuddy、Codex 或其他平台工作区
只能克隆并消费公开包；把文件直接复制进某台电脑的某个平台目录，不构成公开发布，也
不得形成与 GitHub 并行的版本权威。

## 本版新增的核心能力

- 以原始项目材料和轻量任务合同为入口，不再把现成语义核作为默认输入；
- 完整覆盖项目身份、事实／冲突／缺口、产物 1、产物 2、统一语义核、超级竞争力、产物启用与生产准入；
- 连续连接产物 3 第二章竞争推导、第三章 UE 证明、产物 4 单树价值框架与产物 5 交互蓝图；
- 语义变化先回写上游，再只重投影受影响产物；
- 提供平台中立的生产编排 Skill、模板、Schema、机器否决型Harness、公开回归fixture和公开安全黄金参考；
- 用六段SC因果和允许／禁止推导关系约束证据跨步，不把禁词扫描或机器得分当成商业判断；
- 把业务生产路径验收与 PPT／网页适配器验收彻底分开。

## 快速验证

Python 核心只使用标准库：

```bash
python3 tests/run_public_tests.py
python3 scripts/verify_production_run.py examples/production-path-tutorial/expected --mode tutorial
```

旧 RC1 的载体往返演示仍可独立运行：

```bash
python3 scripts/run_rc1_demo.py --install-node-deps
```

它只验证下游合同、PPTX 结构和静态包，不验证住宅竞争战略发现能力。

## 开源与边界

本仓库采用 [Apache License 2.0](LICENSE)。任何人都可以按许可证使用、修改和再分发代码、方法、模板与虚构样例。

以下内容不进入公开仓：真实项目和客户材料、受限图片与案例资产、凭据和运行现场、私有评测材料、平台专属视觉引擎。对应生产能力必须通过匿名或虚构的结构等价资产公开继承，不能因原件私有而省略。公开方法可以消费使用者自己有权使用的资料，但许可证不替代资料授权、保密义务或客户验收。

当前发行状态与尚未通过的门禁见 [RELEASE_STATUS.md](RELEASE_STATUS.md)，完整范围见 [V0_2_RELEASE_SCOPE.md](V0_2_RELEASE_SCOPE.md)，能力覆盖与退役边界分别见 [CAPABILITY_PARITY_MANIFEST.json](CAPABILITY_PARITY_MANIFEST.json) 和 [RETIRED_AND_PRIVATE_BOUNDARY.md](RETIRED_AND_PRIVATE_BOUNDARY.md)。
