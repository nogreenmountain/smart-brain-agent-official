# M07 — ai-usage

## 业务职责

负责 AI 请求归属、Token/成本统计、排行榜、日报、报告和用量隐私边界。

## 不负责

不负责认证、Key 生命周期、模型供应商管理或 Trace Collector 部署。

## 当前实现

- `agentops_local/ai_usage/`
- `ai_usage.py`
- ClickHouse/OTEL 查询和 daily log worker。

## 数据与接口

- 数据：AI Chat tables、`ai_daily_work_logs`、ClickHouse OTEL 数据、候选 Gateway usage。
- 输入：已认证请求身份、provider usage、Trace/Chat records。
- 输出：records、leaderboard、daily logs、report、usage status。
- 公共接口：Usage Query API、Usage Identity contract、Provider Usage Status。
- 内部接口：ClickHouse SQL、日报 prompt、缓存和聚合实现。

## 关键风险

身份、Key、Trace 和 provider usage 必须一致；不能把估算、网关报告和 provider 实报混为一个数。正文、推理和工具参数必须有独立隐私策略。

## 拆分条件

先确定唯一计量事件 schema 和来源优先级，再考虑独立 worker 或仓库。
