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

## 增量补检

上游可以提出 `proposed_incremental_batch`，但不能替下游授权执行。住宅生产 Owner 结合覆盖、边际信息增益、剩余 gap 和本轮业务用途，选择：

- `authorize_incremental`：只授权已提出的查询，并写明批次、时间、成本或停止边界；
- `stop_search`：现有证据已足以稳定当前判断，或继续检索没有业务增益；
- `hold`：等待新材料、权限或更明确的业务问题；
- `not_applicable`：本轮不需要增量检索。

渠道按当次权限、可用性与缺口路由。某一渠道的临时健康状态、账号现场或本机路径不进入长期任务合同。

## 证据采用边界

- `fulfilled`只表示上游履行，不等于`accepted`；
- 非概率社媒样本只能进入个人公开表达、客户语言、比较线索或反例，不自动成为项目硬事实、总体比例或主流态度；
- 冲突不得静默择一，gap不得改写成“市场没有”；
- 上游不得裁定直接竞品、价值锚点、SC或甲方最终主张；
- 机器验证可以拒绝丢字段、越权推导和状态冒充，不能批准业务判断质量。

## 双包兼容

`cross-package-compatibility.json`登记双方独立仓库的Schema、哈希、黄金fixture与验证命令。住宅包已发布`v0.2.0-rc.2`公开预发行版，公开信息包仍处于候选状态；双方已经冻结接口并完成fixture往返，兼容状态仍为`compatible_candidate_frozen`。验证结果见`cross-package-conformance-receipt.json`，该回执保留接口冻结时的候选版本快照。任一Schema字节变化都必须更新哈希并重跑双方conformance；双方正式版本均发布后再升级稳定兼容状态。

住宅侧可运行：

```bash
python3 tools/production_core/validate_upstream_exchange.py \
  --request fixtures/upstream-exchange/request.json \
  --envelope fixtures/upstream-exchange/public-evidence-envelope.json \
  --response fixtures/upstream-exchange/response.json \
  --adoption fixtures/upstream-exchange/adoption-receipt.json
```

两套发行包不要求共享工作目录，不允许依赖另一工程的绝对路径、账号态或私有运行实现。
