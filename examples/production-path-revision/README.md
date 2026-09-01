# 语义变化与定向重投影教程

本教程承接 `examples/production-path-tutorial/expected` 的 `SEM-QC-001`。一份新的虚构正式材料确认：首层园林到地下会所之间包含一段露天路径，因此旧判断“全天候连续归家”不再成立。

正确处理不是只改页面标题，而是：

1. 把新事实写入事实／冲突／缺口登记；
2. 在项目合同中覆盖旧判断；
3. 修订产物 1 的比较标准；
4. 复核产物 2，记录购买任务不变；
5. 将语义版本升为 `SEM-QC-002`；
6. 用 `SC-DAILY-ROUTE`取代 `SC-CONTINUITY`并重新通过五项检查；
7. 同步第二章、第三章、UE交接和产物5目标；
8. 只重做受影响的路径内容，SC-ACCESS和SC-FLEXIBILITY保持不变。

运行：

```bash
python3 scripts/verify_revision_tutorial.py examples/production-path-revision
```

该检查只验证更新顺序、覆盖关系和影响范围，不评价新战略是否专业。
