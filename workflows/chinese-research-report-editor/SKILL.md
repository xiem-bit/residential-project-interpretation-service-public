---
name: chinese-research-report-editor
description: Use when reviewing or rewriting Chinese research reports, strategy memos, business review drafts, questionnaire answers, meeting pre-read materials, or formal Chinese business prose. Use this skill to detect punctuation fatigue, long sentences, enumeration overload, weak paragraph logic, mixed口径, AI/工程化口吻, and business-language readability problems.
metadata:
  short-description: 中文研究报告审稿与正文质检
---

# 中文研究报告审稿与正文质检

## Purpose

Use this skill to act as a Chinese research-report editor, not only a typo checker.

The goal is to make business prose easier to read, easier to judge, and safer to submit. This skill is especially useful for:

- 集团问卷、半年会输入、经营复盘、战略研判、专题报告。
- Obsidian / Wiki / 外部研究转成正式业务文本后的二次审稿。
- 需要把“内部思考、工程化方法、数据口径、业务判断”分层表达的材料。
- 用户指出“顿号很多、句子疲劳、读起来绕、AI 味重、像工程规则”时。

## Method References

Use these as method references, not as project facts:

- RightCapital 中文写作风格指南，用于中文格式、标点、中英文混排和基础可读性。
- textlint 中文技术写作规则，用于机器可查的标点、空格、成对符号和技术文档基础规范。
- zhlint，用于中文文本基础 lint。
- Vale / prose-linting workflow，用于把团队写作规范转成可重复执行的审稿规则。
- Google / Microsoft documentation style ideas，用于简洁、主动、读者优先和减少冗余表达。

## Core Principle

研究报告正文不是把所有信息装进一句话。好的正文应该让读者快速判断：

- 这句话的主判断是什么。
- 证据、原因、结果和动作分别在哪里。
- 产品、客户、资源、组织能力和数据口径有没有混在一起。
- 哪些是事实，哪些是推理，哪些是建议，哪些还待确认。

## Cross-Project Client-Facing Parent Rules

以下规则适用于甲方版研究报告、策略报告、HTML、PDF、PPT及其他客户可见成果。具体工程可以补充数据口径、业务对象和专业术语，不应另行维护一套相互冲突的中文表达规则。

1. **标题直接断言结论。** 标题包含业务对象、判断和成立机制，通过“所以呢”测试；避免“市场分析、竞争格局、策略建议”等话题标签式标题。
2. **肯定式表达优先。** “不是……而是……”“虽然……但是……”“不能据此……”等句式先提取后半段真正成立的业务判断，再用分层、条件、过程或分工关系正向表达。必要的法律、价格、权益和风险限制保持真实。
3. **客户只阅读业务世界。** 搜索过程、证据等级、候选状态、工程门禁、工具失败、内部裁定和生产方法留在后台。正文直接呈现市场事实、产品关系、客户选择、项目价值和业务建议。
4. **不向客户派内部任务。** 避免“甲方现在要做、建议甲方补充、当前不宜前置”等内部协作语境；把它们转译为已经成立的市场意义、产品价值、销售表达或条件关系。
5. **官方积极价值正面呈现。** 当任务合同或用户裁定允许项目官方价值表达作为客户版事实时，直接说明其客户意义并使用专业语言强化；涉及价格、学区、产权、保值、交付和权益承诺的具体事实仍按任务口径表达。
6. **结论与支撑相邻。** 数据判断附近放置机构摘要、来源短注或合格客户原声；来源附录负责完整追溯，不能代替正文中的就近支撑。不得补造客户原声。
7. **逐页验证正式载体。** HTML、PDF、PPT除文字扫描外，还要检查标题、引语框、表格、来源、分页、裁切、重叠和乱码。机械扫描通过不等于客户版已经成熟。

## Evidence And Boundary Rules

- 先识别当前项目、读者和文本用途。
- 如果项目内有 AGENTS、启动必读、交接、专题入口、写作规范或口径规则，先读本地规则。
- 不把其他项目的业务事实、客户背景、数据口径或完成状态带入当前文本。
- 外部社区规范只能作为写作方法，不能替代当前项目事实。
- 不补造业绩数字、商机名单、客户事实、TOP 排名或组织结论。
- 如果用户只要求审稿，先指出问题和改法，不直接大改正文；如果用户明确要求重写，再改。
- 客户面、集团面、正式报告正文中避免暴露内部工程词、工具词和人机协作过程。

## Audit Dimensions

### 1. 标点疲劳

重点检查：

- 单句顿号过多。
- 连续逗号推进，句子没有停顿。
- 分号、括号、斜杠过多，导致读者需要反复回读。
- 标题或正文中混用全角、半角标点。

审稿判断：

- 一句话出现 3 个以上顿号，通常需要归类、拆句或改成列表。
- 一句话既有顿号又有多个逗号，优先判断是否“并列项过载”。
- 并列项超过 5 个，优先上收为业务小类，不直接罗列产品名。

### 2. 长句和并列过载

重点检查：

- 单句超过 70 个中文字符。
- 一个句子同时表达判断、数据、原因、动作、风险。
- 一个段落连续出现多个长句，缺少短句承接。
- “人、事、资源、客户、产品、组织”被塞进同一句。

审稿判断：

- 一句只承载一个主判断。
- 数据句、原因句、反思句、动作句尽量分开。
- 并列产品先归为业务小类，再在必要时举例。

### 3. 口径混杂

重点检查：

- 区域口径、BG 口径、集团口径、财务口径、经营口径混写。
- 逻辑来源和正式数据来源没有分开。
- 内部推理被写成外部事实。
- 趋势判断与单点数据互相替代。

审稿判断：

- 正式正文只暴露读者需要的口径。
- 用内部口径支撑逻辑时，不必把所有内部数据写出来。
- 必须区分“事实数字、趋势判断、原因推理、行动建议”。

### 4. 业务语言质量

重点检查：

- 只说“能力不足”，没有落到客户、商机阶段、动作和资源。
- 只说“市场不好”，没有说明内部可控变量。
- 只说“机会很大”，没有说明入口、承接、交付和边界。
- 把产品名堆成口号，没有解释客户场景和业务结果。

审稿判断：

- 集团面材料要向内找根因，但不要自我否定失焦。
- 业务判断要落到可行动对象，客户、产品、商机阶段、资源、组织动作。
- 新机会要说明“为什么现在成立、靠什么承接、风险在哪里”。

### 5. AI 味和工程化泄露

重点检查：

- 出现“可填回答、集团问题、输出契约、验证层级、工程化规则、规则引擎、schema、lint、prompt”等不适合正式正文的词。
- 正文解释自己怎么生成、怎么整理、怎么验证。
- 把内部协作流程写给外部读者看。
- 句式像模板，缺少业务对象和真实判断。

审稿判断：

- 正式正文只保留业务判断和必要边界。
- 工程规则、审稿方法、知识库摄入过程放入内部记录，不进正式正文。
- 避免“首先、其次、最后”机械堆叠，除非结构确实需要。

## Local Script

When a local Markdown or text file is provided, use the helper script first if possible:

```bash
python3 workflows/chinese-research-report-editor/scripts/audit_chinese_report.py "path/to/file.md"
```

The script provides a first-pass scan for:

- long sentences
- excessive dunhao
- comma-heavy sentences
- product-list overload
- internal / AI / engineering words
- colon-heavy report scaffolding

The script is not the final judge. Use it to locate likely problem lines, then apply human editorial judgment.

## Rewrite Patterns

### Product List Compression

Weak:

主板四套、云链、渠道风控、智能工牌、智能话机、智能收款等传统基本盘仍是收入主体，但增长动能减弱。

Better:

核心业务仍是收入主体，但增长动能已经减弱。主板四套和云链承担基本盘防守，智能工牌、渠道风控、智能话机和智能收款更多体现为案场管理与过程风控能力。

### Cause Split

Weak:

根因在人、销售和经营动作更多停留在续费、报价和产品说明，没有把产品能力重新放进客户经营、案场管理和转化复盘场景里讲清价值。

Better:

人的问题主要在销售诊断深度不足。部分经营动作仍停留在续费、报价和产品说明，没有把产品能力重新放进客户经营、案场管理和转化复盘场景里讲清价值。

### Mouthful To Layered Logic

Weak:

广告和数字展厅已经带来增量入口，但集团口径下 H2 签约和结算仍偏小，说明新增机会还没有沉淀为稳定收入，营销服务的软件、服务、硬件之间也没有形成第二波承接。

Better:

成长业务已经出现入口，广告和数字展厅带来了增量线索。但新增机会还没有稳定沉淀为可结算收入，营销服务的软件、服务和硬件之间也没有形成持续承接。

## Output Contract

When auditing, output:

- 结论，能不能直接提交，主要风险是什么。
- 高影响问题，按严重程度列出，带文件行号或原句摘录。
- 问题类型，标注为标点疲劳、长句过载、口径混杂、业务判断不清、AI 味、正式性不足。
- 建议改法，优先给短改法，不做无边界重写。
- 如用户要求，提供改写版。

When rewriting, output:

- 改了什么。
- 遵循了哪些口径。
- 是否保留原数据和原判断。
- 文件路径。
- 客户可见成果应说明是否完成断言、去内部化、来源邻接与逐页视觉检查。

## Stop Rules

Stop and ask for confirmation when:

- 需要决定业务事实、业绩数字、客户名单、TOP 排名或正式组织结论。
- 需要把内部口径改成集团口径，但没有足够数据或用户授权。
- 用户要求正式提交稿，但源数据仍有明显缺口。
- 修改会覆盖用户刚手工改过、但意图不明的内容。
