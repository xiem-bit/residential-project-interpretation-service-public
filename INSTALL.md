# Codex安装与自检

这套公开包的推荐安装方式是完整克隆仓库，并把仓库根目录作为Codex项目打开。`AGENTS.md`、现行生产Skill、业务合同、机器门禁、黄金参考和学习反馈必须一起存在；只复制PPT模板、网页源码或单个Skill无法继承完整能力。

当前公开预发行标签为`v0.2.0-rc.3`。`v0.1.0-rc.1`只代表历史载体演示，`v0.2.0-rc.1`已由CI修复版`rc.2`取代。推荐固定标签安装：

```bash
git clone --branch v0.2.0-rc.3 \
  https://github.com/xiem-bit/residential-project-interpretation-service-public.git
cd residential-project-interpretation-service-public
python3 scripts/check_environment.py --profile production-core --run-tests
```

doctor显示`pass`后，在Codex中打开这个目录。Codex会从根目录`AGENTS.md`进入；新的住宅研究再按`START_HERE.md`和`workflows/residential-production-orchestrator/SKILL.md`从已授权原始材料开始。

## 一、安装层级

| 目标 | 命令 | 依赖与结果 |
| --- | --- | --- |
| 住宅研究主链 | `python3 scripts/check_environment.py --profile production-core --run-tests` | Python 3.9+；验证入口、业务Harness、参考库和发行清单 |
| 产物3参考与适配输入 | `python3 scripts/check_environment.py --profile product3 --run-tests` | 验证当前20页黄金、三份历史原稿、124文件模板资产、229文件案例素材库与写作参考；PPT生成引擎由终端用户另行安装并现场确认 |
| 产物5源码与运行 | `python3 scripts/check_environment.py --profile product5 --install-node-deps --run-tests` | Node.js 20+与npm；安装锁定依赖并完成构建、交互和静态包测试 |
| 全包试装 | `python3 scripts/check_environment.py --profile full --install-node-deps --run-tests` | 同时验证主链、产物3黄金参考和产物5运行时 |

不需要产物5时无需安装Node依赖。产物4不在本次发行范围，doctor和初始化器都不会提供其入口。

## 二、第一次使用

1. 把本次有权使用的项目材料放进独立项目工作目录；除仓库已登记获授权参考资产外，不要把新客户资料提交到公开仓。
2. 在Codex中明确任务模式、业务问题、受众和需要启用的产物。
3. 让Codex先读取根入口和当前原始材料，再建立轻量项目合同。
4. 新住宅研究默认形成产物1；产物2、3、5按业务问题启用。
5. 机器检查通过后继续专业语义审查和真人业务验收；文件生成、视觉通过、发布与业务效果分别记录。

可先用两套公开安全项目确认安装完整：

```bash
python3 scripts/verify_production_run.py \
  examples/production-path-tutorial/expected --mode tutorial

python3 scripts/verify_production_run.py \
  examples/end-to-end-public-safe/fictional-wangchuan-xu/expected --mode tutorial
```

## 三、能力不足时怎样回传

某台电脑缺少演示文稿能力、Node、浏览器、渠道授权或其他外部能力时，住宅业务主链继续完成可完成部分，并使用`templates/平台适配与能力缺口回传.template.json`记录：

- 缠在哪个载体或外部能力；
- 已经完成哪些业务输入；
- 缺什么环境或授权；
- 建议怎样补齐；
- 是否阻塞住宅业务核。

`gap`不等于住宅战略失败。doctor通过也不等于Codex已经理解业务、真人已经接受、成果已经发布或产生业务效果。

## 四、终端用户自行安装与登录的能力

公开包提供业务方法、参考资产、消费合同和自检，不捆绑以下外部软件、插件或个人账号状态：

1. **PPT生成引擎**：终端用户自行安装或启用支持读取、编辑、渲染和导出PPTX的专业演示文稿能力。安装后先用本包20页黄金稿完成“打开—渲染—另存副本—逐页检查”；doctor只验证PPTX包和参考资产完整，不证明专业引擎可用。
2. **Grist**：只有需要完整真人可视装配裁定时才安装。公开包不携带本机定制Grist控制台；终端用户自行安装Grist，并用本包页面语义、逐页标注和装配字段建立项目级控制表。没有Grist时，Agent仍可用同一字段形成完整非空白预排，再由真人通过普通文档或表格裁定。
3. **Computer Use、浏览器与地图**：终端用户自行安装或启用对应能力，并在本机完成权限授权。安装状态只证明工具存在，具体网站能否使用仍以当次页面和权限为准。
4. **微信、小红书及其他登录型渠道**：账号、Cookie、token、二维码登录态和风控状态不随包迁移。终端用户在自己的客户端或浏览器中自行登录；出现验证码、安全提示、权限不足或会话不可回读时，停止对应渠道并返回真实gap。
5. **发布与云环境**：域名、服务器、云账号和发布权限由终端用户自行配置。包内本地演示成功不等于已经对外发布。

终端首次启用任一外部能力时，把“已安装、已授权、真实任务可用、载体通过、真人接受”分别记录，不用前一层替代后一层。

## 五、升级与版本边界

- 公开仓固定提交和后续标签是发行权威；不要把其他电脑的零散复制件当成新版本。
- 更新前先确认当前分支、未提交改动和发行状态，再用Git取得新提交。
- 真实材料、账号、Cookie、token、浏览器登录态、云端发布配置和渠道健康状态不会随包迁移。
- 产物4将在上游大修完成后由后续版本重新评估，当前安装不得从历史标签恢复旧入口。
