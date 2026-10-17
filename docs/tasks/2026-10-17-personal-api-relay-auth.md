# 个人 API 中转站认证适配

## 任务身份与范围

- 任务编号：`personal-api-relay-auth-20261017`
- 负责人／集成负责人：Codex
- 创建／更新时间：2026-10-17；最后核对 16:36（Asia/Shanghai）
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
- Git 提交、审查与推送状态：待提交；未推送
- 关联发布记录／最近生产核对时间：[personal-api-relay-auth-20261017-r1](../releases/personal-api-relay-auth-20261017-r1.md)；生产只读核对 2026-10-17 16:20。

## 已完成与未完成

| 项目 | 状态 | 证据或说明 |
|---|---|---|
| 9000 与公网 401 复现 | 已完成 | 只读 probe 与生产聚合；不输出 Key、正文或原始日志 |
| 根因定位 | 已完成 | 当前代理剥离 Authorization；Windows relay 要求个人 Bearer 并替换为 CPA Key |
| relay/opaque 代码与测试 | 已验证 | 本地 shim/ASGI 37 passed；候选镜像网络隔离回归 52 passed；source SHA `075b6501…` |
| 候选镜像与显式配置 | 已验证 | candidate r6 image `sha256:28cd0714…`；import probe `relay-config-ok`；显式 mode/URL 仅在候选验证中使用 |
| 生产发布 | 受阻 | current CID `7e700797…` 保持；`smartbrain-backup.service` 最新 Invocation `af6faabf…` 为 failed/exit-code，容量门禁未恢复；`/run/lock/smartbrain-maintenance.lock` 仍存在；未切换 |

## 验证记录

| 时间 | 代码版本或 hash | 环境与命令 | 退出码和结果 | 证据位置 | 验证范围与限制 |
|---|---|---|---|---|---|
| 2026-10-17 | 生产当前 personal proxy（只读） | 9000/public 匿名与无效 Key 请求、PG 聚合 | 401；active Key 也出现 upstream 401 | `.artifacts/gateway-key-401-20261017/` | 未读取真实 Key、正文或完整 Env |
| 2026-10-17 16:20 | candidate source SHA `075b6501…`／image `sha256:28cd0714…` | 网络隔离候选镜像：代理回归 + fake relay/ASGI + mode import | 52 passed；1 个既有 gotrue warning；生产 mutation 0 | `.artifacts/personal-api-relay-auth-20261017/candidate-result-remote.json`、`candidate-evidence-summary.log` | 未接真实 Windows relay、生产 DB、真实 Key 或模型 |
| 2026-10-17 16:43 | 现网旧 personal gateway／备份与容量 | unit、CID/image、timer、四盘、锁和 pending 只读核对 | 旧版本保持；backup `failed/exit-code`；maintenance lock 存在；未变更 | `.artifacts/personal-api-relay-auth-20261017/fresh-production-precheck.json` | 未读取 Env 值、Key、正文；锁未由本轮创建或删除 |

## 运行中的任务

状态：候选构建/测试已终态；没有生产发布任务。current unit active/enabled，backup service failed 且 timer waiting；无 pending maintenance。候选测试容器和镜像保留为证据，未接 systemd/edge。

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
- `smartbrain-backup.service` Invocation `af6faabf…` 仍 `failed/exit-code`、MainPID/ControlPID 0；timer `active/waiting`，下一次计划 2026-10-18 02:42（CST）；maintenance/backup pending 与 intent 标记均不存在，但 `/run/lock/smartbrain-maintenance.lock` 仍存在，不能切换或触碰维护锁。
- Docker 可用约 40.38 GiB；备份盘约 339.48 GiB，备份脚本所需储备仍不足约 6.38 GiB。未执行 prune、删除历史对象、重放备份或任何生产变更。候选 r6 证据继续有效，但不等于已上线。
