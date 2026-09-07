# 产物1、2报告实现复用

本工具从翠湖2026-09-05终稿的渲染函数、CSS、导出与PDF检查提取，只移出项目标题、文件名、来源装载和目录。`blocks_p1.py`、`blocks_p2.py`保留原块职责，`styles`保留既有版式；没有自动研究、编辑或验收能力，不是通用报告平台。

## 输入与运行

Python 3、Node、Playwright及Chrome用于渲染和导出；PDF检查用pypdfium2和Pillow。先通过当前环境的依赖查询取得实际路径，或使用本机已安装运行时。`NODE_PATH`指向实际Node包目录；不在代码中保存维护者绝对路径。

输入JSON只组合现有信息：

```json
{
  "meta": {"title": "报告名称", "header": "顾问机构", "footer": "项目 · 报告", "date": "资料日期"},
  "sources": {"S1": {"title": "真实来源名称", "url": "实际链接或报告内相对存档", "label": "必要说明"}},
  "pages": [{"section": "章节", "title": "当前判断", "lead": "解释关系", "layout": "comparison", "refs": ["S1"], "blocks": [["p", "当前项目正文"]]}]
}
```

`pages`沿用样例页面块，可读两个blocks文件中的hblock/mdblock确定已有参数。产物1引用为`["quote", "忠实节选", "实际来源链接"]`；产物2引用为`["quote", "忠实节选", "人物或材料说明", "S1"]`，来源由sources装载。产物1图片`fig/photo`按assets内相对路径；产物2`image`按HTML相对路径（如assets/位置.svg）。图片及本地来源随本报告资产目录提供，不从样例项目隐式读取。refs与links必须使用存在的来源键。

```sh
python3 tools/product12_reports/render_report.py input.json --kind p1 --assets <本案素材目录> --output <新报告目录>
node tools/product12_reports/export_pdf.cjs <新报告目录>/report.html <新报告目录>/output/pdf/report.pdf
python3 tools/product12_reports/inspect_pdf.py <新报告目录>/output/pdf/report.pdf input.json --output <新报告目录>/qa
```

产物2使用`--kind p2`。输出目录必须为新目录，避免覆盖定稿及手工修订。修改已有输入后导出到新目录；页面数与内容量由任务决定。导出阻断网络请求，正式图像应使用本地资产。图片加载、横向边界和页脚间距未通过时停止导出；PDF检查页数、页码、实际全文并生成预览，最终仍须实际看每页文字、图片和版面。

## 编辑与交付

正式排版导出前完成references/writing/16全文编辑，可先用草图组织内容。A级扫描含主副标题的`qa/assertions.txt`，B级对`source/report.md`执行现有扫描的`--report-only`；人工回读语义，原声允许忠实节选并保留必要条件。配图按本页信息表达或论证作用评价，不要求每图独立证明竞争结论；产物3、5白名单不受影响。

本机及分享版本编辑依赖见[工程中文编辑技能](../../workflows/chinese-affirmative-business-editor/SKILL.md)。仅生成文件不等于编辑通过、用户接受、真实项目研究完成或公开发布。
