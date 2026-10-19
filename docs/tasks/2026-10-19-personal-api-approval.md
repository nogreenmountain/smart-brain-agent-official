# 个人API新增名额审批失败

- 任务：personal-api-approval-20261019；Codex；2026-10-19 18:50（Asia/Shanghai）；阶段排查/隔离复现，生产修复未发布。
- 来源：用户在新账号修复上线后反馈“审批新增api失败了”，继续修复本次个人API上线闭环；不代用户审批、创建/撤销Key或修改账户。
- 权威目录C:/Users/test/.codex/worktrees/deb4/智慧大脑agent - 服务器端；分支codex/project-memory-no-adapter；基线36954daac3dc7a19c4c23e01deb74732d4615ccd。原三处dirty保留，不夹带。
- [方案](../plans/2026-10-19-personal-api-approval.md)，证据.artifacts/personal-api-approval-20261019。

## 18:47只读现场

- 个人CIDd5b76168/image97c378c7/StartedAt10:32:21.769109798Z保持；实际ai_gateway.py SHA2db168c87aa7e0a8dcb1dfb5b8bd37d15de84cd9a1e42cb617811b86b6badd76，审批SQL仍NULLIF(btrim(:comment),'')。
- 生产review_comment为NOT NULL/default空字符串；前端备注可选，空备注参数为空字符串；这会在数据库写入NULL，待隔离复现。
- 审批者聚合1账号/1管理员/1有效；pending1（10月17日创建）、approved2；allowance1行/总额1；47Key指纹92286ee623b3d5708891f3a6faafb074保持。没有生产写入。
- 初始日志解析无匹配审批事件，不据此断言没有错误。current健康registered_active/8/24/DB3、现场0/0/0；原备份68d成功，四盘储备通过。
- 隔离Red使用全新personal-api-approval-20261019-red-r1身份、现有PG镜像/tmpfs/无网络出口；实际生产业务镜像，无源码覆盖。测试/PG终态待核对；不能重跑已创建批次。

后续：核对Red结果后最小修复，隔离Green及实际产物测试；不重放生产pending审批。注册修复r1–r4/扩容/清理/原备份/归档均禁止重跑。

## 18:54 根因/候选

当前生产镜像+真实隔离PG/HTTP复现空备注6 failed/3 passed；NULL写入NOT NULL导致IntegrityError/500。候选单行改btrim(:comment)，保持原约束；Green11 passed，权限/并发/失败回滚/配额/实际创建通过。Green-r1测试PG临时socket竞态失败保留；r2最终TCP readiness后通过，两原测试与PG均停止。正式源码两处/候选仅一行差异，SHA d62df8ee…；发布工具22 passed，准备新approval-r1，生产尚未变更。
