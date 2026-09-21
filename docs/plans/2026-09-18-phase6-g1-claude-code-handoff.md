# Phase 6 G1 Claude Code handoff — P0 blocked, no execution beyond identity evidence

## Paste this prompt to Claude Code

```text
你是本轮 Phase 6 / G1 的执行工程师。先不要改代码、不要重复本地测试、不要启动任何服务。你的第一任务是读取并复核下面的真实证据，然后严格按 gate 停止或继续。

工作区边界
- authoritative source：D:\\AgentOpsServer\\AgentOps\\app
- 计划、日志、artifacts：E:\\智慧大脑agent - 服务器端
- 不得把 E 盘同名旧包当 authoritative source。
- 不得使用历史 runner、历史 container、旧 gateway、旧 tunnel 或历史 source 来补证据。

必须先读取
1. E:\\智慧大脑agent - 服务器端\\.artifacts\\gateway-g1-20260918-r1\\g1-p0-preflight-r2.json
2. E:\\智慧大脑agent - 服务器端\\.artifacts\\gateway-g1-20260918-r1\\g1-p0-discovery-authorization-r2.json
3. E:\\智慧大脑agent - 服务器端\\.artifacts\\gateway-g1-20260918-r1\\g1-p0-discovery-r2.log
4. E:\\智慧大脑agent - 服务器端\\.artifacts\\gateway-g1-20260918-r1\\g1-p0-container-inspect-r2.log
5. E:\\智慧大脑agent - 服务器端\\.artifacts\\gateway-g1-20260918-r1\\g1-p0-image-network-inspect-r1.log
6. E:\\智慧大脑agent - 服务器端\\.artifacts\\gateway-g1-20260918-r1\\g1-p0-host-file-hashes-r1.log
7. E:\\智慧大脑agent - 服务器端\\.artifacts\\gateway-g1-20260918-r1\\g1-p0-postgres-readonly-r2.log
8. E:\\智慧大脑agent - 服务器端\\.artifacts\\gateway-g1-20260918-r1\\g1-p0-management-db-summary-r1.log
9. E:\\智慧大脑agent - 服务器端\\.artifacts\\gateway-g1-20260918-r1\\g1-p0-postgres-schema-r1.log
10. E:\\智慧大脑agent - 服务器端\\docs\\plans\\2026-09-18-phase6-g1-next-instructions.md

当前已解析对象（只允许把这些作为候选身份，仍需复核）
- gateway：smartbrain-llm-pilot-gateway-1，ID 66d7be575889da0c1ccc0eecb303cd2e56def8dd21f20a01c640bc42bdd30c09，image ghcr.io/berriai/litellm:v1.100.1@sha256:a3715fa7ad8387941ab697259bd2881d68931657247a41984f90fae6d11c62bf，scope=isolated-pilot，当前 exited/unhealthy。
- PostgreSQL：smartbrain-llm-pilot-gateway-db-1，ID e39f937447a430da6985ce179731b19c152d101df4c1ae8d0232f9095e0f9cf1，scope=isolated-pilot，running/healthy，数据库 sb_key_management_test_r1，current_user gateway_pilot，PostgreSQL 16.10。
- mock：smartbrain-llm-pilot-mock-upstream-1，ID 939815c32d78c54f87c446aff66552a29ddcde9d0053babfcc4ec8d6e4076074，scope=isolated-pilot，running。
- 网络 smartbrain-llm-pilot_pilot 为 internal，但还挂着 smartbrain-protocol-trusted-r1（ID d0d873d3f5689a1fd2678fd14819662f78d2f06a8c23a7c39f0e9a7432fde2af）。这个历史/旁路对象不是本任务目标，禁止使用、禁止请求、禁止重启。

当前 P0 结论
- P0 discovery 成功，但 identity qualification 仍 blocked/not qualified。
- gateway 已 exited/unhealthy；不得 start、restart、stop、recreate，也不得发 gateway 请求。
- gateway 的 bind source /srv/smartbrain-llm-pilot/litellm.pilot.yaml 在核验时不存在；因此当前 gateway 的 config/source/policy SHA 和 runner identity 没有锁定。
- 历史 trusted-r1 配置路径也不存在；不得用历史 artifacts 的 SHA 冒充当前身份。
- PostgreSQL 只读身份、目标数据库、目标表、RLS、索引和约束已取得真实结果，但当前 gateway instance 无法与已注册记录做确定性绑定，所以这不构成 G1 preflight 通过。

硬性禁止
- 不得运行任何 gateway、mock、provider 或真实模型请求。
- 不得进入 isolated PG gate、mock gate 或真实模型 gate。
- 不得 docker exec gateway；不得读取 Config.Env、.env、API Key、Token、Cookie、Authorization、数据库密码或原始正文。
- 不得执行 INSERT/UPDATE/DELETE/DDL/migration/COMMIT；不得改变数据库。
- 不得启动、停止、重启、创建、删除或重建任何容器、服务、systemd/timer、nginx、tunnel。
- 不得修改 G1 源码、测试、allowlist 或 personal-records flag。
- 不得恢复 Langfuse。
- 不得调用 gpt-6-astra；它必须保持：status=disabled_by_operator, executed=false, request_count=0, fallback_used=false。

本轮允许的动作
1. 只读复核上述证据，并确认工作树没有被你修改。
2. 如需补充身份信息，只能使用新的、明确批准的只读命令；目标必须先由 smartbrain.scope=isolated-pilot 和当前 Compose project 解析，不得枚举生产资源。
3. 如果没有新的、明确批准的“gateway 修复/身份恢复”授权，立即停止，不要猜测路径，不要尝试 start/restart。
4. 仅在获得该新授权且 gateway 重新处于可运行状态后，重新做完整 P0：container/image/digest/network/config/source/policy/runner/LiteLLM version、PG identity/registration/schema/RLS/index/constraint。身份有任何冲突立即停止。
5. 只有 P0 完整通过后，才允许按既有计划依次执行：isolated PG gate -> mock gate -> 仅 Sol/Terra/Luna 最小验证。不得跳 gate，不得扩大请求量，不得重试轰炸。

本轮不得重复
- 不要重复本地 22 passed / 94 passed / py_compile；这些证据已存在。
- 不要伪造 g1-isolated-pg.log、g1-real-models.log 或 g1-final-state.json。

输出要求
- 如果仍 blocked：只生成一份本地阻断报告，包含真实命令、退出码、未执行项和证据路径；不得宣称 preflight、PG、mock、真实模型、G1、灰度或生产就绪。
- 如果后续新授权使 P0 通过，再按每个 gate 单独保存完整日志和 JSON 证据；任一 gate 失败立即停在该 gate。
- 最终报告必须明确：gateway/PG/mock/source/config/policy/runner identity、各 gate 状态、每个模型和 protocol 的真实结果、请求/失败/retry/fallback 数、GPT-6 零请求状态、是否允许 G2/灰度。当前默认答案是：G1 blocked，G2/灰度/生产均不允许。
```

## 当前交接结论

- P0 discovery：完成。
- P0 identity qualification：未完成；gateway exited/unhealthy，配置源缺失，runner/source/config/policy 未锁定。
- PostgreSQL 只读身份与 schema 观察：已完成，但不能替代 gateway identity qualification。
- G1-P1、mock、Sol/Terra/Luna：未开始。
- GPT-6：`disabled_by_operator`，零请求，无 fallback。
- G2、灰度、生产发布：不允许。

## 证据文件

- `.artifacts/gateway-g1-20260918-r1/g1-p0-preflight-r2.json`
- `.artifacts/gateway-g1-20260918-r1/g1-p0-discovery-authorization-r2.json`
- `.artifacts/gateway-g1-20260918-r1/g1-p0-discovery-r2.log`
- `.artifacts/gateway-g1-20260918-r1/g1-p0-container-inspect-r2.log`
- `.artifacts/gateway-g1-20260918-r1/g1-p0-image-network-inspect-r1.log`
- `.artifacts/gateway-g1-20260918-r1/g1-p0-postgres-readonly-r2.log`
- `.artifacts/gateway-g1-20260918-r1/g1-p0-management-db-summary-r1.log`
- `.artifacts/gateway-g1-20260918-r1/g1-p0-postgres-schema-r1.log`
