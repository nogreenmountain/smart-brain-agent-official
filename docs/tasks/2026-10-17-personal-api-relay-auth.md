# 个人 API 中转站认证适配

## 任务身份与范围

- 任务编号：`personal-api-relay-auth-20261017`
- 负责人／集成负责人：Codex
- 创建／更新时间：2026-10-17；最后核对 18:37（Asia/Shanghai）
- 开发阶段：候选已验证，生产发布受备份终态门禁阻断
- 部署范围：未部署；现网仍为旧 personal-key-api
- 目标及可观察的验收标准：有效个人 Bearer 能经本地代理到 Windows 9000；9000 匿名仍为 401；个人 Key 不出现在最终模型下游；chat/responses/streaming 路径和 query/body 保持。
- 本轮授权范围、来源、期限：用户当前请求；仅处理个人 API 认证链路，不扩展到 Key 数据模型或其他服务。
- 前置依赖／相关任务：当前 personal-key-api 容器、Windows 9000 relay；既有个人 API 增量记录发布作为基线。

## 代码与版本

- 权威源码目录／仓库：`C:\Users\test\.codex\worktrees\deb4\智慧大脑agent - 服务器端`
- 工作目录／分支／基线提交：`codex/project-memory-no-adapter`，基线 `6e4cce2`
- 本任务变更文件：`agentops_local/api/personal_gateway_proxy.py`、个人代理测试、`deploy/personal-api-relay-auth-20261017/Dockerfile.personal-api`、本任务/方案/发布记录
- 本任务未提交修改及保存方式：既有 `docs/CURRENT.md`、`docs/tasks/2026-10-12-ai-work-record-projection.md` 等 dirty 修改保留；只提交本任务文件。
- 既有其他任务修改：不归入本任务，提交前按路径审查。
- Git 提交、审查与推送状态：提交 `2d0ee2e535d5d55f9c0bcdc41da3af0cb86ce681` 已推送 `official/codex/project-memory-no-adapter`；Windows 本地 relay 脚本不在该仓库
- 关联发布记录／最近生产核对时间：[personal-api-relay-auth-20261017-r1](../releases/personal-api-relay-auth-20261017-r1.md)；生产只读核对至 2026-10-17 18:36。

## 已完成与未完成

| 项目 | 状态 | 证据或说明 |
|---|---|---|
| 9000 与公网 401 复现 | 已完成 | 只读 probe 与生产聚合；不输出 Key、正文或原始日志 |
| 根因定位 | 已完成 | 两层根因均已确认：个人代理剥离 Authorization；Windows relay 的旧启动脚本用全局列表正则误取插件标签 `Executor` 而非 `access.api-keys`，导致授权通过后的 3000 下游 401；07:08Z 的 `upstream_response_error` 正属于后者 |
| relay/opaque 代码与测试 | 已验证 | 本地 shim/ASGI 37 passed；候选镜像网络隔离回归 52 passed；source SHA `075b6501…` |
| 候选镜像与显式配置 | 已验证 | candidate r6 image `sha256:28cd0714…`；import probe `relay-config-ok`；显式 mode/URL 仅在候选验证中使用 |
| 生产发布 | 受阻 | current CID `7e700797…` 保持；`smartbrain-backup.service` 最新 Invocation `af6faabf…` 为 failed/exit-code，容量门禁未恢复；当时只观察到 `/run/lock/smartbrain-maintenance.lock` 文件，未核对 flock owner／竞争；未切换 |

## 验证记录

| 时间 | 代码版本或 hash | 环境与命令 | 退出码和结果 | 证据位置 | 验证范围与限制 |
|---|---|---|---|---|---|
| 2026-10-17 | 生产当前 personal proxy（只读） | 9000/public 匿名与无效 Key 请求、PG 聚合 | 401；active Key 也出现 upstream 401 | `.artifacts/gateway-key-401-20261017/` | 未读取真实 Key、正文或完整 Env |
| 2026-10-17 16:20 | candidate source SHA `075b6501…`／image `sha256:28cd0714…` | 网络隔离候选镜像：代理回归 + fake relay/ASGI + mode import | 52 passed；1 个既有 gotrue warning；生产 mutation 0 | `.artifacts/personal-api-relay-auth-20261017/candidate-result-remote.json`、`candidate-evidence-summary.log` | 未接真实 Windows relay、生产 DB、真实 Key 或模型 |
| 2026-10-17 16:43 | 现网旧 personal gateway／备份与容量 | unit、CID/image、timer、四盘、锁路径和 pending 只读核对 | 旧版本保持；backup `failed/exit-code`；maintenance lock 文件存在但 flock owner／竞争未核对；未变更 | `.artifacts/personal-api-relay-auth-20261017/fresh-production-precheck.json` | 未读取 Env 值、Key、正文；锁文件未由本轮创建或删除，发布门禁以实际非阻塞 flock 竞争为准 |
| 2026-10-17 17:02–17:10 | Windows relay 启动链与生产门禁续核 | `start-services.test.ps1`、Node relay 回归、进程/连接与生产只读快照 | PowerShell 4/4、Node 26/26；实际 `access.api-keys` 只记录长度/前缀/哈希；生产仍旧版本；未重启/未切换 | `.artifacts/personal-api-relay-auth-20261017/windows-start-services-test.json`、`windows-pre-restart.json`、`production-gate-refresh-20261017T170041+0800.json` | 9000 有一条自旧进程启动后保持的长连接，按在途流处理，未强制中断；新脚本要下次启动才生效 |

## 运行中的任务

状态：候选构建/测试已终态；没有生产发布任务。Windows 启动脚本已修正但当前 relay 进程尚未重启；current unit active/enabled，backup service failed 且 timer waiting；无 pending maintenance。候选测试容器和镜像保留为证据，未接 systemd/edge。

## 不可重跑的动作

| 动作与操作编号 | 已知结果／不确定状态 | 查询或恢复原任务的方法 |
|---|---|---|
| 未执行 | 无 | 不适用 |

## 下一步

1. 在不删除历史证据的前提下恢复并核对新鲜 backup 成功终态；未满足前不发布。
2. 若备份、容量、maintenance 和回退绑定全部通过，按发布记录一次性切换，并在新容器 Config.Env 显式加入 `SB_PERSONAL_UPSTREAM_AUTH_MODE=smartbrain_relay` 与受信 `SB_PERSONAL_UPSTREAM_URL`，不依赖镜像默认值。
3. 切换后核对 direct/public 匿名 401、health、unit/CID/网络身份；真实有效 Key 200 由用户使用现有 Key 做受控请求，不能读取或输出 Key。

## 决策与变更日志

| 时间 | 决策或状态变化 | 原因与来源 |
|---|---|---|
| 2026-10-17 | 采用显式 `smartbrain_relay` 模式 | Windows 9000 新认证契约；避免把个人 Key 发送到最终模型 |
| 2026-10-17 | 生产切换暂停 | 最近 backup service 为 failed/exit-code，不能以静态登记或旧成功替代新鲜备份终态；保留候选和旧现网不动 |

## 2026-10-17 16:36 生产门禁续核

- 只读核对 `smartbrain-personal-gateway-current.service` 仍 `active/enabled`，Invocation `370fc92f…`、MainPID `1060105`；旧 personal-key-api CID `7e700797…`、image `sha256:532a68da…`、RestartCount 0、三网络身份保持，Config.Env 仍未包含本轮两个 `SB_PERSONAL_*` 变量。
- `smartbrain-backup.service` Invocation `af6faabf…` 仍 `failed/exit-code`、MainPID/ControlPID 0；timer `active/waiting`，下一次计划 2026-10-18 02:42（CST）；maintenance/backup pending 与 intent 标记均不存在。`/run/lock/smartbrain-maintenance.lock` 文件存在本身不表示锁被持有；当时未核对 flock owner／竞争，发布只以实际非阻塞 flock 获取结果判定。
- Docker 可用约 40.38 GiB；备份盘约 339.48 GiB，备份脚本所需储备仍不足约 6.38 GiB。未执行 prune、删除历史对象、重放备份或任何生产变更。候选 r6 证据继续有效，但不等于已上线。

## 2026-10-17 17:02–17:10 接续核对

- Windows `start-services.ps1` 现在只从 `access.api-keys` 读取单一 CPA 内部 Key；缺失或多值 fail-closed。`start-services.test.ps1` 退出 0，4 项检查通过（loopback、限制项、重试缩进、Key 解析）；Node `proxy-server.test.js` 与 `gateway-server.test.js` 合计 26/26 通过。实际配置只记录长度 77、脱敏前缀和 SHA `f6801d8c…`，未输出 Key。
- 当前 9000 PID `24220`（2026-10-17 15:08:18 启动）、3000 PID `26204` 保持；9000 存在自启动后持续的已建立连接。为避免杀掉在途长流，没有执行重启；因此新解析结果尚未进入运行进程，不能把 Windows 运行态称为已修复。
- 生产 17:00:41 只读刷新：current unit/CID/image 与旧环境保持；backup Invocation `af6faabf…` 仍 `failed/exit-code`，备份盘短约 6.38 GiB；维护锁和备份锁文件存在，但未据此推断 flock 被持有。没有清理、重放备份、生产切换或真实 Key 请求。
- 证据：`.artifacts/personal-api-relay-auth-20261017/windows-start-services-test.json`、`windows-pre-restart.json`、`production-gate-refresh-20261017T170041+0800.json`。候选代码已由 `2d0ee2e` 推送；现网仍未注入 `SB_PERSONAL_UPSTREAM_AUTH_MODE`／`SB_PERSONAL_UPSTREAM_URL`。

## 2026-10-17 18:36–18:37 上线前实时门禁

- 生产 personal gateway 仍是旧 CID `7e700797…`／image `sha256:532a68da…`，unit active/running/enabled、RestartCount 0；两个 relay 环境变量均未注入。
- backup service 仍为 `failed/exit-code`，Invocation `af6faabf…`，无 PID/Job；timer waiting。备份盘可用 339.481 GiB，而最新失败批次动态需求为 345.861 GiB，仍短约 6.380 GiB。四盘静态硬线虽通过，不能替代 `inactive/success` 的备份终态。
- Windows 9000 PID `24220` 仍有 1 条 17:33:08 建立的连接；watchdog 每 10 秒轮询。连接未排空且未协调 watchdog，不能安全重启加载新 CPA Key。
- 结论：当前不放行上线；没有执行重启、清理、备份重放或生产切换。证据：`.artifacts/personal-api-relay-auth-20261017/production-gate-readonly-20261017T183628+0800.json`、`windows-restart-gate-20261017T183709+0800.json`。

## 2026-10-17 21:44–22:27 r1–r3 回退与 r4 安全接续

- r1、r2 均按各自 stage 安全恢复；r3 只执行一次 promote，因用户未在 15 分钟 smoke 窗口内完成隐藏 Key 输入，于 21:44:58 自动 `restored sequence=15`。不得重放 r1–r3 的 promote、receipt、finalize 或 cutover marker。
- 21:46 只读复核旧 CID `7e700797…`／image `sha256:532a68da…` running、RestartCount 0，最新 StartedAt `2026-10-17T13:44:51.228032986Z`；current unit active/running，unit 与 inventory 均和 r3 rollback 备份一致，inventory 绑定旧 CID。公网 health/login 200、匿名 models/responses 401；backup inactive/success，两把锁可获取，无 maintenance pending/intent。r3 candidate 与失败新容器停止、断网保留。
- 新建独立 `.artifacts/personal-api-relay-auth-20261017-r4/`，先以 Codex PTY 的 `Read-Host -AsSecureString` 取 Key，再允许 promote。ready gate 绑定 PID/StartTime/SessionId、MainWindowHandle=0、唯一精确 `-File` wrapper 路径、wrapper/helper/child SHA、5 分钟 TTL 与随机 nonce；live r4 stage、new CID、awaiting 时间及不超过 900 秒 deadline 通过后才写 cutover marker。Key 不进入聊天、参数、环境变量或文件。
- r4 完整回归 97 passed，Python AST 16/16、PowerShell AST 4/4，身份审计和独立安全复核 GO。当前 r4 runtime JSON 为 0，远端 release dir/stage/smoke receipt、候选/rollback/failed 容器名和 transient unit 均不存在，没有执行 r4 生产切换。
- 当前唯一前置是用户在 Codex 底部终端运行 `C:\Users\test\r4-key-input.cmd` 并隐藏输入现有 Personal API Key；marker 出现后须在 5 分钟内运行 coordinator `validate-ready`，生成全新 release=r4 的 backup/windows receipts，one-shot promote 后显式确认 `awaiting_smoke sequence=13`，再 publish-cutover、生成 smoke receipt 并 finalize。r4 一旦出现 stage 后失败或 restored，禁止重放，改用新 release identity。

## 2026-10-18 19:38 公网个人 API 唯一入口继续实施（尚未切换）

用户明确：员工仅使用 `https://39.105.79.0/v4/personal-api/v1` 加既有个人 Key，Windows 9000 仅作内部上游。r4 终端隐藏输入流程及 direct/public 同时 200 的验收契约已废止，禁止重放旧 r1–r4。真实成功仅由日常客户端或自然公网请求确认；不读取/签发个人 Key。

19:20 三批 ClickHouse staging 与正式归档 SHA、3260 个文件完整载荷逐项一致；19:21 持 backup→maintenance 双锁，确认校验开始前至清理时 ctime/mtime 未变、无外部硬链接/具体容器挂载/打开文件或进程引用后，仅清理 20260918/19/23 三批冗余 staging，实际释放 33,164,529,664 bytes（30.887 GiB）。正式归档、失败证据、恢复目录和完整历史备份保留。证据：`.artifacts/personal-api-public-only-20261018/cleanup-result.json`；远端 acceptance 同任务 `-cleanup`。

19:23 原备份服务新启动一次，Invocation `11735eb839e54c2b8799b3d424cbfd80`、PID `3011428`、Job `11126005`、批次 `.20261018T112315Z.3011428.partial`。19:38 仍 activating/start，PG/CH/上传目录已归档，models 正在进行；不可重跑 start。实际生产 backup.sh 从 deploy/ubuntu/.env 加载配置：MIN_COLD/HOT/BACKUP=250/20/250 GiB、SOURCE_FULL_BACKUP_GB=35，实际动态预算 103,165,566,976 bytes；此前以 stack.conf/default300+错误数据目录推算的数字不作为门禁。当前源码检查器和实际配置未改，启动前真实 checker exit0；首次本地预检因误用 stack.conf 缺 COLD_DATA_ROOT 失败，尚未启动任何服务即修正。

Windows 候选 16/16、PS 启动/防火墙/Prepare/Apply-Rollback/迟到连接与闲置证明测试通过。准备脚本最初误将 UDP Node 规则计入 TCP 范围，已明确 TCP+确切 Node 路径；未据此修改系统。修复回退在文件已替换但旧进程仍活动时误杀旧连接的风险。原 PID476、backend26204、三条精确防火墙规则、watchdog 和回退文件已由用户允许的 UAC 只读备份。有限 elevated helper PID29948 / state `windows-state-r1d` 正等待同一备份成功，再复核固定脚本 SHA 和当前身份后单次 Apply；最长等待30分钟，无永久任务。

Linux 全新身份 `personal-api-public-only-20261018-r1` 工具本地62项通过，加入原网关 active/waiting/DB 双采样零值停止门槛、direct403/marked401/管理403及自然成功凭据指纹验收；远端尚未安装或切换。当前个人 CID `7e700797…`/image `532a68da…`/StartedAt `2026-10-17T13:44:51.228032986Z` 保持。19:29 原42条个人 Key 聚合指纹 `ff1303631e132bee1c6bd06334c410db` 已保存；active/waiting/DB均0。保留的TCP连接约50分钟无数据，只有两端无活动请求、队列为零、无3000连接和至少10秒字节计数稳定同时满足才允许作为 idle retained connection 安全关闭。

运行接续先观察上述备份及 Windows helper，勿重复 Prepare/Apply/start。完整个人 Key 公网成功及生产回退尚未验证；不能称已上线。详见[方案](../plans/2026-10-18-personal-api-public-only.md)、[发布](../releases/personal-api-public-only-20261018-r1.md)。
