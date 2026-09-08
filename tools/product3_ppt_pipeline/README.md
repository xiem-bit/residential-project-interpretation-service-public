# 产物3装配清单到PPTX生产管道

默认消费已裁定装配清单和当前项目页面内容，按已指定的结构生成原生可编辑PPTX，再从这份PPTX回读文字、导出预览和PDF。Grist已退出当前依赖。业务判断、指定视觉要求和图片用途由现有甲方编辑与逐页看图检查承担；工具负责装载与同版核对。

## 当前默认入口

1. 读取当前项目合同、已编辑正文及[页面模板库](../../references/product3/assets/产物3页面模板库/README.md)中的适用参照。沿用既有可视预排与裁定，不增加审稿轮次。
2. `approved_装配清单.json`仍是正式内容真值；`页面内容.json`只记录其逐页标题、正文分组、布局与素材位置，不保存第二套有效判断。`plan_production.py`按页面ID对应两者，绑定素材清单中的原图及指纹。
3. `build_or_patch_deck.mjs`使用Presentations按当前内容装配；装载后的全部文字必须与冻结清单相同，允许换行和空白变化。程序不从“这一页只负责／演讲动作／制作规划”补正文，这些内容只进入备注。
4. 同一入口重新导入导出的PPTX，形成页面预览、对象映射、实际可见全文及原有检查记录。`verify_production.py`包含副标题、卡片、地图标签和页底文字的核对；实际图片按绑定指纹和页面引用核对。可选PDF直接由同版预览生成，不另排一套。

```bash
python3 tools/product3_ppt_pipeline/plan_production.py \
  <approved_装配清单.json> --content <页面内容.json> --out <production_plan.json>

node tools/product3_ppt_pipeline/build_or_patch_deck.mjs \
  --plan <production_plan.json> --out-pptx <新版本/output/方案.pptx> \
  --mapping <新版本/mapping.json> --preview-dir <新版本/preview> \
  --layout-dir <新版本/layout> --montage <新版本/缩略图.png> \
  --work-dir <新版本/.build> --pdf <新版本/output/方案.pdf>
```

`node`使用当前桌面依赖返回的Node；配置`RUNTIME_NODE_MODULES`、`RUNTIME_PYTHON`及当前安装的`PRESENTATIONS_SKILL_DIR`，不硬编码维护者路径。按Presentations Skill在本次首次创建前登记产物操作。最终文件使用新路径，不覆盖父版。生产计划重跑既有输入校验，构建时再核对清单版本，不能绕过批准输入。非生产小样须明确`fixture_only=true`并使用`--allow-test-fixture`，其通过不等于用户验收。

### 页面内容与版式

沿用两项目的页面内容结构：每页包含`id / order / semantic / title / sub / layout / body`。`chapter_label`和`footer`是实际可见文案，也应进入清单的`页面文案`。`body`只放本页需要的可见内容；后台依据、UE引用和讲稿继续维护在现有合同及装配字段。

项目适配入口直接消费当前认可正文，不先生成旧业务稿再层层修正。有第二章合同的项目，在既有装配输入保留`chapter2_contract_path`；现行导出记录`reviewed_chapter2_basis`，事实记录发生实质变化时，沿原有引用及页面职责返回受影响页到`draft_装配清单.json`。Owner在原论证位置复核标题、判断、图表、讲稿和制作内容，再沿用现有批准字段；不因编号相同继承旧批准，也不重审未受影响页面。纯空白修改不触发事实复核。

忠实引用在装配页保留`原文引文`，每段包含`field`（页面名称或页面文案）、精确`text`、`source`和本页`purpose`。词法检查只扣除这段已标识原文，自写内容仍检查；引文是否适合本页仍由原有语义审稿判断。当前生产只核对正在使用的共享素材订正或退出，合法项目新增图保持独立身份，历史交付不自动刷新。

| 适用版式 | 当前内容用法 |
| --- | --- |
| `map` | `map`提供已核阅真实底图、图形编号、1600×900取景及同视窗点位；`body.map_cards.left/right`和`map_meta/conclusion`装载两侧卡片、精度说明及比较结论。底图按当前空间证据取得，编号须在本页“本项目图形”中登记；不把一个截图按所有页面拉伸，不猜坐标。 |
| `gallery` | `body.pairs`为两组`[CASE编号,本案价值题头,本案正文]`，`steps`为已有业务短句。大图槽与留白沿用已认可实现；原图从共享清单解析，不凭编号记忆选图。 |
| `scope` | `body.levels / scope_heading / included / conclusion`说明系统内容与用途，生产端基准保持；这类前台内容不按“出现系统词”删除。 |
| 其他既有组合 | `cover / choices / anchor / sequence / overview / ai / close`沿用同目录`compose_project_pages.mjs`的明确内容槽；标题、封面行、收口句和页底均由本案输入，不能继承原项目硬编码。缺少某种布局时定点补充现有实现，不退回整页复制。 |

页面语义与布局分开；同一语义可以按当前裁定使用不同布局。既有空间页、双图页的指定信息层级保持，几何参数在实现中维护，不要求每个任务量尺寸填表。已有模板没有覆盖的专用页面仍需局部实现；本工具不是任意PPT自动改写器。

地图文件路径相对页面内容文件，或使用绝对路径。地图输入保留真实底图、点位来源、坐标系及精度。板块范围与项目中心必须有相称依据，开发位置示意不能当红线。视窗应按本页对象安排，中央关系不被两侧卡片遮挡。工具不会从缺失坐标推导地理事实。

### 实际检查出口

现有`.build/production_receipt.json`同时指向以下输出：

- `实际可见文案.json`和`全部实际可见文字.md`：从实际PPTX读取，原声保留；
- `A级标题与核心判断.txt`：包含主副标题和核心结论；
- `B级实际可见全文.txt`：全部自写文字，供现有`--report-only`扫描；
- 同版逐页PNG、布局JSON、PPTX及可选PDF。PDF采用逐页画面，文字检索用原生PPTX或全文出口。

图片内固有文字仍需看原图和实际页面；文字一致、图片指纹相同不证明选图或营销判断正确。按references/writing/16第8节执行原有语义审读，保留来源身份与本案事实边界。已知问题修好、关联内容同步且实际输出正确后提交，不无限寻找低价值疑点。

## 局部修订与历史路线

- 只改字句或同用途换图，更新当前内容和既有清单，重建受影响部分或调用`patch_existing_deck.mjs`；保留新版本，不重开语义冻结。改变观看对象、功能或范围时，同步现有页面论证、制作项及讲稿。
- 仅补后台交接时，现有修订请求支持`replace_notes`（`page_id`、`text`）。备注内容从实际合同与适配入口生成，应说明本页表达、展示内容、共用制作项和讲稿重点。全为此动作时只回装SDK生成的备注正文，并核对其余PPT组成文件与父版相同；前台不变的PDF及视觉证据可沿用，不重做全部产物或真人验收。
- `verify_patch.py`核对定向修订之外的页面；`refresh_external_parent.mjs`与`verify_external_refresh.py`处理外部父版接续，实际原生应用兼容性只按真实检查结果报告。
- 历史单来源／多来源starter、`pptx-automizer`和技术夹具继续保留。`reuse_source_slide`只用于显式技术夹具；任意历史PPT的`reuse_structure_rewrite_copy`仍未闭合，不能冒充当前内容默认路线，也不能把来源原文整页带入新项目。
- 公司章节只按任务启用，当前内置组合承接第二／三章；第四章不默认制作。完整系统开发、S3原型、AI推荐官实时能力均不由PPT导出证明。

公开包的可运行输入见[默认入口代表页](../../examples/default-production-pages/README.md)。它只验证代表布局与装载，不替代完整项目研究或真人验收。

三／四项内容：`anchor`、`overview`、`sequence`沿当前原生入口分别承接三项与四项，三项保持现有组织。家庭总览必配人物肖像：装配页沿用`case_slots`登记人物版位`id/purpose/asset_id`，内容用`family`的`body.pairs`逐位装载（2—4位）；已有双图`gallery`对应两位。实际版位及绑定必须与已裁定输入一致，不以标题中的家庭数量或删改版位绕过缺图。
