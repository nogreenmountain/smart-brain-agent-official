# Phase 6 G1 — isolated Gateway repair and identity recovery handoff

## Purpose

This is the next step after the confirmed G1-P0 block. It authorizes Claude Code to repair only the currently selected isolated pilot Gateway filesystem state, then repeat P0 identity qualification. It does not authorize PostgreSQL gate, mock gate, provider calls, model calls, gray rollout, or production release.

The current failure is concrete: the selected Gateway container is `smartbrain-llm-pilot-gateway-1`, state `exited/unhealthy`, and its bind source `/srv/smartbrain-llm-pilot/litellm.pilot.yaml` was absent during P0 inspection. The current Compose project also references missing host files. The repair must restore only an authoritative, current candidate and then prove identity again.

## Source and target boundary

- Authoritative source: `D:\AgentOpsServer\AgentOps\app`
- Evidence and artifacts: `E:\智慧大脑agent - 服务器端`
- Isolated target root: `/srv/smartbrain-llm-pilot`
- Compose project: `smartbrain-llm-pilot`
- Target selector: `smartbrain.scope=isolated-pilot` plus the current Compose project; never select by a historical container ID alone.
- Candidate manifest: `E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-isolated-gateway-repair-candidate-r1.json`

## Paste this prompt to Claude Code

```text
你是 Phase 6 / G1 的隔离 Gateway 修复与身份恢复工程师。当前任务只允许修复当前 isolated-pilot Gateway 的缺失非敏感文件，然后重新执行 P0 identity qualification。不要直接进入 PG gate、mock gate、provider 或真实模型验证。

### 目标

解决已复现的 P0 根因：
- 当前目标 gateway：smartbrain-llm-pilot-gateway-1；
- 当前容器状态：exited/unhealthy；
- 当前容器原始 bind source：/srv/smartbrain-llm-pilot/litellm.pilot.yaml；
- 该 source 在 P0 检查时不存在；
- 当前 Compose 项目引用的 compose.pilot.yaml、litellm.pilot.yaml、mock_upstream.py 也必须重新从 authoritative source 建立可审计身份。

本提示词只覆盖 isolated-pilot repair/identity recovery。不得把 repair candidate 当成运行成功证据。

### 必须先读取

1. E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-isolated-gateway-repair-candidate-r1.json
2. E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-checkpoint.json
3. E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-p0-preflight-r2.json
4. E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-p0-discovery-authorization-r2.json
5. E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-p0-container-inspect-r2.log
6. E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-p0-host-file-hashes-r1.log
7. E:\智慧大脑agent - 服务器端\docs\plans\2026-09-18-phase6-g1-next-instructions.md
8. E:\智慧大脑agent - 服务器端\docs\plans\2026-09-18-phase6-g1-isolated-gateway-repair-handoff.md

### authoritative source

只允许使用以下当前 authoritative files，并在任何远程写入前重新计算 SHA-256：

- D:\AgentOpsServer\AgentOps\app\deploy\llm-gateway\compose.pilot.yaml
  - expected SHA-256: f2851c2803ecbeb5bcaa8d82520a038f5bd7ff2e0a63cb3187d903b5182a22c6
- D:\AgentOpsServer\AgentOps\app\deploy\llm-gateway\litellm.pilot.yaml
  - expected SHA-256: eeaa19f4a5990c966de43b194f7b3f75dafcfebcaf1dfd87bbf3111399616785
- D:\AgentOpsServer\AgentOps\app\deploy\llm-gateway\mock_upstream.py
  - expected SHA-256: cc8231e634c29c538f89449ae9da564616fee820d3c9f394625dd1d847aa9431

如果任意 SHA 不匹配，立即停止。不得使用 E 盘副本、历史 artifacts 内容、历史 trusted-r1 文件或旧 runner 作为替代。

### 身份和目标解析

在任何写入、启动或重建前：

1. 只读取当前远端 Docker/Compose 元数据，确认目标同时满足：
   - Compose project = smartbrain-llm-pilot；
   - smartbrain.scope=isolated-pilot；
   - service/gateway 或对应 gateway-db/mock-upstream 服务属于该项目。
2. 明确列出当前目标的 container ID、image reference、immutable image ID/digest、network、working directory、compose config path、mounts、state。
3. 如果 selector 命中生产对象、历史 trusted-r1 对象、旁路对象或多个无法区分的对象，立即停止。
4. 禁止使用历史 container ID 作为唯一身份；历史 ID 只能用于比对并且不能被启动或重建。

### 允许的远程写入范围

只有在 source SHA 和目标 selector 都通过后，才允许写入以下三个非敏感文件：

- /srv/smartbrain-llm-pilot/compose.pilot.yaml
- /srv/smartbrain-llm-pilot/litellm.pilot.yaml
- /srv/smartbrain-llm-pilot/mock_upstream.py

写入要求：
- 先保存目标文件当前存在的非敏感元数据和 SHA；不要读取或输出 .env、密码、Master Key、Token、Cookie、Authorization 或任何 API Key。
- 使用临时文件、SHA 校验和原子替换；若文件不存在则安全创建。
- 不得覆盖 `/srv/smartbrain-llm-pilot/.env`、数据库目录、证书、密钥或任何未列入上述清单的文件。
- 写入后立刻重新计算远端三个文件 SHA，并与本地 expected SHA 逐项比较。
- 任何一个不匹配，立即停止，不启动服务。

### policy 边界

当前候选 compose/config 不足以证明 trusted identity policy 已经挂载。不得自行加入以下历史文件，也不得使用历史 SHA 冒充当前身份：

- protocol-20260915-r1/trusted-r1/config.yaml
- protocol-20260915-r1/trusted-r1/identity_policy.py
- protocol-20260915-r1/trusted-r1/trusted_identity.py
- smartbrain-protocol-trusted-r1 容器

如果 G1 的当前 gate 明确要求 trusted identity hook，而现有 authoritative compose/config 没有唯一、当前、可验证的 policy 来源：

- 不得启动 Gateway；
- 生成 blocked repair report；
- 说明 policy identity unresolved；
- 等待新的明确授权或新的 authoritative source manifest。

### 修复后的 P0 复核顺序

修复文件并通过 SHA 校验后，才可以在 isolated-pilot 范围内进行必要的服务生命周期动作：

1. 仅针对当前 Compose project 的 gateway、gateway-db、mock-upstream 做 compose config/render 校验；
2. 不读取秘密值；
3. 仅在配置、目标、镜像 digest、network 和 source manifest 一致后，允许启动/重建 isolated-pilot gateway 及其依赖；
4. 不得操作生产容器、systemd、timer、nginx、隧道或历史 trusted-r1；
5. 启动后只做健康检查和身份校验，不发送 gateway、mock、provider 或模型业务请求；
6. 重新记录：container ID、image reference/digest、network ID、config/source SHA、runner identity、LiteLLM version、mount SHA、gateway state/health。

### P0 通过条件

只有以下条件全部满足，才可以把 identity qualification 标记为 passed：

- 当前 gateway container 确实由 smartbrain-llm-pilot Compose project 创建；
- `smartbrain.scope=isolated-pilot` 且 role/service 正确；
- image reference、immutable digest、network 与 approved candidate 一致；
- 远端 compose/config/mock 文件 SHA 与 authoritative manifest 一致；
- runner/source/config/policy identity 均明确；policy 如果不适用，必须明确记录 `not_applicable` 及理由；
- LiteLLM runtime version 已观察；
- 隔离 PostgreSQL 身份可与当前 gateway instance 确定绑定；
- 没有生产对象命中、没有历史对象复用、没有旁路 network 使用；
- 没有发送任何 gateway、mock、provider 或真实模型请求；
- GPT-6 状态未变化。

任意一项不满足，状态必须是 `blocked / not_qualified`。

### 禁止事项

- 不得访问生产主机或生产数据库；
- 不得使用 smartbrain-prod 作为新的执行目标；
- 不得启动、停止、重启或重建生产服务；
- 不得执行 PostgreSQL INSERT/UPDATE/DELETE/DDL/migration/COMMIT；
- 不得进入 isolated PostgreSQL gate；
- 不得进入 mock gate；
- 不得发送 provider 或真实模型请求；
- 不得调用 gpt-6-astra；
- 不得启用 personal records flag；
- 不得恢复 Langfuse；
- 不得修改 G1 源码、测试、allowlist 或业务路由；
- 不得输出任何 API Key、Token、Cookie、Authorization、密码或原始正文。

GPT-6 必须始终保持：

status=disabled_by_operator
executed=false
request_count=0
fallback_used=false

### 证据要求

本轮必须新建本地证据，不得覆盖历史证据：

- E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-isolated-gateway-repair-r1.log
- E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-isolated-gateway-repair-r1.json
- E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-p0-identity-recovery-r1.log
- E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-p0-identity-recovery-r1.json

JSON 至少包含：

- source_root；
- candidate manifest 和每个源文件 SHA；
- target selector；
- 目标 container/image/digest/network；
- 每个远程命令和退出码；
- 写入文件清单；
- 是否读取秘密；
- 是否访问生产；
- gateway/mock/provider/model 请求数；
- policy identity；
- runner identity；
- P0 状态；
- GPT-6 四个固定字段；
- 未完成 gate；
- 下一步是否允许 P1。

如果仍然 blocked，只能生成阻断证据，不得伪造：

- g1-isolated-pg.log；
- g1-real-models.log；
- g1-final-state.json；
- G1 passed；
- G2 allowed；
- gray rollout allowed；
- production ready。

### 最终汇报格式

按以下顺序汇报：

1. 本轮是否执行远程写入；
2. 实际使用的 authoritative source 和 SHA；
3. 实际目标 selector 和 container/image/network identity；
4. 三个候选文件的远端 SHA 校验；
5. 是否启动/重建 isolated gateway；若是，给出仅隔离对象的证据；
6. source/config/policy/runner identity 是否全部锁定；
7. P0 identity qualification 是 passed 还是 blocked；
8. gateway、PG、mock、provider、真实模型请求数；
9. GPT-6 固定状态；
10. 新生成的证据路径；
11. 是否允许 G1-P1。默认答案是：没有完整身份闭环就 blocked，G1-P1/G2/灰度/生产均不允许。
```

## Current candidate evidence

Candidate manifest:

`E:\智慧大脑agent - 服务器端\.artifacts\gateway-g1-20260918-r1\g1-isolated-gateway-repair-candidate-r1.json`

The candidate manifest is preparation metadata only. It is not evidence that the Gateway is running, healthy, qualified, or authorized for G1-P1.

## Hard stop conditions

Stop before any lifecycle action if:

- any candidate SHA differs;
- target selector is ambiguous;
- target is production, historical trusted-r1, or a sidecar/旁路 object;
- `.env` or secret material would need to be read or changed;
- current policy identity is not uniquely established;
- PostgreSQL instance binding is ambiguous;
- any command would touch production or perform DDL/DML/migration;
- the tool safety classifier blocks an allowed action.

The existing overall status remains:

```text
Phase 5 C: candidate closure and isolated qualification complete; not production released
Phase 6 G1 P0 discovery: complete
Phase 6 G1 P0 identity qualification: blocked / not qualified
G1-P1: not allowed
G2: not allowed
gray rollout: not allowed
production: not allowed
GPT-6: disabled_by_operator, zero requests, no fallback
```
