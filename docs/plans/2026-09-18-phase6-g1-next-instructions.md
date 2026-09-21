# 阶段六 G1 下一步执行指示

- 文档日期：2026-09-18
- 当前阶段：Phase 6 / G1
- 当前状态：部分完成，未完成资格认证，未进入 G2、灰度或生产
- 执行对象：Claude Code
- 证据/计划工作目录：`E:\智慧大脑agent - 服务器端`
- authoritative source 根目录：`D:\AgentOpsServer\AgentOps\app`

重要路径边界：

- 代码、测试和 authoritative source 身份必须以 `D:\AgentOpsServer\AgentOps\app` 为准；
- 计划文档、checkpoint、日志和 artifacts 位于 `E:\智慧大脑agent - 服务器端`；
- 不得因为 E 目录存在同名包、旧副本或旧测试，就把 E 目录当作 authoritative source；
- 不得切换到历史 source、旧 runner 或旧 container 来“补齐”当前证据；
- 执行前必须记录实际使用的 source 根目录及其 SHA/manifest。

## 1. 任务目标

完成阶段六 G1 的隔离环境资格认证前置工作，并在权限允许后，依次完成：

1. 隔离 gateway 与隔离 PostgreSQL 的只读身份 preflight；
2. 隔离 PostgreSQL gate；
3. 隔离 mock gateway/network gate；
4. 仅对当前启用的三个模型进行最小真实验证；
5. 生成可审计的 G1 证据和最终状态。

本任务不是生产发布任务，不是灰度任务，也不是 G2。不得因为本地测试通过而宣布 G1 完成。

## 2. 当前已确认事实

本地阶段已经完成，无需重复执行原有本地回归：

- G1 本地协议/身份/用量矩阵：22 passed；
- 相关本地回归：94 passed；
- `py_compile`：通过；
- 当前矩阵总数：192 cells；
- `gpt-6-astra`：48 个 cell，全部为 `disabled_by_operator`；
- GPT-6 请求数：0；
- fallback：未发生；
- 产品候选 allowlist 仍保留四个模型：
  - `gpt-5.6-sol`
  - `gpt-5.6-terra`
  - `gpt-5.6-luna`
  - `gpt-6-astra`

当前证据目录：

- `.artifacts/gateway-g1-20260918-r1/g1-checkpoint.json`
- `.artifacts/gateway-g1-20260918-r1/protocol-model-matrix.json`
- `.artifacts/gateway-g1-20260918-r1/preflight-readonly.json`
- `.artifacts/gateway-g1-20260918-r1/g1-local-tests.log`

当前准确结论：

> 阶段六 G1 部分完成。隔离只读 preflight 曾被权限分类器阻断；没有执行远程命令、gateway 请求、PostgreSQL 查询、mock 请求或真实模型请求。GPT-6 由操作者禁用且未执行。未进入灰度，未进行生产变更。

## 3. GPT-6 操作策略（不可违反）

`gpt-6-astra` 当前由操作者禁用，必须保持以下状态：

```json
{
  "status": "disabled_by_operator",
  "executed": false,
  "request_count": 0,
  "fallback_used": false,
  "reason": "operator_disabled_relay_model"
}
```

严格禁止：

- 调用 `gpt-6-astra`；
- 自动恢复或启用 GPT-6；
- 用 Sol、Terra 或 Luna 替代 GPT-6；
- 把 GPT-6 标记为 provider failure、unsupported、timeout、cooldown 或 passed；
- 删除 GPT-6 allowlist 项；
- 修改模型名称冒充 GPT-6；
- 因 GPT-6 禁用而偷偷改变 G1 产品范围。

如果 Sol/Terra/Luna 后续全部通过，只能称为：

> three-model partial G1 candidate validation

不能称为：

- complete four-model G1；
- four-model G1 passed；
- ready for gray rollout；
- production ready。

## 4. 总体安全边界

整个任务期间禁止：

- 绕过权限或安全分类器；
- 改用未批准的写入工具或远程执行路径；
- 执行生产 migration、DDL 或任何生产数据库写操作；
- 修改生产 Key、路由、container、systemd、timer、nginx；
- 启用 personal records feature flag；
- 接入真实员工；
- 恢复 Langfuse；
- 使用历史 container ID、旧 gateway、旧 runner 或旧 tunnel；
- 启动、停止、重启生产或隔离服务；
- 在 preflight、PG gate、mock gate 通过前调用任何真实模型；
- 为了迎合测试修改测试、放宽身份校验或伪造结果。

所有证据必须记录真实结果。不得把“文件存在”写成“验证通过”，不得把“本地测试通过”写成“隔离 G1 通过”。

## 5. 第一阶段：只读 preflight 与身份锁定

### 5.1 先读取现有文件

只读读取以下文件，确认当前状态，不要修改：

- `.artifacts/gateway-g1-20260918-r1/g1-checkpoint.json`
- `.artifacts/gateway-g1-20260918-r1/protocol-model-matrix.json`
- `.artifacts/gateway-g1-20260918-r1/preflight-readonly.json`
- `.artifacts/gateway-g1-20260918-r1/g1-local-tests.log`
- `agentops_local/ai_usage/llm_key_runtime.py`
- `agentops_local/tests/test_g1_protocol_matrix_local.py`

### 5.2 只读检查范围

只有在获得明确允许的只读执行路径后，才可检查当前隔离环境。必须先解析当前对象身份，再对解析后的对象执行后续检查。

#### 当前隔离 gateway

只读确认：

- 当前隔离 gateway container ID；
- image reference、immutable image ID、digest；
- container state、created time、started time；
- 当前非敏感配置版本信息；
- source/config/policy SHA-256；
- network ID 与 network name；
- LiteLLM 版本；
- 当前 runner/source identity。

不得打印：

- API Key；
- Token；
- Cookie；
- Authorization；
- 原始正文；
- 其他 secret。

#### 当前隔离 PostgreSQL

只能使用预批准的只读角色，确认：

- 当前隔离数据库名；
- `current_user`；
- `server_version`；
- 当前连接目标身份；
- gateway instance 注册记录；
- 当前迁移版本；
- 目标表是否存在；
- 必要的 RLS、索引和约束状态。

禁止执行：

- `INSERT`、`UPDATE`、`DELETE`；
- DDL；
- `COMMIT`；
- 具有副作用的函数；
- migration；
- 任何生产数据库访问。

#### 隔离资源状态

只检查当前隔离 gateway、隔离 PG、当前 mock 和当前 runner：

- 进程；
- 监听端口；
- 临时 tunnel；
- 资源状态；
- 维护状态。

不得启动、停止或重启服务。

### 5.3 身份不一致时停止

如果以下任一项无法确认或相互不一致，立即停止：

- container；
- image/digest；
- network；
- source SHA；
- config/policy SHA；
- PostgreSQL 身份；
- runner identity。

不得根据历史记录猜测目标，也不得使用看起来相似的历史对象继续执行。

### 5.4 如果权限分类器再次阻断

如果只读 preflight 再次被权限分类器拒绝：

1. 立即停止；
2. 不执行 gateway 请求；
3. 不执行 PostgreSQL 查询；
4. 不执行 mock 请求；
5. 不执行真实模型请求；
6. 不切换其他工具绕过分类器；
7. 不修改生产或隔离配置。

如果允许本地写证据，只生成或更新：

`.artifacts/gateway-g1-20260918-r1/g1-preflight-blocked.json`

内容至少包含：

```json
{
  "phase": "phase6-g1",
  "status": "blocked",
  "remote_commands_executed": 0,
  "gateway_requests": 0,
  "postgres_queries": 0,
  "mock_requests": 0,
  "real_model_requests": 0,
  "production_changes": false,
  "bypass_attempted": false,
  "gpt6_status": "disabled_by_operator",
  "gpt6_requests": 0,
  "fallback_used": false
}
```

此时不得声称 preflight、PG、mock、三模型验证或 G1 已完成。

## 6. 第二阶段：隔离 PostgreSQL gate

只有在只读 preflight 通过且身份已锁定后，才可执行此阶段。

要求：

- 使用当前解析出的隔离 PG；
- 使用当前批准 runner；
- 不得复用历史 PG、container、tunnel 或 runner；
- 只执行现有隔离 PG 测试入口；
- 保留真实失败，不得修改测试迎合结果。

至少覆盖：

- instance identity；
- credential identity；
- owner/credential/instance 隔离；
- usage provenance；
- migration/schema；
- RLS；
- 失败和状态隔离；
- 当前 G1 所需的约束与索引。

保存完整日志：

`.artifacts/gateway-g1-20260918-r1/g1-isolated-pg.log`

PG gate 未通过时，不得进入 mock 或真实模型阶段。

## 7. 第三阶段：隔离 mock gateway/network gate

只有在 PG gate 通过后执行现有 mock 测试，覆盖：

- Chat；
- Responses；
- Codex/plugin；
- SSE；
- tool call / additional tools；
- 多轮请求；
- 长正文；
- trusted identity；
- user/credential/instance 隔离；
- usage `missing` / `present` 信号；
- failed/cancelled/overloaded/cooldown 等失败状态；
- no-fallback 约束；
- 敏感字段不进入日志或记录；
- 不调用真实上游模型。

不得把 `estimated provenance` 写成已经实现；只能记录代码真实提供的 `missing/present` 信号。

如项目已有固定 mock 日志入口，沿用现有入口、runner 和命名。不得重建旧 runner 或旧 container。

## 8. 第四阶段：三个启用模型的最小真实验证

只有以下条件全部满足后才允许执行：

- 只读 preflight 通过；
- gateway/container/source identity 已锁定；
- PG gate 通过；
- mock gate 通过；
- 请求明确不会进入生产；
- personal records flag 仍关闭；
- 没有真实员工接入；
- 没有生产 Key、路由、container、systemd、timer、nginx 或 migration 改动。

只允许验证：

- `gpt-5.6-sol`；
- `gpt-5.6-terra`；
- `gpt-5.6-luna`。

按照现有 `protocol-model-matrix.json` 的最小固定请求执行，不得自行扩大请求量，不得做重试轰炸。

每个请求至少记录：

- model；
- protocol；
- request id；
- instance id；
- credential identity；
- HTTP/SDK 最终状态；
- provider/gateway usage 原始状态；
- 是否发生 retry；
- 是否发生 fallback；
- response 完整性；
- 对应 PG 记录；
- 实际请求数；
- 失败原因。

GPT-6 必须保持未调用。

## 9. 第五阶段：证据文件与最终状态

只有实际执行完成后，才可生成或更新：

- `.artifacts/gateway-g1-20260918-r1/preflight-readonly.json`
- `.artifacts/gateway-g1-20260918-r1/g1-isolated-pg.log`
- `.artifacts/gateway-g1-20260918-r1/g1-real-models.log`
- `.artifacts/gateway-g1-20260918-r1/g1-final-state.json`
- `.artifacts/gateway-g1-20260918-r1/g1-checkpoint.json`

最终状态必须区分：

### 只读权限仍被阻断

```text
status = blocked
complete_four_model_g1 = false
g2_or_gray_release_allowed = false
```

### 只读、PG、mock 通过，但三个启用模型未全部完成

```text
status = partially_qualified
complete_four_model_g1 = false
g2_or_gray_release_allowed = false
```

### Sol/Terra/Luna 全部通过，但 GPT-6 仍禁用

```text
status = three_model_partial_g1_candidate
complete_four_model_g1 = false
g2_or_gray_release_allowed = false
gpt6_status = disabled_by_operator
gpt6_request_count = 0
fallback_used = false
```

必须明确写出：这不是完整四模型 G1，也不允许 G2 或灰度。

只有在 GPT-6 被操作者明确重新启用、产品范围仍为四模型，并且 GPT-6 完成相同隔离验证后，才可以重新评估完整 G1。

## 10. Claude Code 最终汇报格式

完成或阻断时，必须汇报：

1. 实际执行的命令；
2. 实际使用的 container/image/network/source/PG identity；
3. preflight、PG、mock、真实模型各 gate 的真实结果；
4. 每个模型和 protocol 的真实状态；
5. 请求数、失败数、retry 数、fallback 数；
6. GPT-6 明确为 `disabled_by_operator` 且请求数为 0；
7. 生成了哪些证据文件；
8. 是否仍允许进入 G2 或灰度；
9. 所有未解决阻塞及对应证据路径。

禁止使用以下表述，除非证据确实满足条件：

- “G1 已完成”；
- “四模型通过”；
- “可以灰度”；
- “可以上线”；
- “preflight 已通过”；
- “真实模型已验证”。
