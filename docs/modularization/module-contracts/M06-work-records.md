# M06 — work-records

## 业务职责

提供会议记录、工作日聚合、AI 工作日志和员工身份到业务用户的映射。

## 不负责

不负责员工采集器本身、模型供应商、通用项目权限或 Trace 写入协议。

## 当前实现

- `meeting_summaries/`
- `workday/`
- `meeting_summaries.py`、`workday.py`
- `ai_usage/daily_log*`

## 数据与接口

- 数据：`meeting_summaries`、`ai_daily_work_logs`、ClickHouse `otel_traces`/spans。
- 输入：员工身份、项目 scope、会议文件、Trace 查询。
- 输出：会议摘要、工作日统计、工作日志。
- 公共接口：Workday Query API、Meeting API、Employee Identity port。

## 当前耦合

依赖 M01、M02、M03、M07 和 M09。不能将会议、工作日和员工端同时拆成互不依赖的仓库。

## 拆分前置条件

冻结员工身份格式、Trace 字段、时区/日期口径和隐私规则。
