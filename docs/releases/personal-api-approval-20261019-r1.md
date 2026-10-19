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
