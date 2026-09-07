---
name: chinese-research-report-editor
description: Draft, rewrite, or review Chinese business prose, reports, proposals, weekly reports, and presentation copy. Use for 断言写作、断言规则、去 AI 腔、说人话, or learning from a user's manual wording edits. Preserve substantive judgments, evidence, terminology, and the user's voice while improving clarity.
metadata:
  short-description: 断言写作与人话审稿
---

# 断言写作与人话审稿

## 共用入口与本轮升级

本 Skill 是本机各工程的中文业务表达父级能力，同时接受“断言写作”“断言规则”“中文审稿”“去 AI 腔”“说人话”等调用意图。当前共用规范为 **断言写作 v2.0（2026-09-04）**，在结论先行、肯定式表达和事实保真的基础上，增加业务用途、完整指代、信息密度、真人语气及跨页一致性的审稿要求。

按当前文本的用途和修改范围读取 [断言写作 v2.0](references/assertion-writing-v2.md)：

- 错字、专名、事实值或用户指定的局部词语替换：核对受影响文本，保留原意；不以完整阅读细则或全文改写为前置。
- 内部草稿、局部段落改写或定向审稿：读取第1、2、5、6节的判断标准、表达原则、保真限制与检查要求；按问题选读第4节示例。客户文稿补读第7节的受众编辑与语义保真要求，房地产客户白描、客群肖像再读对应小标题。
- 正式文稿的新写、实质重写或全面审稿：完整读取通用判断与编辑规范（第1、2、4、5、6、7节），按实际载体做必要质量检查。
- 从用户真人改稿提炼方法：另读第3节，并对照真实前后文本。

范围不清或章节不足以解释当前问题时，可扩大到完整阅读；不将本次局部任务自动扩大为整篇改稿。

用户当前裁定、锁定内容及真实原声优先于通用风格。具体工程可补充领域用语、受众和正式交付要求；历史范例只迁移写法，不迁移项目事实，也不要求把各工程现有文本批量重写。

2026-09-05补充：面向客户的报告默认在正式排版前完成一次读者口吻全文编辑。执行方法、白描与肖像写法、完整改写示范及“喜欢与购买”等语义保真要求见上述 v2.0 文档第7节；该节是现有编辑流程的一部分。已认可主体的限定修订只处理受影响内容。

## Purpose

Use this skill to act as a Chinese research-report editor, not only a typo checker.

The goal is to make business prose easier to understand and use without losing its judgments, evidence, or the author's voice. This skill is especially useful for:

- 集团问卷、半年会输入、经营复盘、战略研判、专题报告。
- Obsidian / Wiki / 外部研究转成正式业务文本后的二次审稿。
- 需要把“内部思考、工程化方法、数据口径、业务判断”分层表达的材料。
- 用户指出“顿号很多、句子疲劳、读起来绕、AI 味重、像工程规则”时。
- 用户手动改过文稿，要求理解修改原则、举一反三并等待裁定时。

## Method References

Use these as method references, not as project facts:

- RightCapital 中文写作风格指南，用于中文格式、标点、中英文混排和基础可读性。
- textlint 中文技术写作规则，用于机器可查的标点、空格、成对符号和技术文档基础规范。
- zhlint，用于中文文本基础 lint。
- Vale / prose-linting workflow，用于把团队写作规范转成可重复执行的审稿规则。
- Google / Microsoft documentation style ideas，用于简洁、主动、读者优先和减少冗余表达。

## Core Principle

正文应让读者直接看懂业务判断及其依据。句子可以适当展开，帮助读者快速判断：

- 这句话的主判断是什么。
- 证据、原因、结果和动作分别在哪里。
- 产品、客户、资源、组织能力和数据口径有没有混在一起。
- 哪些是事实，哪些是推理，哪些是建议，哪些还待确认。

## Cross-Project Parent Rules

统一规则及例子见上方 v2.0 引用。审稿先判断读者和用途，再判断句式。正式客户成果重在客户问题、比较判断与业务价值；培训可以讲生产方法，但要解释真实案例中的判断怎么改变了结果；运行说明可以写操作步骤。不要把“去内部化”误用为删除任务本身要讲的内容。

标题与正文共同承担信息：标题、副标题足以概括主要判断，正文保留自助阅读所需的事实、例子与推导。未经用户要求，不通过删论据、缩短原声或降低信息密度来追求口语化。

## Evidence And Boundary Rules

- 先识别当前项目、读者和文本用途。
- 先读适用的工程规则，再按本次写作范围读取相关口径与材料；不通读所有启动、交接和历史文件。
- 不把其他项目的业务事实、客户背景、数据口径或完成状态带入当前文本。
- 外部社区规范只能作为写作方法，不能替代当前项目事实。
- 不补造业绩数字、商机名单、客户事实、TOP 排名或组织结论。
- 如果用户只要求审稿，先指出问题和改法，不直接大改正文；如果用户明确要求重写，再改。
- 客户面、集团面正文不堆放与读者用途无关的工程词和过程信息。读者明确要学习工具、协作或生产方法时，按任务需要解释。

## 按需审稿细则

标点疲劳、长句并列、口径混杂、业务表达或工程语言问题，定向读取 [检查与改写示例](references/editor-audit-details.md) 的对应章节。全文审稿涉及多类问题时可完整阅读。

## Local Script

For a whole-document audit, the helper can locate candidate wording issues. For typos, proper names or narrow factual edits, inspect the affected text directly; do not scan the whole file by default:

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

The script is not the final judge. Counts and word hits locate candidates; they do not detect the full meaning, authorize rewriting, or require zero findings. It cannot decide whether an expression sounds human. Use v2.0's reader, meaning, and voice checks for that judgment.

## Output Contract

When auditing, output:

- 结论，能不能直接提交，主要风险是什么。
- 高影响问题，按严重程度列出，带文件行号或原句摘录。
- 问题类型，标注为标点疲劳、长句过载、口径混杂、业务判断不清、AI 味、正式性不足。
- 建议改法，以清楚、完整为准，可以比原句更长；不做无边界重写。
- 用户要求先裁定时，逐项给出实际页码或行号、原句、建议句和理由；未获授权不改正文。
- 用户提供手工修改时，先用真实前后差异解释原则，再列同类建议；将错字、引用不一致与风格建议分开。
- 如用户要求，提供改写版。

When rewriting, output:

- 改了什么。
- 遵循了哪些口径。
- 是否保留原数据和原判断。
- 文件路径。
- 客户可见成果按任务风险核对事实、原声与版面；对用户只说明会影响使用的限制，不在成果正文加入制作和审稿自证。

## Stop Rules

Pause only the affected text when a missing fact or authorization cannot be resolved from current materials:

- 需要决定业务事实、业绩数字、客户名单、TOP 排名或正式组织结论。
- 需要把内部口径改成集团口径，但没有足够数据或用户授权。
- 用户要求正式提交稿，且源数据缺口会改变核心结论或正式效力；非关键缺口可保留真实限制后继续。
- 修改会覆盖用户刚手工改过、但意图不明的内容。
