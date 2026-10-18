# 个人 API 公网唯一入口发布记录

## 发布身份

- 发布编号／关联任务：`personal-api-public-only-20261018-r1`／`personal-api-relay-auth-20261017`
- 发布负责人／验证人：Codex
- 目标环境：Windows `192.168.10.146:9000` relay 与 `smartbrain-personal-gateway-current.service`
- 授权来源：用户 2026-10-18 明确要求关闭 9000 员工直连，只保留公网个人 API 加个人 Key，并要求今天上线。
- 状态：候选与发布工具已验证；已清理确证冗余副本并启动新备份，Windows 已 Prepared；应用服务尚未切换。
- 最后现场核对：2026-10-18 19:47（Asia/Shanghai）。

## 发布前后版本清单

| 组件 | 旧版本与身份 | 候选版本与身份 | 实际生效版本 | 证据 |
|---|---|---|---|---|
| Windows relay | `proxy-server.js` 监听 `0.0.0.0:9000`；PID476／Started 18:48:10；AI/管理面均可被 LAN 访问 | `deploy/personal-api-public-only-20261018/proxy-server.js`；AI 仅 `.165 + personal-api marker`，管理面仅 loopback | 未发布 | `.artifacts/personal-api-public-only-20261018/` |
| personal-key-api | CID `7e700797…`／image `sha256:532a68da…` | image `sha256:28cd0714…`／source `075b6501…` | 未切换 | 2026-10-17 r6 候选证据；切换前须重核 |

## 数据与兼容性

- 无数据库迁移，不修改或读取个人 Key 原文。
- 不签发、撤销、轮换、隐藏或删除 Key；发布前后只核对聚合指纹。
- 公网个人 API URL、请求协议和 Key 格式不变。
- Windows 9000 成为内部 hop；员工客户端若仍配置 9000，将按新边界失败，应改用公网 URL。

## 发布步骤与实际结果

| 顺序 | 目标与前置条件 | 动作及预期 | 实际结果 |
|---|---|---|---|
| 1 | 复现现状 | 只读核对监听、peer、防火墙和入口 | 已完成：9000 Any/Any，管理面匿名 LAN 200；生产源 `.165` |
| 2 | 候选回归 | Node 与 PowerShell 测试、临时端口隔离验证 | Node16、Python发布工具64、PS边界/回退/空闲证明通过；应用服务未变更 |
| 3 | Windows 边界 | 备份、安装、单次重启、恢复 watchdog | 未执行 |
| 4 | personal gateway | 新发布身份 one-shot promote | 未执行 |
| 5 | 生产验收 | direct 拒绝、公网匿名401、有效 Key 公网成功、身份与回退绑定 | 未执行 |

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
