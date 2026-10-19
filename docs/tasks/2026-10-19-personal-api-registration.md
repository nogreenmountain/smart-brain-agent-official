# 新注册账号个人 API 准入修复

## 身份、范围与版本

- 任务：personal-api-registration-20261019；负责人：Codex；核对时间：2026-10-19 15:07（Asia/Shanghai）。
- 用户报告新号无法创建 API；目标为有效注册账号可查看名额、创建并使用自己的个人 Key，保留配额、跨账号边界与禁用/封禁/删除/匿名拒绝。
- 权威目录：`C:\Users\test\.codex\worktrees\deb4\智慧大脑agent - 服务器端`；分支 `codex/project-memory-no-adapter`，基线 `d7861a5cd39ff7f860ea489888e9b1e254ee0bc2`。
- 阶段：已验证（生产准入/运行/归档）；部署范围：生产；真实新号页面领取待用户验收。方案见 [实施方案](../plans/2026-10-19-personal-api-registration.md)。
- 原 dirty：relay-auth-20261017 发布记录、ai-work-record-projection-20261012 任务及未跟踪发布记录；保留且不归入本次提交。

## 已核对

- 15:07 当前个人容器仍 `052676a8caaf…` / image `28cd0714…`，StartedAt `2026-10-18T14:43:13.86527095Z`，current unit active/running/enabled，Invocation `c1554993c4ba4e9c85ce6fa887082f5e`。
- 实际 scope 在查询实时账号状态前要求用户位于固定名单。名单26人；当前25个有效账号中3个不在名单。截图账号auth/public各1、有效、名单不包含。服务器仅定向聚合查询，不导出账号列表/Key/正文。
- 原45条Key聚合指纹 `61a5646cfd1c1119890ac23233fda77a`，当时3执行/0等待/DB0，8/24/DB3保持。本任务未签发/撤销/轮换Key。
- Docker空闲42,832,199,680 bytes，低于40GiB门槛117,473,280 bytes；root/backup/cold达标。backup Invocation `2f043103ee9e4af7a4ccc62cbeebb2d0` failed/exit1/PID0，登记20，原因待查。不能使用昨晚成功状态作为今天门禁通过。
- 证据：`.artifacts/personal-api-registration-20261019/initial-readonly.json` 和只读源码副本；初次本地取证脚本字符串嵌套错误在SSH前失败，修正后实际只读成功。

## 后续与边界

1. 先以生产相同scope复现固定名单拒绝，补新账号及失效账号测试；保留异步代理/长流和公开唯一入口。
2. 注册模式按当前auth/public实时判定，旧名单模式仅供明确隔离/灰度调用，不默认为正式个人入口。
3. 查当前工作记录路由是否也受同一名单约束；有证据再确定最小变更范围。
4. 完成隔离PG和HTTP验证；门槛未恢复不构建/发布，不清理历史容器、日志或备份来掩盖。
5. 新发布需独立身份、实际备份/容量/维护门禁、无在途流排空及回退证据；旧发布/Windows边界/已终态清理不重跑。

运行任务：本任务取证已终态；其他进程状态仅以上述核对为准。Git未提交/推送；生产未变更。

## 2026-10-19 15:37 接续：候选通过、储备恢复、唯一备份运行中

- 本地旧入口明确复现新账号403；候选20项scope回归及路由静态合并22 passed/1 deselected。生产镜像＋只读挂载候选＋独立PG/真实HTTP组合测试1 passed；覆盖首Key、默认额度1、6并发仅1成功、跨账号404、旧/新Key认证、禁用/封禁/删除/匿名拒绝、撤销401及再次创建、8/24/DB3。浏览器session解码和模型响应为合成，不冒充真实登录或模型闭环。
- 15:20测试r3成功终态，test05dfa373/PGc0aa4e2c均停止；PG128MiB tmpfs随停止释放，无生产Key签发。r1日志驱动参数错误、r2runner替换范围错误均保留，不再启动；r3不重跑。发布状态机17项成功/故障/单次回退/准入健康测试通过。
- 15:29用户明确批准“允许增加2GiB，继续上线”；15:29:51仅将 `/dev/ubuntu-vg/smartbrain-docker` 从105226698752增至107374182400 bytes，并完成ext4在线扩展，free44945653760 bytes。原业务重启0。证据`storage-extended.json`及远端`personal-api-registration-storage-20261019-r1/stage.json=complete`，禁止重跑lvextend。
- 15:34完成9月15/16/17三个新目标的正式archive SHA及各1133文件逐一比对，相同；15:36 review、15:37执行前复核双锁/无活动backup/无pending/无容器与进程引用/元数据未变/无外部硬链接，移除的仅对应clickhouse-staging副本。释放33165008896 bytes（30.887GiB），正式备份归档/清单全部保持。今日目标与昨天已清理三目标不同；两批都不可重跑。
- 15:37:39动态容量checker通过后，仅启动一次新的online备份：Invocation `68dcec4071f04a6c806763d4d72a40d7`，初始Job11324206/ControlPID2135364/start-pre。**仍在运行，未验收成功；后续只观察此Invocation，不重启或启动第二批。** start-intent/started位于`/srv/smartbrain/acceptance/personal-api-registration-20261019-backup-r1/`。
- 实际proxy原始字节SHA仍`075b650186ad79cfec6b74eb8cb257ceabe8fee7426016f91308c1acb6cc09fe`；initial-readonly里`5b57721c…`是stdout文本换行规范化后的SHA，不是生产漂移。原始字节证据在`gates-readonly.json.source_bytes_sha256`。
- 公网ai-gateway/个人模型路由均指当前个人容器；独立workday读入口仍有自己的部署，当前任务不改变该服务或Windows。现有生产业务代码尚未切换，新账号问题仍待发布后用户验证。
- 下一步：核对上述唯一备份终态/归档清单和容量→构建两文件叠加镜像→实际镜像独立测试→无在途流时单次发布/核对。`deploy/personal-api-registration/release.py`为新发布入口，仅复用旧库的Docker/systemd原语，不执行旧promote/Windows脚本。

## 2026-10-19 15:55 发布前接续核对

- 15:49/15:52/15:54仍为原online备份Invocation `68dcec4071f04a6c806763d4d72a40d7`、MainPID2135368、Job11324206；PostgreSQL 1137679980 bytes和ClickHouse 9078287608 bytes已生成，其他归档继续，未终态，不重启。
- 本次代码与工具已限定提交并推送official：`89d5f61`、`e7d2991`、`77778be`。原三处dirty保持，不夹带。
- 自审复现回退工具未处理Docker名称前导`/`导致名称仍占用，新增Red后最小修正，最终21项通过；生产发布尚未执行，未发生线上回退失败。证据`release-rollback-red.log`/`release-rollback-green.log`。
- 已核对既有`validate_static_capacity`明确规则：动态备份预算在备份启动前检查并由该备份消费；备份后发布维持40/20/250/250GiB和内存储备，无需立即再留一份完整备份的瞬时预算。此处沿用既有门槛，未降低或跳过容量检查。
- 新r4实际镜像测试入口已准备，只使用新build镜像与独立tmpfs PG，不挂载scope/app覆盖镜像；尚未执行。后继发布/只读核验/归档入口已准备，均为新任务身份，旧终态runner不重跑。

## 2026-10-19 16:47 发布接续：镜像通过，等待空闲窗口

- 原online备份`68dcec4071f04a6c806763d4d72a40d7`已于16:40前成功终态，PID0/Job空。16:40:30核验36项自校验、31小文件独立SHA、归档根同inode、登记20和四盘储备通过；5大payload依赖精确Invocation自校验，未另做全库冻结恢复。
- 新镜像`sha256:97c378c7e3f3d9a60cd00e5bdae53063da7814786695cef7f4caa4db6452edd4`，tag `smartbrain/personal-key-api:2026.10.19-registration-r1`；scope SHA`2878fb16424cdd9d13e9442050971211a29631467914b8f624e3287c23db8534`、app SHA`c804ec8fdd3f3f8c6fbeb03ee5c280c2f493736e77838bc0134af6babe2ae1ad`。16:41实际镜像r4独立PG/HTTP组合1 passed，不挂载业务源码覆盖镜像；test f3248f2a/PG04624fe0均exit0停止，零生产Key/模型调用。
- 16:42:02原47条Key聚合指纹`92286ee623b3d5708891f3a6faafb074`；相比15:07的45条存在自然变化，本任务没有签发/撤销/改Key。1059容器新切换基线，edge双视图`c22e68d9…`保持。
- r1发布Invocation `c3b25e0450ce4c99aafdd64768c7b98a`于16:43:34 failed/exit1/PID0：候选健康通过，但60秒未排空，RuntimeError在cutover前触发；旧CID/StartedAt/配置/网络/current unit均保持。candidate06d8dc49已停；没有新业务CID、停止旧服务或实际回退。r1不可重跑。
- r1启动调用因缺少`--no-block`等待15秒超时；已按原ExecStart/源码SHA/Invocation读回并记录接受的原job，无重复启动。新r2入口明确使用`--no-block`。
- r2发布复用同一镜像/备份/真实测试收据，无第二次构建或PG测试；仅新批次身份与300次有界排空检查。原21项状态机测试在r2源上通过，driver已提交并推送`26a4f43`。r2根`/srv/smartbrain/releases/personal-api-registration-20261019-r2`，源码SHA`d93278ba620ba9d6bda16e307d11a99c59bb79cd1d3d9e584adc91d04d4b762c`。
- 16:46:44 r2启动一次：unit`smartbrain-personal-registration-release-20261019-r2.service`，Invocation `b37eea7487cd4d9e8282cb6ab74b8529`/MainPID2341302/Job11350409。16:47:27仍activating，candidate a976843c已验证并停止，stage source_health_verified，等待自然空闲；只观察原r2，不启动第三批。已提示用户暂缓新AI请求以完成安全切换。
- 证据：`backup-verified.log`、`build.log`、`isolated-pg-r4.log`、`independent-before.json`、`release-start-reconciled.json`、`release-observed.log`、`r2-uploaded.json`、`release-r2-tests.log`、`release-r2-started.log`；远端各自evidence保留。尚未称新账号线上实际领取通过。

## 2026-10-19 16:53 收尾：等待空闲窗口，修复尚未切入生产

- r2于16:51:59因300次排空检查仍有在途请求而在cutover前退出；Invocation `b37eea7487cd4d9e8282cb6ab74b8529` failed/exit1/MainPID0/ControlPID0/Job空，new_id=null。两次都是安全门槛拒绝，不是应用切换后故障；没有实际停止旧业务或执行回退。
- 16:53:02独立终验：原1059容器Config/HostConfig/image/代际全部相同，新增两个候选06d8dc49/a976843c均停止保留；当前1061容器。原个人CID052676a8/image28cd0714/StartedAt14:43:13.86527095Z/current Invocation c1554993与三源码SHA保持，47条Key指纹保持；edge双视图c22e68d9保持。
- 公网login/ready200、匿名keys/models/responses401；Windows9000员工直连403、内部标记匿名401；8执行/24等待/DB3保持，当前3执行/0等待。四盘空闲bytes为44910219264/33017987072/347418877952/271470034944，MemAvailable6580117504，backup原68d成功/登记20。
- 当前新号仍可能收到原固定名单403，不能称已上线或真实领取完成。已请用户暂缓新的个人API任务，等现有生成结束；既有上线授权保持，不需重新批准扩容/代码/镜像。无后台发布runner、未创建定时自动任务。
- 下一步：确认有可用空闲窗口→重新核对原CID/镜像/源码/current/Key与备份/容量→基于同一97c378c7镜像及r4测试收据，准备全新发布批次身份后单次切换，不能重跑已终态r1/r2。成功后独立核验实际registered_active准入/入口/Key/无关容器，并归档实际发布镜像与证据。
- 尚未执行生产镜像归档和实际生产回退；原备份是online，不是完整冻结恢复合格点。`independent-blocked.json`和`blocked-final-comparison.json`为本轮最终核验。正式代码包含89d5f61/e7d2991/77778be/26a4f43，均已推official；文档后继另行提交，旧三处dirty保持。

## 2026-10-19 18:32 用户停止请求后切换接续

- 最新用户“已停止，切入生产”。18:27:39核对执行0/等待0/DB0，旧CID/StartedAt/current/47条Key保持，1061容器基线；原备份68d成功、登记20、容量通过，旧before证据已加时间后缀保留。
- r3于18:29:29因候选名称仍为r2在preflight拒绝，Invocation4f064dcc、failed/exit1/PID0、new_id=null，原业务未停。错误记录保留，新增名称隔离回归Red复现；r4全身份修正后22项通过，镜像不变。
- r4 driver67674809、镜像97c378c7；准备提交bff67d8已推official。18:32:05仅启动一次unit `smartbrain-personal-registration-release-20261019-r4.service`，Invocation `28aca7cd84c641109c166c4bb1729b49`、MainPID2634742、Job11368346，首次activating。后续只用observe_release_r4_remote.py观察原Invocation，不重跑start/r1–r3。
- 完成状态待独立核验和归档；不冒充真实新号页面领取通过。没有第二次扩容/清理/备份/镜像构建/生产Key创建。

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
