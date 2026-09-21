# M10 — employee-agent

## 业务职责

采集员工端 AI/工作事件、建立共享设备会话、提供 Windows 安装包和客户端升级载荷。

## 不负责

不负责业务数据库表、项目权限判断、AI 用量结算或模型调用。

## 当前实现

- `employee_telemetry/`
- `employee-deploy/`
- `smartbrain-dashboard/public/downloads/` 中的发布资产。

## 公共接口

- Monitor enrollment/status contract；
- Workday/usage event contract；
- 客户端版本和签名/完整性 contract。

## 敏感数据

处理设备标识、会话元数据和可能的 AI 请求摘要。不得采集或提交真实 Cookie、Key、正文或响应。

## 独立性

可较早独立版本化，但必须先锁定 M06、M07 和 M09 的事件协议；安装包发布需要单独的安全和签名审核。
