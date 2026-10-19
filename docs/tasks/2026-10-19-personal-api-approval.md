# 个人API新增名额审批失败

- 任务：personal-api-approval-20261019；Codex；2026-10-19 18:50（Asia/Shanghai）；阶段生产服务器侧已验证，真实用户点击审批待确认。
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

## 2026-10-19 18:57 实际产物通过，单次发布运行中

18:55新镜像sha256:c49eadce37fbeb9b37dd04818c05060c00ac0bb5a2c8da21e8b8ef6d40ce2f5b构建exit0。18:56:21实际镜像独立PG/socket HTTP 12 passed（审批11＋原注册/Key生命周期1），无源码挂载覆盖；test b488a925/PG e86df208均停止exit0。原备份18:55重新只读核验36自检/31小文件SHA、原Invocation68d、登记20及容量通过，无新备份。

18:57:01独立基线1070容器，个人d5b76168/注册scope/app/proxy保持，0执行/0等待/DB0；47Key、3申请、1allowance聚合已固定。18:57:22只启动一次新unit smartbrain-personal-approval-release-20261019-r1.service，Invocation e966ae676a1d47f6bd365cc1783ce37d/MainPID2712943/Job11376776，首次activating。只观察原Invocation，不重复start。发布成功与实际用户审批仍待核验。

## 2026-10-19 19:00 实际发布完成与独立终验

- approval-r1于18:57:47 promoted，18:59:07原Invocation `e966ae676a1d47f6bd365cc1783ce37d`确认success/exit0/MainPID0/ControlPID0/Job空。当前个人CID `7db129b5287213a62de6ffbe69ce963290084ef8b5719fdb4ab4c5e4df8f58ee`，image `sha256:c49eadce37fbeb9b37dd04818c05060c00ac0bb5a2c8da21e8b8ef6d40ce2f5b`，StartedAt `2026-10-19T10:57:38.551642968Z`，RestartCount0。
- current unit active/running/enabled、Invocation `592821fb02894246845d2fe0d470761c`、PID2715299，writer inventory的CID/image/配置hash匹配。原d5b76168以本次rollback名称停止/断网保留，候选031e9470停止；7个本任务隔离测试/PG容器全部停止。无运行中发布/构建/测试runner，无新自动任务；所有已终态批次不重跑。
- 18:58:25独立实际源码SHA d62df8ee…与候选一致，scope/app/proxy原字节保持。实际生产函数中的btrim(:comment)提取后，在只读生产事务对空串、空格和文字参数求值通过；没有执行生产审批UPDATE。25个有效账号含旧名单外3个继续通过注册准入，8/24/DB3保持。
- 原47条Key指纹92286ee623b3d5708891f3a6faafb074、3条审批记录指纹9b05491045fff0cf69b4130e45243a16、1条名额记录指纹66d4498efa6cdda3783af0437e35f73e全部保持。没有代用户审批/新增配额/签发或撤销Key。
- 1069无关容器配置/代际全部保持，当前1072容器；edge双视图c22e68d9与原代际保持。实际nginx `/v4/ai-gateway/` 指向新个人服务的原alias personal-key-api-r1:8000；公网申请/审批GET匿名401，login/ready200、匿名keys/models/responses401；Windows9000员工直连403/内部标记匿名401保持。
- 18:58:32单次归档 `/srv/smartbrain-backups/backups/personal-api-approval-20261019-r1`：image.oci.tar.gz 193049253 bytes/SHA `131b1a615cfe6fea43190ead8b4e18dd4da628f7923110da7d99f6b639521691`，evidence.private.tar.gz 108675 bytes/SHA `10ac133714780a2aaa1184701c0c512a9273f74e546c3d8900c3838760e240ed`，均0600。18:59:07独立重新计算SHA/尺寸/权限，OCI index匹配当前镜像及全部64 blob/引用descriptor通过。
- 终验四盘free bytes 44885221376/33005629440/347032592384/271565533184，MemAvailable6697824256，原门槛通过；backup68d原成功批次/登记20保持，没有新备份、扩容、清理或生产DDL。
- 代码90ad8de已推official；本次文档/记录限定提交并镜像E盘，原三处dirty保留。证据：isolated-red.log、isolated-green-r2.log、isolated-image.log（12 passed）、release-tests.log（22 passed）、release-terminal.log、independent-after.json、public-approval-route.json、archive.log、final-readonly.json、checkpoint.json。
- **修复已上线且服务器侧验证通过；真实用户登录点击审批仍待用户确认。** 原pending未重放，用户刷新后可在不填备注的情况下再审批一次。完整冻结恢复、全部模型和30人容量未据此验收，生产实际回退未执行。
