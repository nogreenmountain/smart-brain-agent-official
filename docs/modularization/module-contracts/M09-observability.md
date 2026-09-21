# M09 — observability

## 业务职责

接收和查询 Trace、span、logs，维护 ClickHouse schema 和可观测性成本字段。

## 不负责

不负责业务权限主数据、项目 Wiki、Key 生命周期或员工业务规则。

## 当前实现

- `api/agentops/api/routes/v4/traces`
- `api/agentops/api/routes/v4/metrics`
- `opentelemetry-collector/`
- `clickhouse/`

## 数据与接口

- 数据：ClickHouse `otel_*`、基础 AgentOps `sessions/agents/llms/tools/actions`。
- 输入：受信任的项目/API key/身份字段和 OTLP records。
- 输出：Trace、metrics、logs、cost usage 查询。
- 公共接口：OTLP contract、Trace Query API、Usage Event schema。
- 内部接口：Collector pipeline、ClickHouse SQL 和 retention 配置。

## 拆分条件

固定身份字段、脱敏规则、schema 版本和 retention 后可独立版本化；仍需与 M07/M06 通过契约集成。
