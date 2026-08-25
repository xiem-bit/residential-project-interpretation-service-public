# 从这里开始

这是一套住宅项目竞争力生产的公共核心。它帮助一个不了解私有工程的使用者，
把已授权的项目材料整理成可检查的竞争判断和生产合同，再把高状态的 PPT／网页
制作交给当前平台，最后用公共规则验收返回产物。

当前仓库内的 `青岚澄境` 是全量虚构示例，不对应任何真实城市、企业、楼盘或客户。
第一次使用请先完整跑通它，不要先替换成真实项目。

## 你需要准备什么

- Python 3.9 或更高版本；
- Node.js 20 或更高版本及 npm；
- 约 300 MB 可用空间；
- 首次安装 Node 依赖时可访问 npm 软件源。

不需要 Codex 本机运行时、Grist、私有仓库、真实客户材料、云服务器或登录态。

## 第一步：运行完整虚构项目

任何人都可以从公开固定版本取得工程，无需仓库邀请或登录态：

```bash
git clone --branch v0.1.0-rc.1 --depth 1 \
  https://github.com/xiem-bit/residential-project-interpretation-service-public.git
cd residential-project-interpretation-service-public
```

然后在仓库根目录执行：

```bash
python3 scripts/run_rc1_demo.py --install-node-deps
```

命令会完成环境检查、合同装配、第二／三章门禁、平台往返、可编辑 PPTX 结构 QA、
产物5壳层装配、静态包锁定和最终回执。输出位于：

```text
verification-tmp/fictional-demo/
```

成功标志是终端显示 `RC1 FICTIONAL E2E: PASS`，并生成
`delivery-receipt.json`。再次运行可以省略 `--install-node-deps`。

这一步只证明当前克隆中的公共核心与测试适配器可运行，不等于 WorkBuddy 已经完成
正式视觉生产，也不等于跨机器冷启动通过。

## Agent 应按什么顺序读取

1. 本文件；
2. `contracts/住宅竞争力方法与生产合同.md`；
3. `examples/fictional-qinglan-chengjing/README.md`；
4. `examples/fictional-qinglan-chengjing/input/` 中的虚构输入；
5. `examples/fictional-qinglan-chengjing/work/semantic_core.json`；
6. `contracts/capability-routing.json` 与平台请求／回传 Schema。

不需要读取私有仓历史，也不要猜测任何未出现在这些材料中的真实项目事实。

## 谁负责什么

公共核心负责：

- 输入结构、事实／冲突／缺口状态和住宅竞争力方法；
- 3—4 条超级竞争力及第二／三章语义连续性；
- 平台生产请求与回传格式；
- PPTX 结构安全、业务门禁、静态包完整性及交付回执；
- 能力不足时返回真实 gap。

当前平台负责：

- PPT 的正式视觉设计、页面装配、渲染与逐页视觉检查；
- 正式网页原型的视觉检查；
- 根据平台能力选择自己的演示文稿、网页或原型 Skill。

仓库内的 PPT 测试适配器只证明接口可往返，不代表正式视觉质量。平台不得改写
公共合同中的项目标识、页面 ID、超级竞争力 ID、证据边界或已登记 gap。

## 什么时候算完成

虚构冷启动完成需要同时满足：

- 第二章、第三章及跨章门禁通过；
- 平台请求和回传页面 ID 完整一致；
- 返回一个可编辑 PPTX，且 OOXML 无孤立部件、损坏关系或本机路径；
- 产物5壳层使用同一语义核，静态包文件集合和哈希锁定；
- 最终回执明确区分本机结构验证、平台视觉责任和跨机器状态。

真实项目正式交付还必须由所选平台完成视觉复核。未完成时应保留
`FORMAL_VISUAL_REVIEW_REQUIRED`，不能把结构通过写成客户已验收。

## 从 GitHub 验证 WorkBuddy 冷启动

完成本地参考闭环后，任何使用者都可以从 Public GitHub 固定 tag 获取工程，只凭本文件
让 WorkBuddy 自主选择自己的演示文稿与网页能力。完整输入、回传证据、零内容指导和
最终验收要求见 `COLD_START_PROTOCOL.md`。

在 `verification-tmp/external-cold-start/external-delivery-receipt.json` 真实生成前，
本工程的准确状态始终是“外部 WorkBuddy 冷启动未执行”，不得用本机目录或测试适配器
替代。

## 哪些情况必须停

- 输入包含无权使用的客户材料、个人信息或第三方受限资产；
- 项目身份、权益、价格、学区、交付等关键事实发生冲突且无法按现有材料定级；
- 少于 3 条已成立且机制不同的超级竞争力；
- 平台不能返回可编辑产物、页面映射和真实 gap；
- 回传产物包含绝对路径、内部域名、凭据、缺页或无法解释的外部资源。

本仓库按 Apache-2.0 公开发行；使用、修改和再分发条件见 `LICENSE`，当前能力与
未验证边界见 `RELEASE_STATUS.md`。

## 继续使用真实项目

先复制虚构示例目录，再只替换你有权使用的输入和语义核。保留字段、ID、状态和
缺口语义；不要把示例结论、竞品或数字平移到真实项目。真实项目接入与 WorkBuddy
冷启动属于 RC1 本地闭环之后的验证，不由本次虚构回执冒充完成。Apache-2.0 允许
使用者自行适配，但许可证本身不构成真实项目效果或客户验收承诺。
