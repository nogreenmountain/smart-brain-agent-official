# 循环依赖与边界泄漏

## 结论

静态 Python import 扫描没有发现一个需要立即阻断启动的完整业务包级循环；发现了路由包自身通过 `v4/__init__.py` 注册路由的自引用，以及多个逻辑/延迟导入循环。后者会阻止直接按领域拆仓。

## 已确认的逻辑循环

### 项目记忆 ↔ 项目 Wiki

```text
project_memory route/service
  -> project_wiki.service
  -> project_memory.ingest
```

表现：项目记忆发布流程调用 Wiki service，而 Wiki service 又调用项目记忆摄取。当前部分导入位于函数内部，降低了 import-time 失败概率，但没有消除领域循环。

影响：项目记忆和项目 Wiki 不能分别复制到两个仓库而不先定义发布接口或领域事件。

建议：将“记忆候选发布”抽象为单向 application port；Wiki 只消费候选/审核事件，不直接回调项目记忆内部实现。

### 项目记忆/材料 ↔ RAG

```text
project_memory.ingest
  -> rag.ingest
  -> project_memory.parsers

rag.parsers
  -> project_memory.parsers
```

影响：材料格式、文本抽取和分块逻辑同时被记忆和 RAG 使用。直接拆分会导致重复实现或反向依赖。

建议：把文件解析和格式协议下沉为独立 `content-kernel`，RAG 只接收标准化文档块，项目记忆只调用内容接口。

### Wiki ↔ 成员 Wiki/会议/MCP

```text
wiki_mcp.operations
  -> project_wiki.query/service
  -> member_wiki.query/access
  -> meeting_summaries.query
  -> rag.authz/model_clients
```

影响：Wiki MCP 不是纯适配器，它直接知道多个业务领域和权限实现，不能先独立拆成通用 MCP 仓库。

建议：先定义稳定的 `WikiReadPort`、`MemberKnowledgePort` 和 `MeetingSourcePort`，MCP 只依赖接口。

### 成员 Wiki ↔ 项目 Wiki domain

`member_wiki.domain` 和 `member_wiki.compiler` 直接引用 `project_wiki.domain` 的清洗/模型能力。

影响：两个 Wiki 领域共享内部 domain 实现，拆分时会形成复制代码或反向依赖。

建议：将文本清洗、来源引用、候选状态等真正通用能力移入 `content-kernel` 或 `shared-domain`。

## 路由注册自引用

`agentops_local/api/routes/v4/__init__.py` 负责导入并注册全部 `/v4` 路由，同时保留原 AgentOps v4 路由。静态扫描会看到 `v4` 包自身的聚合引用。

这不是业务循环，但说明路由注册层承担了过多职责：

- SmartBrain 路由注册；
- AgentOps 原生路由注册；
- 认证 route class 绑定；
- Stripe webhook 兼容入口。

建议后续拆成 `legacy_router`、`smartbrain_router` 和 `platform_router` 三层，再保持同一 HTTP app 的兼容挂载。

## 共享基础设施导致的隐性循环

以下不一定表现为 Python import 循环，但属于拆仓时必须处理的闭环：

- AI 用量依赖 AI Chat/Trace 数据；日报和成员 Wiki 又反过来消费 AI Chat 数据。
- Gateway 依赖用量和认证；用量记录又需要识别 Gateway 请求身份。
- Workday 依赖员工 Monitor/OTEL；Monitor 状态和共享会话又通过 AI 用量接口暴露。
- 项目管理清理逻辑直接修改材料、记忆、Wiki 和会议状态。
- 部署脚本同时决定 API、worker、RAG、数据库和 Redis 的运行拓扑。

## 当前没有证据支持的循环

以下内容本轮没有通过源码静态扫描确认，不能直接当成已发现循环：

- 前端组件之间的运行时状态循环；
- 数据库触发器形成的完整跨域循环；
- Redis 队列任务之间的消息闭环；
- 生产环境 nginx/systemd 的服务循环。

这些项目应在后续只读阶段通过迁移触发器扫描、Compose 拓扑和测试夹具进一步确认。

## 拆分前必须先消除的循环

1. 项目记忆与项目 Wiki 的双向调用；
2. RAG 与内容解析的反向依赖；
3. 成员 Wiki 对项目 Wiki domain 的内部实现依赖；
4. Wiki MCP 对多个业务领域内部查询实现的直接依赖；
5. Gateway、AI 用量和认证之间的身份/计量闭环；
6. 路由聚合器对旧 AgentOps 和 SmartBrain 的混合注册。
