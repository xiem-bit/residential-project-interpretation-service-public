# 外部上游能力合同

本目录把住宅生产核心与公开信息、机构数据、甲方资料和专家能力分开。上游负责按冻结任务检索、回传证据和说明缺口；住宅生产 Owner 负责接受／拒绝用途、决定是否补检，并最终裁定直接竞品、价值锚点与超级竞争力。

## 标准闭环

```text
residential.upstream_task.v0.2
→ public_evidence_envelope.v1
→ residential.upstream_response.v0.2
→ residential.upstream_adoption_receipt.v0.2
```

四层职责不得合并：

1. `upstream-task`冻结业务问题、判断缺口、对象身份、证据职责、接受口径、精确查询、执行下限、增量授权和停止线；
2. `public_evidence_envelope`由公开信息包生产，保留来源、证据层级、负命中、冲突、缺口、充分性和停止原因；
3. `upstream-response`只登记上游履行状态、证据包哈希和充分性回执，不得声称下游已经采用；
4. `upstream-adoption-receipt`由住宅生产 Owner 独立记录接受用途、拒绝原因、未解冲突／缺口、判断影响和下一轮增量授权。

## 首轮检索与充分性

真实研究检索默认在执行前明确：

- `acceptance_mode`：数量、质量充分或混合；
- 合格类别与质量条件；
- 来源角色／项目／品牌多样性；
- 每个冻结查询的结果批次与实际开读下限；
- 支持证据、反例、负命中和冲突的保留方式；
- 达到充分、边际增益耗尽或触发安全／权限边界时怎样停止。

已知 URL、指定文档、单一事实或精确记录获取可以使用简单定向获取，但必须有人工豁免；只要任务涉及多查询、支持与反例、来源多样性、比较模式、增量可能或市场外推，就不得借豁免绕开研究充分性。

## 增量补检与原请求保护

同目标、同对象、预算内的继续检索服从有效任务授权；`in_scope_iteration_allowed=false`明确禁止范围内继续，字段省略也不能覆盖任务原文里的停止限制。`execution_authorized`表示范围外扩展的授权状态，不把历史`false`自动改成`true`。上游执行前自行冻结本批精确查询。

住宅生产 Owner 在用户已有授权范围内选择`authorize_incremental`、`stop_search`、`hold`或`not_applicable`，在独立采用回执中记录理由与执行边界。Owner的条件采用不等于真人验收。超出用户批准的对象、预算或动作范围时取得用户新授权；不能以改写旧请求或更换写入方式绕过平台拒绝。

## 冻结请求贯穿执行与回包

原请求是对照依据，不能从回包反生成请求。上游通过确定性接口读取住宅`acceptance_contract`、对象与停止条件，执行和封装均与原件核对。新证据包的`contract_binding`包含原请求指纹、完整验收条件及实际充分性输入指纹。只有数量超过门槛不能代替质量、资格及多样性；冲突和缺口不直接计入合格证据。

住宅校验默认要求绑定；提供`--sufficiency-input`同时核对实际充分性输入。旧无绑定回包仅可通过`--allow-legacy-unbound`做结构只读审阅，此模式不能生成采用通过。恢复旧任务时保留原request与已有材料，上游按原合同重算充分性并重包，再由住宅侧条件采用。部分充分可以合法回传，不改写成充分，不自动启动新增检索。

原request由住宅侧维护并冻结；上游在自己的授权目录产出证据包和充分性输入，住宅侧在自己的项目目录产出response和adoption。双方传递可移植文件与引用，不把对方目录当默认写入目标。

## 证据采用边界

- `fulfilled`只表示上游履行，不等于`accepted`；
- 非概率社媒样本只能进入个人公开表达、客户语言、比较线索或反例，不自动成为项目硬事实、总体比例或主流态度；
- 冲突不得静默择一，gap不得改写成“市场没有”；
- 上游不得裁定直接竞品、价值锚点、SC或甲方最终主张；
- 机器验证可以拒绝丢字段、越权推导和状态冒充，不能批准业务判断质量。

## 双包兼容

`cross-package-compatibility.json`登记双方固定版本、Schema及哈希。当前联动以执行前已冻结的住宅请求为起点，经上游转换、充分性校验和封装，再由住宅校验；历史回执保存在`conformance-history/`，不代表当前修复已经通过。

住宅侧可运行：

```bash
python3 tools/production_core/validate_upstream_exchange.py \
  --request fixtures/upstream-exchange/request.json \
  --envelope fixtures/upstream-exchange/public-evidence-envelope.json \
  --response fixtures/upstream-exchange/response.json \
  --adoption fixtures/upstream-exchange/adoption-receipt.json \
  --sufficiency-input fixtures/upstream-exchange/sufficiency-input.json
```

两套发行包不要求共享工作目录，不允许依赖另一工程的绝对路径、账号态或私有运行实现。
