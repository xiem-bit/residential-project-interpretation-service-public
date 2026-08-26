# WorkBuddy 路由

若目标是复刻住宅生产流程，先把 WorkBuddy 作为 `business_orchestrator`：只给固定公开候选、`START_HERE.md`和原始输入，让其自主读取公开 Skill 并完成全部业务输出。不要先要求它生成 PPT。

业务输出通过机器合同后，再按需把 WorkBuddy 作为 `carrier_adapter`调用其演示文稿或网页能力。第二次调用的结果只进入 `adapter_statuses.workbuddy.presentation`或`adapter_statuses.workbuddy.web`。

旧 RC1 的 WorkBuddy 外部冷启动只验证第二类调用，不能作为第一类调用的通过证据。
