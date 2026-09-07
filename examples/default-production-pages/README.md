# 默认生产代表页

这是从既有公开虚构教程抽取并重新编辑的页面片段，不是新完整项目。4页检查全屏真实地图、两侧卡片、大图案例、窗前观察与系统范围；所有点位示范均明确为虚构，不借地图宣称真实距离。

地图底图从此前已授权公开的20页参考PPT第5页原样提取，保持OpenStreetMap署名。案例图只从当前有效公开库按稳定编号读取，不另复制图片。

使用`tools/product3_assembly_console/scripts/export_approved_blueprint.py`导出本目录`assembly-input.json`，再按`tools/product3_ppt_pipeline/README.md`将导出的JSON与`page-content.json`传给真实默认计划与构建入口。没有项目专属生成器、Grist或预置成品替代生产。

正式新任务用自己的研究、判断、名称、点位、脚本和图片用途替换输入。代表页通过只证明这一读取与导出路径可用，不证明陌生项目首次交稿的业务质量已稳定。

产物1、2的两页输入分别为product1-content.json与product2-content.json，图片和来源在report-assets。通过tools/product12_reports的render_report、export_pdf、inspect_pdf依次生成；它们是原公开教程的局部表达示范，不是新增完整项目。
