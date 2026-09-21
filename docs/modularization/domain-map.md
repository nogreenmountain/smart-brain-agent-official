# SmartBrain 领域地图

## 分析范围

本文件基于当前工作区 `main` 分支 `8280adda3846af082a386a2c3fd20da8c01dca4a` 的静态扫描生成。分析包含 `api/`、`agentops_local/`、`smartbrain-dashboard/`、`dashboard/`、迁移、worker、部署和 OTEL/RAG 目录；不读取或输出运行时密钥、Cookie、数据库内容或真实模型正文。

当前仓库不是纯 SmartBrain 仓库，而是 AgentOps 基础产品、SmartBrain 覆盖层、部署资产和员工端工具的混合单仓库。

## 领域分层

### 应用层

| 领域 | 前端入口 | API 入口 | 当前状态 |
|---|---|---|---|
| 应用壳层与登录 | `smartbrain-dashboard/app/layout.tsx`、`app/login` | `auth_me.py`、基础 AgentOps auth | 共享认证和 API client |
| 项目与成员 | `projects`、`team`、`members` | `projects.py`、`team_members.py` | 强依赖组织、RLS 和公共项目表 |
| 知识、上传与 RAG | `knowledge`、`uploads` | `knowledge.py`、`project_materials.py` | 依赖对象存储、RAG、项目权限 |
| 项目记忆 | `project-memory` | `project_memory.py` | 与内容、Wiki、会议记录交叉依赖 |
| 项目 Wiki | `wiki` | `project_wiki.py`、Wiki MCP | 依赖项目记忆、RAG、审核和 worker |
| 成员 Wiki | `member-wiki` | `member_wiki.py` | 依赖成员、聊天记录、RAG 和定时 worker |
| 会议记录 | `meeting-notes` | `meeting_summaries.py` | 依赖项目、成员、文件解析和 AI 用量 |
| 工作记录 | `workday`、`worklogs` | `workday.py` | 依赖员工身份、OTEL/ClickHouse 和用量 |
| AI 用量 | `leaderboard`、AI workspace | `ai_usage.py` | 跨 PostgreSQL、ClickHouse、Redis 和模型 |
| AI Monitor | `monitor/setup`、AI workspace | `ai_monitor.py` | 与员工端、工作日和共享会话耦合 |
| Personal Key/Gateway | `profile`、AI workspace | `ai_gateway.py` | 当前包含未提交候选实现，不能视为稳定模块 |
| 管理后台 | `admin`、`members`、`team` | `audit_admin.py`、成员/项目路由 | 权限边界集中但实现分散 |

### 领域服务层

- `agentops_local/auth`：身份、会话、认证中间件。
- `agentops_local/rag`：解析、分块、embedding、混合检索、回答和 RAG 授权。
- `agentops_local/project_memory`：材料解析、记忆摄取、草稿、发布和存储键。
- `agentops_local/project_wiki`：候选生成、编译、审核、MCP token 和 worker。
- `agentops_local/member_wiki`：成员经验编译、查询、处理会话和 worker。
- `agentops_local/meeting_summaries`：会议摘要领域模型和查询。
- `agentops_local/workday`：员工身份、工作日聚合、展示模型和 ClickHouse 查询。
- `agentops_local/ai_usage`：访问控制、用量查询、日报、报告和 Gateway/Key 候选代码。
- `api/agentops`：AgentOps 原生认证、Trace、Metrics、OpsBoard、计费和 API 版本。

### 基础设施层

- PostgreSQL/Supabase：用户、组织、项目、内容、Wiki、会议、工作日、用量和 Key 状态。
- ClickHouse/OTEL：Trace、span、工作记录和部分 AI 用量来源。
- Redis：Jockey 队列、缓存、限流及候选网关缓存。
- 对象存储/本地卷：项目材料、会议文件和下载资产。
- RAG 服务：embedding 与 reranker 容器。
- 部署：Docker Compose、nginx、公网中继、systemd/脚本和备份服务。
- 员工端：`employee_telemetry`、`employee-deploy` 和 Windows 安装包。

## 建议的第一阶段模块边界

建议先在同一仓库中建立以下逻辑模块，不立即拆成独立网络服务：

1. `platform-core`：认证、身份、组织、权限、审计和共享配置。
2. `project-management`：项目、部门、成员关系和项目生命周期。
3. `content-rag`：材料、文件、文档、解析、向量和检索。
4. `project-memory`：项目记忆草稿、审核、发布和仓库元数据。
5. `wiki`：项目 Wiki、成员 Wiki、MCP 和编译 worker。
6. `work-records`：会议、工作日、工作日志和员工身份映射。
7. `ai-usage`：用量、日报、排行榜、报告和成本口径。
8. `personal-gateway`：Personal Key、Gateway 运行时和操作状态机；需先冻结当前未提交候选。
9. `observability`：AgentOps Trace、OTEL、ClickHouse 查询和成本处理。
10. `employee-agent`：Monitor、采集器、安装包和客户端协议。
11. `runtime-infra`：Compose、nginx、部署、备份、Jockey 和发布脚本。
12. `legacy-agentops`：原始 `api/`、`dashboard/`、`landing/`，作为兼容边界，不与 SmartBrain 直接混拆。

## 边界结论

- 认证、组织、项目和权限是平台核心，不应先独立拆仓。
- RAG 是技术模块，但其授权、项目和内容数据仍属于平台边界。
- Wiki、项目记忆、会议和材料目前不能分别独立部署，因为存在直接代码和表依赖。
- AI 用量和 Personal Gateway 暂不具备独立发布条件；需要先稳定身份、计量、Key 状态机和接口契约。
- 员工端可以比业务后端更早独立版本化，但必须先固定 Monitor API 和身份协议。
- 部署与备份适合先拆成 `infra/` 逻辑目录，暂不创建独立 GitHub 仓库。
