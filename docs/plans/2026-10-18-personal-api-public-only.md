# 个人 API 公网唯一入口实施方案

## 目标

员工仅通过 `https://39.105.79.0/v4/personal-api/v1` 加既有个人 API Key 使用 AI；`192.168.10.146:9000` 保留为生产网关内部上游，不再作为员工或局域网客户端入口。

授权来自用户 2026-10-18 的明确纠正与“今天上线”要求。既有个人 Key、配额、归属、撤销状态、历史记录和数据库结构均不改。

## 已锁定决策

- r4 的“direct 9000 与 public 同时 200”契约与目标冲突，废止且不执行；使用新的发布身份。
- Windows relay 的 AI 路径必须同时满足：TCP 来源为生产服务器 `192.168.10.165`，且请求含 personal gateway 固定内部标记。个人 Key 仍由原 SmartBrain authorize 路径验证，随后只在 Windows loopback hop 换成原 CPA 内部 Key。
- Windows relay 的 `/`、`/panel`、`/management.html`、`/v0/*` 和 `/v8/management/*` 仅允许 loopback；生产主机和其他局域网来源不得访问。
- Windows 防火墙先精确允许 `192.168.10.165 -> 192.168.10.146:9000/TCP`，再禁用两条 RemoteAddress=Any 的旧 9000 规则，以及一条精确绑定当前 Node 可执行文件的宽 TCP 规则（合计三条，以 Prepared 状态中规则 ID 为准）。默认入站 Block；不添加会覆盖 Allow 的显式全局 Block。
- 不要求用户把个人 Key 输入 Codex 终端。有效 Key 的最终确认只通过用户日常客户端的公网地址或后继自然流量；证据不保存 Key、正文或响应正文。

## 阶段 1 — 候选与回归

- 文件：`deploy/personal-api-public-only-20261018/proxy-server.js`、`start-services.ps1` 与测试。
- 变更：增加不可伪造的 TCP peer 地址检查和内部标记检查；管理面只允许 loopback；内部标记不转发到 3000；启动脚本固定生产来源 IP。
- 验证：先保存 Red，再运行 Node 原回归和新增边界测试；PowerShell 静态测试；19000 临时端口验证本机 LAN 地址 AI 403、loopback panel 200，不读取凭据。

## 阶段 2 — Windows 边界发布

- 前置：保存当前脚本、hash、PID/StartTime、计划任务和防火墙规则；确认 3000 仅 loopback、9000 当前连接与 watchdog 身份。
- 动作：安装候选文件；精确收窄防火墙；停止 `CLIProxyAPI2Services` watchdog；等待在途连接排空；只停止确切旧 9000 PID 一次；运行 `start-services.ps1` 一次；恢复 watchdog。
- 验证：9000 新 PID/源码 hash；生产主机匿名 AI 401；生产主机 panel/management 403；Windows LAN 地址 AI 403；Windows loopback panel 200；3000 仍只监听 loopback。
- 回退：停止新 PID 一次，恢复原文件和原防火墙规则，运行原启动脚本一次并恢复 watchdog。不得循环重启。

## 阶段 3 — 生产 personal gateway 切换

- 候选：已验证镜像 `sha256:28cd0714f8ebdb214ad259444e4a9123b1d5d6ec4b89bf93fd48a40bd19e1cb1`，源码 SHA `075b650186ad79cfec6b74eb8cb257ceabe8fee7426016f91308c1acb6cc09fe`。
- 前置：重新核对 current CID/image/StartedAt、unit、backup success、锁、pending、四盘容量、Windows 新边界及候选镜像存在。
- 动作：用全新发布目录、容器名、unit 和一次性 stage 切换；显式设置 `SB_PERSONAL_UPSTREAM_AUTH_MODE=smartbrain_relay` 与受信 upstream URL；不重放 r1–r4。
- 验证：公网 health/login 200；公网 personal 匿名/无效 Key 401；direct 9000 从非生产来源拒绝；生产来源匿名 401；有效个人 Key 仅经公网入口成功；Key 数据指纹不变。
- 回退：任何启动、边界或有效 Key 验收失败即恢复旧 CID/unit/inventory，保留候选和失败证据；Windows 边界修复可独立保留，因为旧 personal gateway 本就不需要用户直连 9000。

## 风险

- 生产主机 LAN 地址变化会让 9000 fail-closed；发布前后同时核对 `ip route get` 与 Windows 实际 peer。
- Windows 防火墙需要提升权限；若无法自动取得，不用宽规则冒充完成，应用层边界先发布并明确记录网络层状态。
- 真实有效 Key 不可从数据库反推。未观察到公网有效请求前，只能写“候选及匿名边界通过”，不能称个人 Key 端到端已验收。


## 19:38 发布编排补充

已增加仅对确切旧网关保留空闲连接的证明：两个样本至少10秒，active/waiting/database_in_use均0，双端TCP队列0且字节计数稳定，最后发送/接收超过1800秒，Windows无3000连接，源端口/PID与现场一致；停止前再次核对。普通活动连接仍等待排空，迟到连接触发恢复文件且不杀原进程。新Linux工具仅支持公网成功＋direct403，不需要终端Key输入。新online备份运行时仅准备文件和读取状态，边界Apply等待该批次成功。
