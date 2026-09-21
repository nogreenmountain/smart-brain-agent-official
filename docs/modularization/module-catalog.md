# SmartBrain 模块目录

本目录描述的是当前代码的目标逻辑边界，不代表已经完成物理拆分，也不代表模块已经可以独立部署。

| 编号 | 模块 | 当前主要路径 | 数据边界 | 当前独立性 | 首要前置条件 |
|---|---|---|---|---|---|
| M01 | platform-core | `api/agentops/auth`、`agentops_local/auth`、`common` | users、orgs、user_orgs、audit_logs | 不可独立 | 稳定认证/权限 port |
| M02 | project-management | `projects.py`、`team_members.py`、项目迁移 | projects、departments、project_members、requests | 不可独立 | 依赖 M01，禁止跨域清理 |
| M03 | content-rag | `knowledge.py`、`project_materials.py`、`rag/`、`rag_services/` | documents、chunks、materials、storage | 部分可独立测试 | 内容标准化接口 |
| M04 | project-memory | `project_memory/`、记忆页面和迁移 | memory drafts、repositories、review queue | 不可独立 | 解除与 Wiki/RAG 双向依赖 |
| M05 | wiki | `project_wiki/`、`member_wiki/`、`wiki_mcp/` | wiki pages、experiences、versions、tokens | 不可独立 | 统一 Wiki read/write port |
| M06 | work-records | `workday/`、`meeting_summaries/`、employee adapters | meetings、workday、daily logs | 不可独立 | 固定员工身份和 OTEL contract |
| M07 | ai-usage | `ai_usage/`、ClickHouse 查询 | ai chat、daily logs、OTEL usage | 不可独立 | 统一计量来源和隐私口径 |
| M08 | personal-gateway | `ai_gateway.py`、`gateway*.py`、Key UI | gateway keys、llm operations、credentials | 候选阶段 | 冻结未提交实现和外部协议 |
| M09 | observability | `api` traces、OTEL、ClickHouse | otel traces、spans、logs | 技术上较独立 | 固定写入 schema 和身份字段 |
| M10 | employee-agent | `employee_telemetry/`、`employee-deploy/` | 本地采集，不直接拥有业务表 | 可独立版本化 | 固定 Monitor/Workday API |
| M11 | runtime-infra | `deploy/`、Compose、nginx、Jockey、backup | 不拥有业务表 | 可独立维护但不独立业务发布 | 环境契约和 secret policy |
| M12 | legacy-agentops | `api/`、`dashboard/`、`landing/` | 原 AgentOps 全部数据 | 兼容边界 | 明确保留/退休范围 |

## 模块优先级

### 先治理、不拆仓

M01、M02、M03、M04、M05、M06、M07、M08 目前都依赖同一应用、认证和数据库。第一阶段应只建立目录边界、接口和测试约束。

### 可以较早独立版本化

M09、M10、M11 具有较清晰的技术边界，但仍需共享稳定的 API、schema 和部署契约。独立版本化不等于立即创建独立仓库。

### 必须单独决策

M12 是原始 AgentOps 产品边界。不能在没有产品保留/退休决定的情况下将其文件移动到 SmartBrain 模块。
