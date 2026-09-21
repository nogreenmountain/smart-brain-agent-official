# M08 — personal-gateway

## 业务职责

管理个人 API Key、Gateway credential、操作状态机、配额、模型路由和请求身份绑定。

## 不负责

不负责组织权限主数据、用量最终结算、用户认证实现或基础设施备份。

## 当前实现

- `agentops_local/api/routes/v4/ai_gateway.py`
- `agentops_local/ai_usage/gateway*.py`
- `llm_key_*.py`、`litellm_management.py`
- 个人资料页面和 API client 的未提交候选改动。

## 数据与接口

- 数据：旧 `ai_gateway_*` 表、候选 `llm_*` 表、credential refs、operation records。
- 输入：认证用户、Key 操作、模型请求、provider/gateway 状态。
- 输出：只显示一次的 secret、Key 状态、operation 状态、quota 状态、usage projection。
- 公共接口：Key CRUD、Operation Polling、Gateway Request contract。
- 内部接口：密钥 hash、原生 provider adapter、reconcile worker。

## 敏感数据

处理 API Key、请求正文、工具参数和可能的模型响应。日志和测试不得输出真实 secret 或正文。

## 当前风险

该模块当前处于未提交候选状态，不能与已发布 API 混为稳定接口。必须先完成协议、迁移、身份和失败恢复评审。
