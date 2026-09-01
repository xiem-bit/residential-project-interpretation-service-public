# 网页／原型适配器边界

输入来自产物 5 交互蓝图、语义核和 UE 交接。适配器负责技术实现、交互、响应式布局、静态包和运行验证。

网页不得新增 SC 或改写客户路线。视觉检查、浏览器运行和发布回执只进入 web adapter 状态。

`tools/product5_shell/`是当前唯一项目中立运行时，`examples/gold-product5-public-safe/`只登记公开安全黄金参考与QA证据，不复制第二套源码。真实项目按`workflows/product5-presales-focus/SKILL.md`替换配置、图片、客户路线和发布信息。

本地构建、浏览器复核、真人接受、外部发布和业务效果必须分别记录。没有真实HTTPS地址时不显示二维码；适配器不得为完成画面伪造公网地址。
