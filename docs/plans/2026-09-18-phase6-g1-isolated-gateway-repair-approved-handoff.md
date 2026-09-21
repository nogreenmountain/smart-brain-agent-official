# Phase 6 G1 — approved isolated Gateway repair handoff

## Approval

- Approval ID: `G1-P0-ISOLATED-REPAIR-20260918-R1`
- Approved by: server/isolation owner acting under the task owner's explicit instruction
- Scope: isolated-pilot repair and P0 identity recovery only
- Expires: `2026-09-18T23:59:59+08:00`
- Transport: SSH alias `smartbrain-prod` is approved only as transport to the host that contains the isolated pilot. It is not approval to inspect or mutate production resources.
- Production resource access: forbidden

## Paste this prompt to Claude Code

```text
你是 Phase 6 / G1 的隔离 Gateway 修复与 P0 身份恢复工程师。本提示词是新的明确授权，替代上一轮“不得使用 smartbrain-prod 作为新执行目标”的限制，但只在下述极窄范围内有效。

授权编号：G1-P0-ISOLATED-REPAIR-20260918-R1
授权截止：2026-09-18T23:59:59+08:00

### 新授权的准确含义

允许使用 SSH alias `smartbrain-prod` 作为传输入口，因为当前 isolated-pilot Docker/Compose 域位于该主机上。但它只能用于解析和操作同时满足以下条件的对象：

- `smartbrain.scope=isolated-pilot`；
- `com.docker.compose.project=smartbrain-llm-pilot`；
- gateway service 必须为 `com.docker.compose.service=gateway`；
- PostgreSQL service 必须为 `com.docker.compose.service=gateway-db`；
- mock service 必须为 `com.docker.compose.service=mock-upstream`。

不得枚举、读取或修改其他生产容器、生产 PostgreSQL、生产 systemd、timer、nginx、tunnel、Key、路由或文件。不得把 `smartbrain-prod` 解释为“允许生产操作”。

### 必须先读取

1. `E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-isolated-gateway-repair-candidate-r1.json`
2. `E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-isolated-gateway-repair-r1.json`
3. `E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-p0-identity-recovery-r1.json`
4. `E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-p0-preflight-r2.json`
5. `E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-p0-container-inspect-r2.log`
6. `E:\智慧大脑agent - 服务器端\docs\plans\2026-09-18-phase6-g1-isolated-gateway-repair-handoff.md`
7. `E:\智慧大脑agent - 服务器端\docs\plans\2026-09-18-phase6-g1-isolated-gateway-repair-approved-handoff.md`

### authoritative source 与固定 SHA

source root 只能是：

`D:\AgentOpsServer\AgentOps\app`

在任何远程动作前重新核验：

1. `deploy/llm-gateway/compose.pilot.yaml`
   - SHA-256: `f2851c2803ecbeb5bcaa8d82520a038f5bd7ff2e0a63cb3187d903b5182a22c6`
2. `deploy/llm-gateway/litellm.pilot.yaml`
   - SHA-256: `eeaa19f4a5990c966de43b194f7b3f75dafcfebcaf1dfd87bbf3111399616785`
3. `deploy/llm-gateway/mock_upstream.py`
   - SHA-256: `cc8231e634c29c538f89449ae9da564616fee820d3c9f394625dd1d847aa9431`

任一 SHA 不匹配，立即停止。不得从 E 盘副本、历史 artifact、trusted-r1、旧 runner 或旧容器提取文件来替代。

### Gate A：远端 selector 与目标身份重新解析

只允许执行带精确 label filter 的 Docker 只读命令，不得先无过滤枚举全主机容器。

必须解析并记录：

- gateway 当前 container ID、name、service、scope、Compose project；
- gateway image reference、immutable image ID/digest、state、health、mounts、network；
- gateway-db 和 mock-upstream 的同类隔离身份；
- Compose working directory 和 config path；
- `smartbrain-llm-pilot_pilot` network ID 及其 isolated-pilot 成员；
- 不得读取 `Config.Env`，不得输出环境变量或 secret。

如果 selector：

- 命中 0 个 gateway；
- 命中多个 gateway；
- 命中任何不带 `smartbrain.scope=isolated-pilot` 的对象；
- 命中 `smartbrain-protocol-trusted-r1` 或其他历史/旁路对象；
- 指向与现有证据不同的 Compose project/root；

立即停止，不执行文件写入或服务启动。

### Gate B：远端文件状态与 runner 身份

只允许检查以下路径是否存在、文件类型、owner/mode 和 SHA-256；不得输出文件正文：

- `/srv/smartbrain-llm-pilot/compose.pilot.yaml`
- `/srv/smartbrain-llm-pilot/litellm.pilot.yaml`
- `/srv/smartbrain-llm-pilot/mock_upstream.py`

明确记录本轮实际远程 runner/transport 身份、执行命令和退出码。不得读取：

- `/srv/smartbrain-llm-pilot/.env`；
- API Key、Token、Cookie、Authorization；
- 数据库密码；
- prompt、response 或个人正文；
- 任何容器 `Config.Env`。

如果 runner 无法明确记录，立即停止。

### Gate C：允许的三文件修复

只有 Gate A 和 Gate B 都通过后，才允许修复以下三个文件：

- `/srv/smartbrain-llm-pilot/compose.pilot.yaml`
- `/srv/smartbrain-llm-pilot/litellm.pilot.yaml`
- `/srv/smartbrain-llm-pilot/mock_upstream.py`

要求：

1. 只从上述 authoritative source 传输；
2. 在同一目标目录使用临时文件；
3. 临时文件 SHA 必须先与 expected SHA 一致；
4. 再以原子替换方式落到目标路径；
5. 不覆盖、不读取 `.env`、数据库目录或任何未列出的文件；
6. 落盘后重新计算三个远端 SHA；
7. 任一远端 SHA 不匹配，立即停止，禁止启动 Gateway；
8. 不得复制 `identity_policy.py`、`trusted_identity.py`、`litellm.protocol.yaml` 或任何历史 trusted-r1 文件。

### Gate D：Compose 静态检查

三文件 SHA 全部一致后，只允许执行当前项目的静态 Compose render/config 校验：

- project root 必须是 `/srv/smartbrain-llm-pilot`；
- project name 必须是 `smartbrain-llm-pilot`；
- 不输出解析后的 secret 或环境变量；
- 镜像 digest、network、mount destination、port binding、restart policy 必须与候选和既有容器身份一致。

如静态配置需要读取/输出 secret，改用不会显示值的校验方式；不能安全校验则停止。

发现 compose/config 与当前容器存在实质身份漂移时，停止。不得 recreate。

### Gate E：只允许启动现有隔离 Gateway

仅当 Gate A-D 全部通过，才允许对 Gate A 解析出的唯一现有 gateway container 执行一次 `docker start`。

禁止：

- `docker compose up`；
- recreate；
- remove；
- pull/build；
- 启动或重启 gateway-db、mock-upstream、trusted-r1 或任何其他容器；
- 修改 network；
- 修改 `.env`；
- 修改生产服务。

启动后进行有界观察：

- container state；
- health；
- restart count；
- mount source/destination；
- image/digest/network；
- LiteLLM runtime version，只能使用不会发模型请求且不会输出 secret 的方式；
- 最多执行必要的本机 liveliness/health 请求，不得调用模型、mock 或 provider endpoint。

如果 Gateway 启动失败、退出、持续 unhealthy，或 identity 漂移：

- 不重试；
- 不 recreate；
- 如果它仍在运行但 unhealthy，允许仅对同一个已解析 gateway container 执行一次 `docker stop` 作为回退；
- 保存日志并停止。

### Gate F：P0 身份复核

Gateway healthy 后，仅允许重新核验 P0 身份：

- container/image/digest/network/mount；
- 三文件远端 SHA；
- source/config identity；
- runner identity；
- LiteLLM version；
- gateway 与隔离 PostgreSQL instance registration 的只读确定性绑定。

PostgreSQL 只允许最小只读查询：database、current_user、server_version、instance registration 和必要 schema identity。禁止 DML、DDL、migration、COMMIT 和具有副作用的函数。这不是 G1-P1 PostgreSQL gate。

### trusted identity policy 的强制停止条件

当前授权只恢复 baseline pilot 文件，不能把历史 trusted-r1 当成当前 policy。

如果恢复后的当前 config 没有唯一、当前、可验证的 trusted identity policy/hook，则：

- 可以如实记录 Gateway runtime/source/config 已恢复；
- 不得把 P0 identity qualification 标记为完整通过；
- 状态必须是 `runtime_repaired_but_policy_identity_unqualified` 或等价 blocked 状态；
- 不得进入 G1-P1、mock gate、provider 或模型验证；
- 不得自行把历史 `identity_policy.py`、`trusted_identity.py` 或 trusted-r1 config 挂入当前 Gateway。

只有 source/config/policy/runner/PG binding 全部明确且一致时，才能写 `p0_identity_qualification=passed`。否则仍为 blocked。

### 全程禁止

- 枚举或操作非 isolated-pilot 生产资源；
- 生产 PostgreSQL 访问；
- 生产 Key、路由、container、systemd、timer、nginx、tunnel 修改；
- 任何 migration、DDL、DML、COMMIT；
- G1-P1 isolated PostgreSQL gate；
- mock 业务请求；
- gateway 模型请求；
- provider 或真实模型请求；
- personal records flag 启用；
- Langfuse 恢复；
- G1 源码、测试、allowlist 修改；
- 使用历史 runner、历史 container、trusted-r1 或旧 tunnel；
- 输出 secret 或原始正文。

GPT-6 必须保持：

status=disabled_by_operator
executed=false
request_count=0
fallback_used=false

### 新证据文件

不得覆盖旧证据。生成：

- `E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-isolated-gateway-repair-approved-r1.log`
- `E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-isolated-gateway-repair-approved-r1.json`
- `E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-p0-identity-recovery-approved-r1.log`
- `E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-p0-identity-recovery-approved-r1.json`

JSON 必须记录：

- approval ID、授权有效期；
- transport alias 和生产资源排除声明；
- 每条命令、退出码和时间；
- selector 与实际命中对象；
- local/remote 三文件 SHA；
- 是否执行远程写入；
- 是否执行 Gateway start/rollback stop；
- health 请求数；
- PostgreSQL 只读查询数；
- gateway/mock/provider/model 请求数；
- source/config/policy/runner/PG binding identity；
- P0 最终状态；
- GPT-6 四个固定字段；
- 是否允许 G1-P1。

不要生成尚未执行 gate 的：

- `g1-isolated-pg.log`；
- `g1-real-models.log`；
- `g1-final-state.json`。

### 最终汇报

必须明确：

1. Gate A-F 每项结果；
2. 是否恢复了三个文件及远端 SHA；
3. 是否启动了现有 Gateway；
4. Gateway 最终 state/health；
5. source/config/policy/runner/PG binding 是否全部锁定；
6. P0 是 passed，还是 runtime repaired 但 policy 仍 blocked；
7. 是否访问任何生产资源；
8. health、PG、gateway、mock、provider、模型请求计数；
9. GPT-6 固定状态；
10. 是否允许 G1-P1。

没有完整身份闭环时，默认答案必须是：G1-P1/G2/灰度/生产均不允许。
```