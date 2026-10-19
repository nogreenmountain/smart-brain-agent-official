# 新账号个人 API 准入发布 r4

- 关联[任务](../tasks/2026-10-19-personal-api-registration.md)、[方案](../plans/2026-10-19-personal-api-registration.md)；负责人/验证人Codex。用户授权“已停止，切入生产”保持。
- 2026-10-19 18:32（Asia/Shanghai）准备中，尚未切换。发布与回退步骤、原业务/镜像/源码、无迁移和真实新号验收边界沿用[r3准备记录](personal-api-registration-20261019-r3.md)，仅全新r4目录/unit/候选/回退名称。
- r3因候选名称漏改而在preflight失败；原业务未停止。r4修正全部批次名称，driver SHA `67674809cd8b2e737181573fd9010b2679e46cd59c65ad585859eeca4088f800`。新增名称隔离测试Red明确复现，r4 22项全通过；不修改业务镜像。
- 镜像 `sha256:97c378c7e3f3d9a60cd00e5bdae53063da7814786695cef7f4caa4db6452edd4`；backup Invocation `68dcec4071f04a6c806763d4d72a40d7`，再次使用原成功批次与测试收据，无新备份/构建/生产Key创建。
- 上传先核对r3确切失败Invocation `4f064dcc591445fca1feb3aa340c1433`、只有failed阶段及旧业务与r2基线一致；新目录须不存在。启动仅一次，保留两次零在途、双锁、备份/四盘门槛和单次受控回退。之后仅观察原Invocation。
- 原配置/网络/HostConfig/长期流代理保持；正式app改为实时有效注册账号准入。无DB迁移/历史回写/Key重置。回退仅原应用/网络/unit/inventory，保留所有新增数据；真实生产回退尚未执行。
- 成功后独立核验实际源码、25个有效账号含3个旧名单外账号、47条Key聚合、无关容器/edge/Windows边界，并单次归档、文档镜像/推送。真实新号页面领取/模型使用尚待用户侧确认；online备份不冒充完整冻结恢复。

实际启动、发布、验收与归档结果随后追加；r1/r2/r3均终态不可重跑。

## 2026-10-19 18:39 发布完成与独立核验

- r4于18:32:05启动、18:32:30 promoted；18:36:42终态再核对：Invocation `28aca7cd84c641109c166c4bb1729b49`，success/exit0/MainPID0/ControlPID0/Job空。没有运行中发布runner，无新自动任务，r1–r4/start/归档均不可重跑。
- 当前CID `d5b76168fd4168de808f4df3d1b0e9ceaf8c7cdc1f19b9ebb1cd64fd3ee54627`，镜像 `sha256:97c378c7e3f3d9a60cd00e5bdae53063da7814786695cef7f4caa4db6452edd4`，StartedAt `2026-10-19T10:32:21.769109798Z`，RestartCount0。current unit active/running/enabled、Invocation `4c5bcafe67ea492d9a08edb95dfc7dbc`、PID2637747；writer inventory的CID/image/配置hash一致。
- 18:34:46实际scope/app SHA与候选一致，proxy SHA075b6501保持；健康membership_policy=registered_active、member_count=null，8执行/24等待/DB3，现场0执行/0等待/DB0。
- 使用实际生产app的browser_scope/require_user闭包及只读事务，25个有效账号全部通过，包括旧名单外3个。47条Key聚合指纹 `92286ee623b3d5708891f3a6faafb074`保持；本任务没有创建/撤销/轮换生产Key或主动模型调用。
- 公网login/ready200，匿名keys/models/responses401；Windows9000员工直连403、内部标记匿名401。1060个无关容器配置/代际逐一保持，edge原CID/StartedAt及宿主/实际挂载c22e68d9保持；当前1063容器。
- 原CID052676a8以本次rollback名称停止/断网保留，r4候选12d5a848停止。新容器Env/Cmd/HostConfig/网络保持，仅镜像/hostname及本次scope标签变化；无DB迁移/历史回写/批量重启，生产实际回退未执行。
- 18:35单次归档 `/srv/smartbrain-backups/backups/personal-api-registration-20261019-r4`：image.oci.tar.gz 193005201 bytes/SHA `70ef35f66e026d69707951cb3b621cccb7ea3289e2f3083126364e6347c6d3ca`；evidence.private.tar.gz 94794 bytes/SHA `01188dc03817a32ac6dbe85be21ec587302531d9cae31eff52af4dfab94dfb30`；均0600。
- 18:36:42独立重算两个归档SHA/尺寸/权限，OCI顶层index匹配生产镜像；62个blob及62个引用descriptor的SHA/尺寸通过。原成功online备份68d保持；四盘free bytes 44895653888/33006809088/347225763840/271495798784，内存可用6575812608，原门槛通过。
- 核验工具失败保留：初次after假设扁平FastAPI路由而失败，后按实际_IncludedRouter.include_context依赖核验通过；首次归档检查误把Docker29 OCI index ID当config digest，后以实际index/全部blob校验通过。未改业务或归档以迎合检查。
- 发布准备1aadebe/bff67d8已推official；e7705da仅保存启动checkpoint，提交标题不能代替最终发布证据。本段为实际收尾记录，限定提交并镜像E；三处原dirty保持。
- 证据：`.artifacts/personal-api-registration-20261019/{release-r4-started.log,release-r4-observed-final.log,independent-after.json,independent-after-verified.log,archive-r4.log,final-readonly-r4.json}`；服务器r4/evidence保留对应终态。
- **生产部署及服务器侧核验完成；真实新号登录页面领取Key、使用模型仍待用户侧验收。** online备份不是完整冻结恢复；不宣称全系统恢复/30人容量或全部模型已验。下一步用户刷新个人API页面尝试创建，原个人Key继续使用公网唯一入口。
