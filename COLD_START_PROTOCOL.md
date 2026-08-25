# WorkBuddy 外部冷启动协议

本协议验证“陌生使用者从公开 GitHub 固定 RC 获取工程，并让 WorkBuddy 自主完成平台适配”。
本机 `run_rc1_demo.py` 的测试适配器只证明公共接口可往返，不能使本协议通过。

## 冷启动入口

- Public repository：`https://github.com/xiem-bit/residential-project-interpretation-service-public`
- 固定版本：`v0.1.0-rc.1`
- 使用者只获得仓库地址、tag 和 `START_HERE.md`；
- 不提供私有工程、历史聊天、本机 RC1 目录或项目内容口头教学。

网络和系统依赖可获得基础设施协助，但必须记录次数。公开仓无需访问授权；任何
解释住宅方法、页面答案、文件消费顺序或替 WorkBuddy 选择 Skill 的提示都计入内容
指导；首次正式冷启动要求内容指导为 0。

## 第一步：从 GitHub 固定版本取得工程

```bash
git clone --branch v0.1.0-rc.1 --depth 1 \
  https://github.com/xiem-bit/residential-project-interpretation-service-public.git
cd residential-project-interpretation-service-public
```

运行本地参考闭环：

```bash
python3 scripts/run_rc1_demo.py --install-node-deps
```

这一步只验证下载、安装和公共核心，状态仍是 `local_fictional_e2e_pass`。

## 第二步：准备平台交接包

```bash
python3 scripts/prepare_external_cold_start.py
```

WorkBuddy 从下列文件开始自主选择自己的演示文稿和网页检查能力：

- `verification-tmp/external-cold-start/contracts/presentation-request.json`
- `contracts/presentation_response.schema.json`
- `contracts/capability-routing.json`
- `verification-tmp/external-cold-start/product5/site/index.html`

公共核心不提供 WorkBuddy 的 Skill 安装路径。WorkBuddy 应从自己的能力商店或环境
选择适合的演示文稿、网页预览或原型能力，并保持项目、页面、证据与超级竞争力 ID。

## 第三步：WorkBuddy 返回真实平台产物

必须写入：

```text
verification-tmp/external-cold-start/
├── cold-start-observation.json
├── presentation/
│   ├── platform-response.json
│   ├── product3-workbuddy.pptx
│   ├── presentation-visual-review.json
│   └── previews/...
└── product5/
    ├── product5-visual-review.json
    └── previews/...
```

其中：

- `platform-response.json` 的 `status` 必须是 `complete`；
- `producer.platform` 必须明确为 WorkBuddy，且 `formal_visual_renderer=true`；
- PPTX 必须可编辑，页面／对象映射必须与请求完整一致；
- 每页预览必须登记在 `presentation-visual-review.json`，正式视觉结果为 `pass`；
- 桌面与手机页检查必须登记在 `product5-visual-review.json`；
- 能力缺失时返回真实 gap，本轮记录为部分完成，不能伪造通过。

准备命令会把三个模板复制到对应位置。测试者只填写观察事实；WorkBuddy 或实际生产
平台填写产物回传与视觉证据。

## 第四步：运行公共最终验收

```bash
python3 scripts/verify_external_cold_start.py --install-node-deps
```

成功标志：

```text
EXTERNAL PLATFORM COLD START: PASS
```

最终回执为：

```text
verification-tmp/external-cold-start/external-delivery-receipt.json
```

只有该回执同时出现以下状态，才能写成 WorkBuddy 外部冷启动通过：

- `formal_visual: pass`
- `cross_machine: pass`
- `workbuddy: pass`
- `content_guidance_count: 0`

该状态仍不等于真实客户项目验证、客户接受或业务效果。
