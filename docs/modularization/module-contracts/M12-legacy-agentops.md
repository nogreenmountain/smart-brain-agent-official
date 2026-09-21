# M12 — legacy-agentops

## 业务职责

保留原始 AgentOps API、Dashboard、Landing、Trace/OpsBoard/计费兼容能力，直到产品方确认退休或迁移完成。

## 不负责

不负责新增 SmartBrain 领域实现，不接收未评审的本地覆盖层代码。

## 当前实现

- `api/`
- `dashboard/`
- `landing/`
- 原始 AgentOps migrations 和测试。

## 数据与接口

- 数据：原生 projects、sessions、agents、threads、stats、actions、llms、tools、errors、billing 等。
- 公共接口：现有 API v1/v2/v3/v4、OpsBoard、Trace 和计费兼容接口。
- 内部接口：原 AgentOps ORM、Supabase client、ClickHouse client。

## 拆分风险

SmartBrain 当前通过 `agentops` 包直接引用该模块内部实现。必须先建立兼容 facade，不能直接把 `api/` 复制到新仓库。
