# SmartBrain 依赖关系分析

## 分析方法

本报告使用当前源码的静态扫描结果：前端路由和 API client 字符串、FastAPI 路由注册、Python import、SQL 字符串中的表名、迁移文件、worker 入口、Compose/Docker/部署文件。未执行数据库查询、Docker 重建、真实模型调用或生产探针。

依赖类型分为：直接代码依赖、间接依赖、数据库耦合、运行时耦合、部署耦合、权限耦合、共享类型耦合和历史耦合。

## 页面到 API

| 前端区域 | 主要 API client 函数/路径 | 后端路由 | 主要耦合 |
|---|---|---|---|
| 登录/个人资料 | `login`、`getMe`、`updateMyProfile` | `auth_me.py` | 认证会话、Cookie、用户表 |
| 项目/团队/成员 | `listProjects`、项目成员和团队函数 | `projects.py`、`team_members.py` | 组织、项目、成员、RLS |
| 知识/上传 | `searchKnowledge`、`answerQuestion`、材料上传函数 | `knowledge.py`、`project_materials.py` | 项目权限、对象存储、RAG、文档表 |
| 项目记忆 | `listProjectMemoryDepartments`、draft/review 函数 | `project_memory.py` | 项目、材料、会议、Wiki、审核 |
| 项目 Wiki | Wiki overview/compile/review/MCP 函数 | `project_wiki.py` | 项目记忆、RAG、MCP token、worker |
| 成员 Wiki | `getMemberWikiOptions`、`getMemberWikiOverview` | `member_wiki.py` | 用户、成员、聊天、RAG、worker |
| 会议 | `listMeetingSummaries`、`createMeetingSummary` | `meeting_summaries.py` | 项目成员、上传文件、AI 用量 |
| 工作日/日志 | `getWorkdaySummary`、日报函数 | `workday.py`、`ai_usage.py` | OTEL/ClickHouse、员工身份 |
| AI 用量 | leaderboard/records/report/session 函数 | `ai_usage.py` | PostgreSQL、ClickHouse、Redis、模型 |
| AI Monitor | `getAIMonitorStatus` | `ai_monitor.py` | 员工身份、共享会话、用量 |
| Personal Gateway | Gateway key/operation 函数 | `ai_gateway.py` | 当前未提交候选、Key 表、认证和用量 |

## API 到后端服务/基础设施

| API/服务 | 直接依赖 | 运行时依赖 | 是否可独立部署 |
|---|---|---|---|
| 认证 | `agentops.auth.middleware`、Supabase auth/users | Cookie、JWT、PostgreSQL | 否，平台基础能力 |
| 项目/成员 | ORM、RAG authz、audit | PostgreSQL/RLS | 暂不可以 |
| 知识/材料 | RAG ingest/search、文件解析、存储 | PostgreSQL、对象存储、embedding/reranker | 暂不可以 |
| 项目记忆 | RAG ingest、项目 Wiki service、会议 domain | PostgreSQL、模型、文件存储 | 暂不可以 |
| 项目/成员 Wiki | compiler/service/query/worker、RAG | PostgreSQL、模型、定时运行 | 暂不可以 |
| 会议 | meeting domain/query、材料解析、RAG client | PostgreSQL、对象存储、模型 | 暂不可以 |
| 工作日 | workday domain/query、ClickHouse client | ClickHouse、员工身份、OTEL | 暂不可以 |
| AI 用量 | ClickHouse、ORM、reporting、audit | PostgreSQL、ClickHouse、Redis、模型 | 暂不可以 |
| Gateway | Key runtime/quota/operations、认证、用量 | PostgreSQL、外部 Gateway、缓存 | 当前不可以 |
| Wiki MCP | member/project Wiki query/service、RAG authz | PostgreSQL、模型、网络入口 | 可单独进程运行，但业务上仍强耦合 |
| Jockey | Redis queue、Kubernetes/Docker 模板 | Redis、部署目标 | 可单独运行，但属于 infra |

## 后端到数据库/数据源

### 平台和项目

- `users`、`auth.users`、`user_orgs`、`orgs`、`org_invites`：认证、组织和成员权限共同使用。
- `projects`、`project_members`、`departments`、`project_department_migrations`、`project_creation_requests`：项目管理、权限、材料、Wiki 和审计共同使用。
- `audit_logs`：多数写操作都会调用审计能力。

### 内容和知识

- `documents`、`document_chunks`、`document_chunks_v2`：RAG 和资料模块共同使用。
- `project_material_documents`、`project_material_intakes`、统一内容/审核相关表：上传、项目管理、知识和记忆共同使用。
- 本地材料卷/对象存储：材料、会议附件、下载接口共同使用。

### Wiki/记忆/会议

- `project_memory_drafts`、`project_memory_repositories`：项目记忆和项目 Wiki 共享。
- `project_wiki_pages`、Wiki change/review/token 表：Wiki、项目管理、MCP 共享。
- `member_wiki_experiences`、`member_wiki_experience_versions`、`member_wiki_experience_sources`、`member_wiki_runs`、`member_wiki_processed_sessions`：成员 Wiki 和 worker 使用。
- `meeting_summaries`：会议页面、项目目录清理、项目记忆和 AI 用量使用。

### AI 用量/工作日/Gateway

- `ai_chat_sessions`、`ai_chat_messages`：AI Chat、日报、成员 Wiki 和用量读取。
- `ai_daily_work_logs`：日报 worker 和前端用量/工作日志页面使用。
- `ai_gateway_keys`、`ai_gateway_key_allowances`、当前未跟踪迁移新增的 `llm_*` 表：Personal Gateway 候选使用。
- `otel_traces`、ClickHouse `otel_*`：工作日、Trace、用量和成本查询使用。

## 直接/间接/运行时/部署耦合

### 直接代码依赖

- `agentops_local` 路由大量直接 import `agentops.auth`、`agentops.common.orm`、`agentops.rag.authz` 和 `agentops.rag.audit`。
- `project_memory` 直接使用 RAG ingest/parser/storage。
- `project_wiki` 直接使用 RAG search 和 project memory ingest。
- `member_wiki` 直接使用 project Wiki domain 和 RAG client。
- `wiki_mcp` 直接使用 project Wiki、member Wiki、meeting summaries 和 RAG authz。

### 数据库耦合

- 多领域直接执行 SQL，而不是通过领域仓储接口。
- `projects.py` 会读取/更新文档、材料 intake、项目记忆草稿、项目 Wiki 页面和会议摘要状态。
- `ai_usage`、日报 worker、成员 Wiki worker 直接读取 AI Chat 表。
- Gateway 候选同时读取旧 `ai_gateway_*` 表和新的 `llm_*` 表。

### 权限耦合

- 路由普遍共享 `AuthenticatedRoute`、`current_user_id`、`require_member`、`require_admin`、`is_system_admin`。
- RAG 授权模块同时被知识、Wiki、项目、工作日、AI Chat 和 Gateway 使用。
- 成员 Wiki 还直接查询 `user_orgs`、`projects`、`project_members` 和 `auth.users`。

### 运行时耦合

- worker 与 API 使用相同 Python 包、配置和数据库连接方式。
- RAG 依赖 embedding/reranker 服务可用性。
- AI 用量依赖 ClickHouse 和 OTEL 数据到达时序。
- Gateway 依赖外部模型/Gateway、Key 状态和用量口径一致。

### 部署耦合

- Compose 中 API、多个 worker、Wiki MCP 和 RAG 服务共享镜像、网络和环境变量。
- 部署脚本同时管理数据库、Redis、nginx、隧道和宿主路径。
- 旧 AgentOps Dashboard、SmartBrain Dashboard 和 API 的发布资产仍位于同一仓库。

## 无法独立测试的区域

- 数据库迁移测试依赖完整 Supabase 迁移序列。
- 工作日和 Trace 测试依赖 ClickHouse schema/客户端。
- Jockey worker 测试依赖 Redis 行为。
- RAG 集成测试依赖 embedding/reranker 或替身服务。
- 前端 API 测试依赖单体 `lib/api.ts` 类型和路径。
- Gateway 候选测试依赖未提交迁移和候选实现，不能作为稳定接口证明。
