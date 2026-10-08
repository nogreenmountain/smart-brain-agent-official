# 服务器只读状态快照

核对时间：2026-10-08 09:30（Asia/Shanghai）。用途：开发接续和版本留存。精简机器清单见 [JSON](server-state-20261008.json)，版本与恢复范围见[基线](../releases/server-baseline-20261008.md)。

## 实际运行版本

共有 902 个容器、38 个运行；停止容器包含历史版本和试验现场，不能将总数解释为业务服务数量。第二轮快照按挂载目标排序后前后稳定；第一轮未排序挂载数组导致结构比较不稳定，其原始结果在私有证据中保留。

| 组件 | 镜像引用 | 状态 / 健康 |
|---|---|---|
| smartbrain-agentops-dashboard-1 | `smartbrain/agentops-dashboard:2026.09.24-project-context-r9` | running / 未配置健康检查 |
| smartbrain-wiki-mcp-1 | `smartbrain/wiki-mcp@sha256:f082527c40bb30d645072afeafcf8c76bf61b6589cdf6ca46017d14c09f0a1b4` | running / healthy |
| smartbrain-workday-records-unified-20260921-profile-url | `smartbrain/agentops-dashboard:2026.09.22-workday-records-r1` | running / 未配置健康检查 |
| smartbrain-smartbrain-reverse-tunnel-1 | `smartbrain/reverse-tunnel:ubuntu-2026.08.28.2` | running / healthy |
| smartbrain-personal-key-api-20260923-filter-internal-r1 | `smartbrain/personal-key-api:2026.09.24-request-id-r1` | running / 未配置健康检查 |
| smartbrain-api-20260923-filter-internal-r1 | `smartbrain/api:2026.09.24-project-context-r1` | running / 未配置健康检查 |
| smartbrain-postgres-1 | `public.ecr.aws/supabase/postgres:15.8.1.085` | running / healthy |
| smartbrain-workday-gateway-body-20260923-filter-internal-r1 | `smartbrain/workday-gateway-read:2026.09.23-filter-internal-r1` | running / 未配置健康检查 |
| smartbrain-llm-pilot-gateway-1 | `ghcr.io/berriai/litellm:v1.100.1@sha256:a3715fa7ad8387941ab697259bd2881d68931657247a41984f90fae6d11c62bf` | running / healthy |
| smartbrain-llm-pilot-gateway-db-1 | `postgres:16.10-alpine@sha256:029660641a0cfc575b14f336ba448fb8a75fd595d42e1fa316b9fb4378742297` | running / healthy |
| smartbrain-redis-1 | `redis:7.4.2-alpine` | running / healthy |
| smartbrain-edge-1 | `nginx:1.27.5-alpine` | running / healthy |

镜像 ID、启动时间和重启计数在 JSON 内。`health` 缺失表示未配置该检查，不代表健康或故障。当前主页面入口指向新 dashboard，另一个 workday-records-unified 入口仍对应较早容器；实际映射已分别记录，不能只看某个容器名称判断全站版本。

## 入口验证与配置

- 严格 TLS GET：login、profile、workday、health/ready 均 200。
- 匿名 GET：Key、operations、records、个人模型入口均 401。
- Edge 宿主配置与容器实际绑定文件 SHA-256 相同，inode 仍不同；不能用一次宿主 atomic replace 推导活动配置变化。
- 仅做匿名读取，没有登录用户功能闭环、用户正文读取或模型请求。

## 生命周期、备份及容量

- 备份服务最近一次执行于 2026-10-08 02:45:36–02:45:40，failed/exit 1，MainPID=0、Job 空；备份 timer active/waiting。失败原因本轮未追查，不重跑原批次。
- 前端和 workday read unit active/running；personal registered API unit enabled 但 inactive。个人代理容器仍运行，须另核对 unit 与实际容器绑定。
- 旧 tunnel unit failed，但 Docker reverse tunnel healthy，公网可访问；未证明 unit 恢复或整机重启闭环。
- reconcile service 已安装但 inactive，timer disabled，管理 feature gate 文件不存在。不能宣称 Key 状态机 worker 已启用。
- maintenance pending intent 不存在。历史测试 unit 的 failed 状态不自动代表当前业务故障。
- Docker 29.7.2；可用内存约 5.6 GiB。各数据卷容量见 JSON；Docker 卷可用约 32.31 GiB，低于既有 40 GiB 发布门槛；本轮不清理旧镜像、容器或证据。

## 数据库只读核对

选定迁移登记查询仅返回 `20260923000000`；Key 管理四表与 project_conversation_records 实际存在。旧两项未出现在该登记查询中，不能据此断言表结构不存在，也不能重跑迁移。没有读取员工行或正文，没有进行 DDL。

## 与开发工作区的关系

本地 gateway.py、personal_gateway_proxy.py 的归一化 hash 与个人代理容器相同；ai_usage.py、ai_gateway.py 与若干活动容器不同。主 API、个人代理、read 服务之间还存在源码版本差异。具体线上 hash 保留在本地私有观察中；本次 Git 快照不替代任何线上镜像。

后续先核对备份失败、磁盘门槛、生命周期绑定及需要发布的权威源码。当前观察不是冻结备份或恢复合格点，本轮生产写入、迁移、重启、Key 变更和模型调用均为 0。
