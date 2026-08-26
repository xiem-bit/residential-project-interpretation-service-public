# 青岚澄境竞争态势研究（全量虚构）

```json
{
  "schema": "residential.product1_competition_study.v0.2",
  "project_id": "fictional-qinglan-chengjing-production",
  "input_freeze_id": "INPUT-FREEZE-QC-001",
  "status": "product1_complete",
  "market_judgments": [
    {"id": "MJ-01", "claim": "本案不能用新区环境单独对抗成熟通勤，必须把通勤可接受、低密日常可用和家庭空间适配组成连续选择理由", "boundary": "本教程128—168平方米改善任务", "evidence_refs": ["E-MARKET", "E-VOICES"]},
    {"id": "MJ-02", "claim": "价格未公布使继续等待成为现实替代，售前阶段应先关闭空间适配判断并保持价格承诺边界", "boundary": "虚构项目预售前", "evidence_refs": ["E-VOICES", "GAP-PRICE"]}
  ],
  "competitors": [
    {
      "id": "COMP-BEIWAN",
      "name": "北湾府（虚构）",
      "role": "direct",
      "role_boundary": "128—143平方米、优先成熟通勤且预算盘交叠的家庭",
      "why_chosen": "既有轨道和成熟配套降低日常不确定性，是本案新区位置的强替代",
      "substitution_basis": ["lifecycle", "product_form", "price_band", "sales_window", "purchase_task"],
      "strengths": ["距既有轨道站约650米", "成熟商业和学校更集中"],
      "tradeoffs": ["容积率2.35", "连续园林—架空层—地下会所关系不是其主购买理由"],
      "evidence_refs": ["E-MARKET", "E-VOICES"]
    },
    {
      "id": "COMP-QIXIA",
      "name": "栖霞里（虚构）",
      "role": "direct",
      "role_boundary": "143—168平方米、优先低密与会所体验且预算盘交叠的家庭",
      "why_chosen": "更低容积率和已开放会所让低密体验具有当前可见性",
      "substitution_basis": ["lifecycle", "product_form", "price_band", "sales_window", "purchase_task"],
      "strengths": ["容积率1.20", "会所已开放"],
      "tradeoffs": ["距老城就业节点更远", "143平方米没有双套房切换条件"],
      "evidence_refs": ["E-MARKET", "E-VOICES"]
    },
    {
      "id": "ALT-WAIT",
      "name": "继续居住并等待",
      "role": "partial",
      "role_boundary": "价格和权益未正式公布前的行为替代",
      "why_chosen": "保留现金流和选择权，避免在关键信息未知时提前承诺",
      "substitution_basis": ["lifecycle", "price_band", "purchase_task"],
      "strengths": ["不立即增加现金流压力", "保留继续比较的权利"],
      "tradeoffs": ["跨城通勤矛盾继续存在", "父母短住与居家办公空间冲突继续存在"],
      "evidence_refs": ["E-MARKET", "E-VOICES", "GAP-PRICE"]
    }
  ],
  "competition_problem": {
    "adverse_belief": "青岚澄境只是距离更远、兑现更慢的环境型低密项目，价格未出时继续等待没有损失",
    "target_belief": "青岚澄境能让双向就业家庭在通勤可接受的前提下，把低密归家和三代空间弹性转成每天可使用、可提前验证的改善方案",
    "tangible_enemies": ["COMP-BEIWAN", "COMP-QIXIA", "ALT-WAIT"],
    "intangible_enemies": ["成熟配套单一标准", "低密只等于环境", "价格未出就无需关闭其他选择判断"],
    "evidence_refs": ["E-BRIEF", "E-PRODUCT", "E-ROUTE", "E-MARKET", "E-VOICES", "GAP-PRICE"]
  },
  "effective_boundary": {
    "geography": "澄川市东岸虚构比较样本",
    "customer": "双向就业、存在三代短住或居家办公矛盾的改善家庭",
    "area_and_price": "128—168平方米；绝对价格未知，只使用预算盘交叠这一有限条件",
    "product_form": "低密改善住宅",
    "purchase_task": "在通勤可接受的前提下取得低密日常与家庭空间弹性",
    "lifecycle_window": "本案预售前与两项目在售窗口",
    "rationale": "两个在售项目分别占据成熟通勤和低密可见性，继续等待占据价格纪律；本案必须在同一购买任务内重组比较标准"
  },
  "sc_candidates": [
    {"id": "SC-C01", "mechanism": "双向就业路径与低密空间的时间—空间组合", "support_refs": ["E-BRIEF", "E-VOICES", "E-MARKET"]},
    {"id": "SC-C02", "mechanism": "园林、架空层和地下会所的日常路径连续性", "support_refs": ["E-ROUTE", "E-VOICES", "E-MARKET"]},
    {"id": "SC-C03", "mechanism": "双套房与可变书房承接三代短住和居家办公，并把空间确认前置于价格决策", "support_refs": ["E-PRODUCT", "E-VOICES", "GAP-PRICE"]}
  ],
  "client_visible_conclusions": [
    "本案应放弃用新区环境正面对抗成熟通勤，改用双向就业路径与低密日常的组合进入候选",
    "本案应承认栖霞里会所已开放的优势，并用连续归家关系重设低密比较标准",
    "本案在价格未出阶段先证明家庭空间适配，让等待价格不再等于停止其他购买判断"
  ],
  "gap_refs": ["GAP-PRICE", "GAP-SCHOOL", "GAP-DELIVERY", "GAP-VISUAL"],
  "stop_search": {"value": true, "reason": "教程输入足以形成三条竞争机制；价格、权益和视觉缺口分别保留，不扩大为无界检索"}
}
```

## 竞争结论

北湾府凭成熟轨道与配套进入候选，栖霞里凭更低容积率和已开放会所赢得低密比较，继续等待凭现金流纪律阻断行动。青岚澄境无法靠“环境好”同时击败三者，它需要重设三个连续标准：位置是否同时服务两条就业路径，低密配置是否进入每天的归家路线，家庭空间是否能在价格确定前先完成适配判断。

## 本案答案

本案的竞争机会不在单一资源，而在通勤选择、低密日常和家庭弹性的组合。三个机制分别承担进入候选、赢得比较和促进行动，并都可以由现有项目事实与 UE 语义证明。

## 诚实边界

学校、步行距离、价格和交付均不进入正式承诺；两个竞品角色只在登记的面积、预算盘和购买任务内成立；六条合成声音不代表总体比例。
