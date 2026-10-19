# 个人API可选审批备注修复发布 r1

## 身份与边界

2026-10-19 18:54（Asia/Shanghai）准备，负责人/核验Codex。关联[任务](../tasks/2026-10-19-personal-api-approval.md)/[方案](../plans/2026-10-19-personal-api-approval.md)；接续用户个人API上线任务及“审批新增api失败了”反馈。修复发布不代用户审批pending或签发Key。

生产CIDd5b76168fd4168de808f4df3d1b0e9ceaf8c7cdc1f19b9ebb1cd64fd3ee54627/image97c378c7，StartedAt2026-10-19T10:32:21.769109798Z。目标仅个人服务ai_gateway.py审批SQL：NULLIF(btrim(:comment),'')改btrim(:comment)，空备注按既有NOT NULL字段保存空字符串。无生产DDL/配额修改/历史回写，其他源码和配置保持。

## 构建与验证

- 当前实际ai_gateway SHA2db168c87aa7e0a8dcb1dfb5b8bd37d15de84cd9a1e42cb617811b86b6badd76；候选SHA d62df8ee29cb5e0a00dc66f94ecafaf1fea4295d34bdc040676f2529487cf78a。源码两处规范换行后均与候选一致，候选仅一处字节替换。
- 生产镜像真实隔离PG/socket HTTP Red：空/省略/空格备注通过与拒绝6 failed，文字和权限并发3 passed，错误500/IntegrityError。Green11 passed，含事务故障回滚、原配额不降、第二Key创建/第三Key拒绝、指定审批人边界和并发。
- Green-r1测试设施误把PG临时Unix socket当最终ready，createdb前退出；PG已停止，业务测试未运行。Green-r2改为最终TCP readiness并全通过，旧证据保留，两个批次均不可重跑。
- 新driver SHA a245d980d9f242717d0fdd25ba309ba8002afb5d60f55489015d9891f039f891；22项发布故障/单次回退/名称隔离测试通过。镜像待构建，必须实际镜像独立测试后才可切换。

## 发布与回退步骤

1. 全新/srv/smartbrain/releases/personal-api-approval-20261019-r1；复用原成功online备份68dcec4071f04a6c806763d4d72a40d7，重新只读核验原清单/Invocation，自检和小文件独立SHA；不启动第二备份。
2. 实时四盘40/20/250/250GiB、内存、双锁、无pending、当前CID/image/unit/source全过后，构建单文件叠加镜像，不拉镜像/改基础层。
3. 实际候选镜像+独立tmpfs PG通过审批及原注册/Key生命周期；固定镜像与收据。新发布unit只启动一次，旧发布r1–r4不重放。
4. 候选源码/registered_active/8/24/DB3/匿名401通过，连续两次无在途后单次停止旧current、保留旧容器、同配置新容器/网络/current精确绑定，更新writer inventory。
5. 失败切换前不动业务；切换后单次恢复旧应用/网络/unit/inventory，仍先排空、不杀长流。无DB恢复或Key状态倒退；生产实际回退尚未执行。
6. 独立核对实际源码、准入、公网、47Key及审批聚合、无关容器/edge，归档镜像/证据并校验，限定提交推送和E盘镜像。

当前生产尚未切换。真实用户登录审批需用户点击确认，隔离结果不冒充该闭环；online备份不是完整冻结恢复。
