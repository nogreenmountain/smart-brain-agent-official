# 个人 API 公网唯一入口发布记录

## 发布身份

- 发布编号／关联任务：`personal-api-public-only-20261018-r1`／`personal-api-relay-auth-20261017`
- 发布负责人／验证人：Codex
- 目标环境：Windows `192.168.10.146:9000` relay 与 `smartbrain-personal-gateway-current.service`
- 授权来源：用户 2026-10-18 明确要求关闭 9000 员工直连，只保留公网个人 API 加个人 Key，并要求今天上线。
- 状态：已上线并完成验收；promoted sequence14，2条真实公网完成请求，用户确认目标全部实现。
- 最后现场核对：2026-10-18 22:53（Asia/Shanghai）。

## 发布前后版本清单

| 组件 | 旧版本与身份 | 候选版本与身份 | 实际生效版本 | 证据 |
|---|---|---|---|---|
| Windows relay | `proxy-server.js` 监听 `0.0.0.0:9000`；PID476／Started 18:48:10；AI/管理面均可被 LAN 访问 | `deploy/personal-api-public-only-20261018/proxy-server.js`；AI 仅 `.165 + personal-api marker`，管理面仅 loopback | 已发布：PID31076，watchdog恢复 | `.artifacts/personal-api-public-only-20261018/` |
| personal-key-api | CID `7e700797…`／image `sha256:532a68da…` | image `sha256:28cd0714…`／source `075b6501…` | 已切换：CID052676a8／image28cd0714 | 2026-10-18 r1终态与独立终验 |

## 数据与兼容性

- 无数据库迁移，不修改或读取个人 Key 原文。
- 不签发、撤销、轮换、隐藏或删除 Key；发布前后只核对聚合指纹。
- 公网个人 API URL、请求协议和 Key 格式不变。
- Windows 9000 成为内部 hop；员工客户端若仍配置 9000，将按新边界失败，应改用公网 URL。

## 发布步骤与实际结果

| 顺序 | 目标与前置条件 | 动作及预期 | 实际结果 |
|---|---|---|---|
| 1 | 复现现状 | 只读核对监听、peer、防火墙和入口 | 已完成：9000 Any/Any，管理面匿名 LAN 200；生产源 `.165` |
| 2 | 候选回归 | Node 与 PowerShell 测试、临时端口隔离验证 | Node16、Python发布工具最终66、PS边界/回退/空闲证明与真实进程树测试通过 |
| 3 | Windows 边界 | 备份、安装、单次重启、恢复 watchdog | 已完成；新PID31076保持，watchdog enabled/running，9000边界通过 |
| 4 | personal gateway | 新发布身份 one-shot promote | 已执行一次，promoted sequence14，CID052676a8 |
| 5 | 生产验收 | direct 拒绝、公网匿名401、有效 Key 公网成功、身份与回退绑定 | 2真实完成请求＋用户确认通过，42条Key/1051无关容器保持；生产实际回退未执行 |

## 回退

- Windows：恢复发布前两个脚本与防火墙规则，只重启确切 relay 一次；3000 与个人 Key 数据不动。
- personal gateway：恢复发布前旧 CID、unit、inventory 与三网络；不恢复数据库。
- r1–r4 已终态或已废止，所有 promote/receipt/finalize/marker 禁止重放。

## 收尾

实际时间、hash、CID/PID、入口状态、Key 指纹、备份和回退执行情况随发布追加；未完成前不写“已上线”。


## 2026-10-18 19:38 公网个人 API 唯一入口继续实施（尚未切换）

用户明确：员工仅使用 `https://39.105.79.0/v4/personal-api/v1` 加既有个人 Key，Windows 9000 仅作内部上游。r4 终端隐藏输入流程及 direct/public 同时 200 的验收契约已废止，禁止重放旧 r1–r4。真实成功仅由日常客户端或自然公网请求确认；不读取/签发个人 Key。

19:20 三批 ClickHouse staging 与正式归档 SHA、3260 个文件完整载荷逐项一致；19:21 持 backup→maintenance 双锁，确认校验开始前至清理时 ctime/mtime 未变、无外部硬链接/具体容器挂载/打开文件或进程引用后，仅清理 20260918/19/23 三批冗余 staging，实际释放 33,164,529,664 bytes（30.887 GiB）。正式归档、失败证据、恢复目录和完整历史备份保留。证据：`.artifacts/personal-api-public-only-20261018/cleanup-result.json`；远端 acceptance 同任务 `-cleanup`。

19:23 原备份服务新启动一次，Invocation `11735eb839e54c2b8799b3d424cbfd80`、PID `3011428`、Job `11126005`、批次 `.20261018T112315Z.3011428.partial`。19:38 仍 activating/start，PG/CH/上传目录已归档，models 正在进行；不可重跑 start。实际生产 backup.sh 从 deploy/ubuntu/.env 加载配置：MIN_COLD/HOT/BACKUP=250/20/250 GiB、SOURCE_FULL_BACKUP_GB=35，实际动态预算 103,165,566,976 bytes；此前以 stack.conf/default300+错误数据目录推算的数字不作为门禁。当前源码检查器和实际配置未改，启动前真实 checker exit0；首次本地预检因误用 stack.conf 缺 COLD_DATA_ROOT 失败，尚未启动任何服务即修正。

Windows 候选 16/16、PS 启动/防火墙/Prepare/Apply-Rollback/迟到连接与闲置证明测试通过。准备脚本最初误将 UDP Node 规则计入 TCP 范围，已明确 TCP+确切 Node 路径；未据此修改系统。修复回退在文件已替换但旧进程仍活动时误杀旧连接的风险。原 PID476、backend26204、三条精确防火墙规则、watchdog 和回退文件已由用户允许的 UAC 只读备份。有限 elevated helper PID29948 / state `windows-state-r1d` 正等待同一备份成功，再复核固定脚本 SHA 和当前身份后单次 Apply；最长等待30分钟，无永久任务。

Linux 全新身份 `personal-api-public-only-20261018-r1` 工具本地62项通过，加入原网关 active/waiting/DB 双采样零值停止门槛、direct403/marked401/管理403及自然成功凭据指纹验收；远端尚未安装或切换。当前个人 CID `7e700797…`/image `532a68da…`/StartedAt `2026-10-17T13:44:51.228032986Z` 保持。19:29 原42条个人 Key 聚合指纹 `ff1303631e132bee1c6bd06334c410db` 已保存；active/waiting/DB均0。保留的TCP连接约50分钟无数据，只有两端无活动请求、队列为零、无3000连接和至少10秒字节计数稳定同时满足才允许作为 idle retained connection 安全关闭。

运行接续先观察上述备份及 Windows helper，勿重复 Prepare/Apply/start。完整个人 Key 公网成功及生产回退尚未验证；不能称已上线。详见[方案](../plans/2026-10-18-personal-api-public-only.md)、[发布](../releases/personal-api-public-only-20261018-r1.md)。


19:47：同一备份仍活动，models.tar.gz 1,998,323,712 bytes；Windows helper29948仍Prepared等待。Linux发布工具权威源码已整理至 `deploy/personal-api-public-only-20261018/`，最终64项离线测试通过，修复“回退时容器已经停止或生产名称暂空”情况下的排空检查；旧artifacts副本仅留证据，后续执行使用deploy包。


## 2026-10-18 20:08 备份与提权等待接续

19:52–20:06 对同一 Invocation `11735eb839e54c2b8799b3d424cbfd80` 只读观察，models 归档从2.981GB增长至6.015GB，备份仍 activating/start，未启动第二批。20:01 Docker40.09GiB、backups325.17GiB。原 elevated helper29948已在30分钟上限退出，错误为 `Backup gate not ready; no Apply`；20:08确认状态仍Prepared。新 `apply-windows-prepared-continuation.ps1` 仅接续原state-r1d，拒绝原helper仍在或状态非Prepared，保留原SHA检查、原三规则ID及单次Apply；未重跑Prepare。新进程需Windows再次UAC，目前等待系统批准。业务容器/9000尚未切换。


## 2026-10-18 20:33 备份完成，Windows 单次切换后收尾等待提权

- 原备份 Invocation `11735eb839e54c2b8799b3d424cbfd80` 成功结束，MainPID/ControlPID/Job清零，批次 `/srv/smartbrain-backups/backups/20261018T112315Z`；36项自校验与29个小文件独立SHA核验通过，登记20，四盘静态门槛通过。凭据在 `.artifacts/personal-api-public-only-20261018-r1/fresh-backup-receipt.json`；online不代表冻结恢复通过。
- 20:11用户重新批准UAC后，helper29688沿用原Prepared状态；备份成功后已收窄三条宽规则、启用精确`.165→.146:9000/TCP`规则，保存原日志、停止旧relay一次并启动新PID31076（StartTimeUTC `2026-10-18T12:25:49.9930121Z`）。backend26204保持；watchdog目前Disabled，state仍`OldRelayStopped`。
- 原Start-RelayOnce的`Start-Process -Wait`等待整个后代进程树，starter22804已退出但helper29688仍等待常驻Node，故未进入收尾。真实隔离复现StarterReturned=false；结束仅测试waiter后后台child保持。源码改为Process.WaitForExit，只等starter；新真实测试StarterReturned=true/child保持，Apply/rollback夹具通过、Python66项通过。原在运行helper使用旧已加载源码，不会自动取得修复。
- netsh将单IP呈现为相同起止范围（`.146-.146`、`.165-.165`），读回工具新增严格单IP归一化，接受裸IP、/32、相等起止，拒绝更宽网络/范围；未为迎合核验更改防火墙。
- 新`settle-windows-existing-relay.ps1`仅允许确切helper29688/StartTime12:11:41.0050689Z与relay31076/StartTime12:25:49.9930121Z、原backend、当前源码与三规则身份全部通过后，结束waiter一次、保留relay、恢复原watchdog、双轮询后标Applied。UAC返回用户取消，脚本未执行，仍需用户批准；无第二次relay重启。
- 下一步：重新批准并运行该收尾脚本（不得重跑Prepare/Apply或旧固定SHA continuation），读回Applied及watchdog，再执行deploy包collect_windows_receipt.py、两份凭据通过后一次性promote_remote.py，真实公网完成事件通过后finalize。Linux新发布尚未执行，原个人CID7e700797/Key42行指纹保持基线；尚未重新核对有效Key公网成功。


## 2026-10-18 22:45 Windows收尾完成，Linux已切换，等待真实公网请求验收

用户再次要求尽快上线。重新核对原PID/启动时间后经UAC恢复收尾：首版PS5.1因UTF8无BOM中文路径未找到状态；修正为PSScriptRoot相对解析。第二版在任何变更前因原watchdog XML省略默认Enabled=true而拒绝；只读确认当前XML仅多Enabled=false后规范化比较。最终22:42只结束确切waiter29688，relay31076/StartTime12:25:49.9930121Z及backend26204均保持；watchdog enabled/running，state Applied，未重复relay重启。三宽TCP规则disabled、精确`.165→.146:9000/TCP`allow均独立读回；LAN AI403、生产无marker403/marked匿名401、远程panel403、loopback panel200通过。

同一成功备份Invocation11735eb8、36自校验/29小文件SHA、20登记和当前容量重新只读验证通过，未启动新备份。注意collect_backup_receipt中的completed_at为再次核验时间；真实服务终态由固定ExecMainExitTimestampMonotonic3564742433645与Invocation证明，不表示22:40重新备份完成。

22:42:59仅一次执行新身份promote，unit `smartbrain-personal-public-only-promote-20261018-r1-20261018T144259Z`。22:43:22进入awaiting_smoke sequence13，新CID `052676a8caaff02578b73a25f10258da0d11350f164e4a94469d7912f2dae35e`／image28cd0714／source075b6501，current unit active/enabled，Invocation c1554993c4ba4e9c85ce6fa887082f5e，MainPID3571167。旧CID7e700797停止断网改名rollback保留，不能重放promote。真实请求验收截止22:58:22；未收到收据则原runner按既定流程回退，不延长或伪造验收。

22:44独立核对1051无关容器配置和启动代际无变化，当前1054/39；网络、HostConfig、公网匿名401/login200及Windows边界通过；Key42行聚合指纹ff1303631e132bee1c6bd06334c410db保持。四盘可用字节Docker43005775872/root33054875648/backups345756135424/cold271549591552，MemAvailable8295817216。22:45网关health ok，active/waiting/DB0，最近小时尚无真实请求完成事件，不能称有效Key公网成功已验收。

唯一接续：运行deploy包collect_natural_success.py只读汇总切换后真实完成请求；其成功时安装无Secret收据供原runnerfinalize。然后只读status确认promoted及collect_final_independent.py。不要重跑WindowsPrepare/Apply、备份start或Linuxpromote。


## 2026-10-18 22:53 发布完成与独立终验

用户确认日常客户端测试成功，并确认“员工关闭9000直连，仅使用公网个人API＋原个人Key”的目标全部实现。22:52:48服务端只读聚合确认切换后2条`personal_api`真实请求status200且content_complete，原42条Key聚合指纹`ff1303631e132bee1c6bd06334c410db`保持。收据只含请求摘要及计数，无Key或正文；原runner采纳后进入`promoted sequence=14`，22:53独立读回确认，未发生本次Linux发布回退。

当前公网地址仍为 `https://39.105.79.0/v4/personal-api/v1`。新CID `052676a8caaff02578b73a25f10258da0d11350f164e4a94469d7912f2dae35e`，image `sha256:28cd0714f8ebdb214ad259444e4a9123b1d5d6ec4b89bf93fd48a40bd19e1cb1`，source `075b650186ad79cfec6b74eb8cb257ceabe8fee7426016f91308c1acb6cc09fe`；current unit active/running/enabled、Invocation `c1554993c4ba4e9c85ce6fa887082f5e`、MainPID3571167。原容器停止断网作为回退保留；新旧个人Key鉴权/归属/配额/撤销状态/历史记录/表结构未修改。

Windows relay PID31076/StartedAt12:25:49.9930121Z与backend26204/StartedAt2026-10-17T07:08:16.5011949Z保持，3000仅loopback，watchdog enabled/running。卡住的waiter29688与收尾helper29912均已退出；未再次重启relay。个人9000直连403，生产内部marked匿名401，远程管理面403；公网匿名models/responses401、login200。端口9000保留为受限内部上游，不作为员工入口。

1051无关容器Config/HostConfig hash、镜像、运行状态、启动时间及RestartCount全部保持；当前1054容器/39运行，个人网关三网络和HostConfig保持。原备份Invocation11735eb8在20:24:24 CST成功终态，36自校验/29小文件独立SHA通过、登记20；没有重放备份或另造一批。发布unit终态active/exited、Result success、ExecMainStatus0、MainPID/ControlPID0，已不等待或执行自动回退。

22:53磁盘空闲Docker43,001,860,096 bytes（约40.05GiB，余量薄）、/srv/smartbrain33,054,777,344、backups345,756,135,424、cold271,612,805,120，MemAvailable8,273,473,536；原门槛未降低。无新build、大归档、历史日志/备份/容器删除。此前仅清理三批已逐文件核实的冗余staging，释放30.887GiB。

验收范围：本次公网唯一员工入口、原个人Key真实请求、Windows边界及当前服务完整性通过。未声称所有模型/30人并发容量、全writer冻结/全库恢复或本次生产实际回退演练通过。原r1–r4旧发布和本次已终态promote、WindowsPrepare/Apply、backup-start均禁止重放；后续问题从当前身份取证。

证据：`.artifacts/personal-api-public-only-20261018-r1/{natural-success-observation,live-release-status,final-independent-state,fresh-backup-receipt,windows-ready-receipt}.json`；Windows `windows-state-r1d/release-state.json`、`windows-settlement-before.json`、`windows-settlement-result.txt`；远端 `/srv/smartbrain/releases/personal-api-public-only-20261018-r1/evidence/`。代码/工具此前已推`5027a5b`、`67ccb9a`；本次仅提交终验文档，旧dirty不混入。
