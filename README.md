# 住宅项目竞争力公共核心 — v0.1.0-rc.1

这是一个平台无关的住宅项目竞争力生产核心公开发行候选版。任何人都可以直接克隆、下载、检查和运行，无需申请仓库访问权限。

首个完整虚构项目流程已经在标准 Python 和 Node 运行环境中通过验证。请从 [`START_HERE.md`](START_HERE.md) 开始；本页用于说明发行包的能力与边界。

本仓库采用 [Apache License 2.0](LICENSE) 开源许可。公共 RC 状态和支持边界记录在 [`RELEASE_STATUS.md`](RELEASE_STATUS.md) 中。

## 已包含的可运行能力

- 中文断言式文案检查；
- 产物 3 第二章和第三章合同校验；
- 产物 3 第二章至第三章桥接校验；
- 产物 4 合同与 XMind 校验；
- 通用产物 3 业务门禁；
- 虚构 Markdown 安全测试夹具；
- 面向多来源原生页面窄场景的 PPTX starter 适配器，并包含 OOXML 包级质量检查。

## Python 验证

Python 核心仅使用标准库。

```bash
python3 tests/run_public_tests.py
```

## 完整虚构项目冷启动

```bash
python3 scripts/run_rc1_demo.py --install-node-deps
```

该命令会在 `verification-tmp/fictional-demo/` 下生成本机回执。已确认状态为 `local_fictional_e2e_pass`：方法合同、平台往返、PPTX 结构和产物 5 静态包均已通过。正式视觉审阅、独立电脑运行和 WorkBuddy 适配仍属于彼此独立的验证状态。

这个本机命令是参考实现，不是外部可移植性测试。使用固定 tag、零内容指导的 WorkBuddy 流程定义在 [`COLD_START_PROTOCOL.md`](COLD_START_PROTOCOL.md) 中。

## PPTX starter 验证

PPTX 适配器需要 Node.js 20 或更高版本，以及标准 npm 依赖。

```bash
cd tools/product3_ppt_pipeline/automizer_adapter
npm ci
npm run verify
```

该适配器只保留明确选中的源页面，剥离备注和批注，移除不可达的 OOXML 部件，拒绝绝对源路径，并生成可跨路径使用的回执。独立校验器会检查页面数量、关系、孤立部件和嵌入的本机路径痕迹。

这是结构包质量检查，不是演示文稿渲染器。正式页面设计、高保真生成和渲染由所选平台适配器负责，例如 Codex、WorkBuddy、其他 Agent 平台或人工制作团队；它们不是公共核心必须实现的能力。`image-size` 的传递依赖安全公告及补偿性输入控制，已作为有期限的依赖例外记录；本工程不宣称 `npm audit` 已通过。

## v0.1 收敛目标

本公共候选版用于证明：没有私有项目历史、也没有 Codex 运行环境的使用者，可以在干净的标准运行环境中执行一次虚构住宅项目流程：

`START_HERE → 研究合同 → 虚构证据 → 产物 3 生产输入 → 平台生成演示文稿 → 公共 QA → 产物 5 通用壳层 → 静态包 → 交付检查`。

只有闭合该流程所必需的组件才进入 RC1。独立 WorkBuddy 冷启动是下一项可移植性验证，不是下载或安装门槛。详见 `V0_1_RELEASE_SCOPE.md`。

## 明确排除的内容

- 所有真实项目、客户材料、生产资产和私有评测数据；
- 私有 Git 历史、分支、标签和仓库元数据；
- 本机路径、凭据、内部域名、SSH 配置和托管现场；
- 平台专属的演示文稿、托管和高状态生产运行环境；
- RC1 虚构端到端流程不需要的组件；
- 正式 PPT 生成引擎、Grist、云发布配置和真实项目的产物 5 实现；
- A4 PDF 生成能力，除非后续 RC1 流程证明它确有必要。

候选包的精确边界见 `PUBLIC_CORE_MANIFEST.json`、`RELEASE_MANIFEST.json`、`A_CLASS_ALLOWLIST.txt`、`B_CLASS_PROMOTION_MANIFEST.json`、`V0_1_RELEASE_SCOPE.md` 和 `DEPENDENCY_EXCEPTIONS.json`。第三方许可证与安全边界记录在 `THIRD_PARTY_NOTICES.md`、`THIRD_PARTY_LICENSES.json` 和 `SECURITY.md` 中。
