# Phase 6 G1-P0 隔离环境只读授权申请包

- 申请日期：2026-09-18
- 申请阶段：Phase 6 / G1 / P0
- 当前状态：`blocked / not qualified`
- 申请目的：仅为当前隔离 gateway 和隔离 PostgreSQL 提供一次可审计的只读身份 preflight
- 不包含：代码发布、生产访问、数据库写入、服务启停、mock 请求、gateway 请求、模型请求或灰度

## 1. 当前项目边界

authoritative source：

`D:\AgentOpsServer\AgentOps\app`

计划、日志和 artifacts：

`E:\智慧大脑agent - 服务器端`

执行文档：

`E:\智慧大脑agent - 服务器端\docs\plans\2026-09-18-phase6-g1-next-instructions.md`

当前阻断证据：

`E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-preflight-blocked.json`

## 1.1 当前本地发现结果（只读，不构成授权目标）

本地历史 artifacts 中发现过以下试点选择器：

- `/srv/smartbrain-llm-pilot`；
- Docker Compose project：`smartbrain-llm-pilot`；
- Docker network：`smartbrain-llm-pilot_pilot`。

这些值来自 2026-09-15 的历史试点记录，只能作为后续“当前对象解析”的候选过滤条件，不能直接当作当前 container、image、network、PG 或 runner 身份。执行前仍必须读取当前对象并核对当前 source/config/policy SHA。

已知 SSH 别名 `smartbrain-prod` 解析到生产主机 `192.168.10.165`。该别名和主机不是隔离环境授权目标，不能用它替代当前隔离身份，也不能通过它推断隔离对象仍然存在。

生产目标明确排除：

- SSH 别名 `smartbrain-prod`；
- 任何生产主机、生产 Docker、生产 PostgreSQL；
- 生产 gateway、生产 Key、生产路由、生产 systemd/timer/nginx；
- 任何无法证明为隔离环境的对象。

## 2. 请求批准的最小范围

请只批准以下“当前隔离环境只读身份检查”。批准不包含后续 PG gate、mock gate 或真实模型验证。

### 2.1 隔离 gateway 身份

允许读取：

- 当前隔离 gateway container selector 对应的 container ID；
- image reference、immutable image ID、digest；
- container state、created time、started time；
- 当前 network ID/name；
- 非敏感配置版本信息；
- source/config/policy SHA-256；
- LiteLLM 版本；
- 当前 runner/source identity；
- 当前隔离对象的 labels、manifest 或 inventory 元数据。

禁止读取或输出：

- API Key、Token、Cookie、Authorization；
- 环境变量中的 secret；
- 数据库密码；
- 原始 prompt、response 或个人正文；
- 未脱敏配置全文。

### 2.2 隔离 PostgreSQL 身份

只允许使用批准的只读角色，并且目标必须明确标记为隔离环境。

允许执行只读查询确认：

- database；
- `current_user`；
- `server_version`；
- 当前连接目标身份；
- gateway instance registration；
- migration/schema 状态；
- 目标表是否存在；
- 必要的 RLS、索引和约束状态。

禁止执行：

- `INSERT`、`UPDATE`、`DELETE`；
- DDL；
- migration；
- `COMMIT`；
- 具有副作用的函数；
- 任意生产数据库连接。

### 2.3 隔离资源身份

仅允许读取当前隔离组件的：

- runner identity；
- 进程和监听状态；
- 临时 tunnel 状态；
- 资源和维护状态。

禁止启动、停止、重启或重新创建任何组件。

## 3. 授权人需要补齐的目标信息

以下字段必须由环境负责人填写，不能由执行者猜测：

```yaml
authorization:
  approved: false
  scope_approved_by_task_owner: true
  execution_status: "blocked_missing_current_target_identity"
  approver_name: ""
  approver_role: ""
  approved_at: ""
  expires_at: ""
  ticket_or_change_id: ""

target:
  environment: "isolated-non-production"
  host_or_execution_context: ""
  gateway_container_selector: ""
  gateway_manifest_path: ""
  postgres_target: ""
  postgres_readonly_role: ""
  runner_path: ""
  runner_sha256_or_manifest: ""

scope:
  readonly_preflight_only: true
  production_access: false
  gateway_requests: false
  mock_requests: false
  provider_requests: false
  real_model_requests: false
  service_start_stop_restart: false
  migration_or_ddl: false
  dml_or_commit: false
  secret_output: false
```

说明：本任务负责人已批准“只读 preflight 这一范围”作为工作目标；但 `approved` 仍保持 `false`，因为当前隔离 gateway、隔离 PostgreSQL 和获准 runner 的实际身份尚未被当前环境解析。范围批准不等于对未知目标执行远程命令。目标身份缺失时，执行授权自动保持阻断。

## 4. 允许的命令类型

授权人应批准“同等只读语义”的实际命令，而不是授权任意 shell。命令必须满足：

- 目标先解析、后读取；
- 不接受用户提供的任意 container ID、数据库 URL 或 shell 片段；
- 不打印 secret；
- 不执行管道中的写操作；
- 不调用会产生副作用的脚本或函数；
- 每条命令写入审计日志。

建议批准的逻辑命令清单：

```text
READ_ONLY gateway container identity for the approved isolated selector
READ_ONLY gateway image immutable identity and digest
READ_ONLY gateway labels, sanitized config/source/policy identity, and network identity
READ_ONLY LiteLLM version without inference request
READ_ONLY isolated PostgreSQL database/current_user/server_version
READ_ONLY gateway instance registration and migration/schema status
READ_ONLY isolated table/RLS/index/constraint metadata
READ_ONLY isolated runner/process/listener/tunnel/resource status
```

以下命令不在本授权范围内：

```text
docker exec commands that start applications or send requests
docker restart/stop/start/rm/run/build/pull
systemctl start/stop/restart/enable/disable/daemon-reload
psql INSERT/UPDATE/DELETE/DDL/migration/COMMIT
ssh to smartbrain-prod
curl or SDK calls to gateway/provider/model
mock network traffic
any command printing environment secrets
```

## 5. 执行后的强制停止点

即使 preflight 成功，本授权也只允许执行到身份快照完成为止。执行者必须在以下文件中记录结果后停止：

`E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\preflight-readonly.json`

必须人工复核以下内容后，才能另行批准 G1-P1：

- 当前 container/image/digest/network；
- source/config/policy SHA；
- LiteLLM 版本；
- runner/source identity；
- PostgreSQL database/current_user/server_version；
- gateway instance registration；
- migration/schema/RLS/index/constraint 只读结果；
- 身份是否一致且没有漂移；
- 是否发生任何写操作；
- 是否读取或输出敏感信息。

## 6. 阻断和撤销条件

出现以下任一情况，立即撤销本次授权并保持 `blocked`：

- 目标无法证明是隔离环境；
- 目标解析到 `smartbrain-prod` 或任何生产对象；
- container、image、network、source SHA、PG 身份或 runner identity 不一致；
- 权限分类器拒绝执行；
- 命令包含写操作、服务启停、网络请求或 secret 输出风险；
- 发现实际执行了未批准命令。

阻断时必须保持：

```json
{
  "status": "blocked",
  "gateway_identity_locked": false,
  "postgres_identity_locked": false,
  "pg_gate_started": false,
  "mock_gate_started": false,
  "three_model_validation_started": false,
  "g1_complete": false,
  "g2_or_gray_release_allowed": false,
  "production_changes": false,
  "bypass_attempted": false
}
```

## 7. GPT-6 固定策略

本授权不改变模型策略。`gpt-6-astra` 必须保持：

```json
{
  "status": "disabled_by_operator",
  "executed": false,
  "request_count": 0,
  "fallback_used": false
}
```

本授权不允许调用以下任意模型。真实模型验证属于后续单独 gate：

- `gpt-5.6-sol`；
- `gpt-5.6-terra`；
- `gpt-5.6-luna`；
- `gpt-6-astra`。

## 8. 授权批准后的执行顺序

只有授权人填写第 3 节并明确 `approved: true` 后，才能启动 P0：

1. 读取本文件和执行文档；
2. 解析当前隔离 gateway 身份；
3. 解析当前隔离 PostgreSQL 身份；
4. 检查身份一致性；
5. 写入 `preflight-readonly.json`；
6. 停止并等待人工复核；
7. 不自动进入 isolated PG、mock 或模型验证。

## 9. 授权结果回传格式

环境负责人或执行者应回传：

```text
authorization.approved = true/false
approver = <name and role>
ticket_or_change_id = <id>
expires_at = <ISO-8601>
isolated_gateway_target = <non-production identity>
isolated_postgres_target = <non-production identity>
readonly_role = <role name, no secret>
approved_runner = <path and sha/manifest>
production_target_excluded = true/false
allowed_scope = <exact read-only scope>
```

没有完整授权回传时，不能把 P0 从 `blocked` 改为 `approved`，也不能进入 G1-P1。
