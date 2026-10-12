# AI 工作记录投影修复方案

核对时间：2026-10-12 16:00（Asia/Shanghai）

## 目标

将 AI 工作记录改为“用户输入 + 最终 AI 总结”的紧凑视图，同时保留项目知识库中的完整对话记录，避免中间工具和 Codex 运行时内容污染业务界面。

## 根因

工作记录查询路由 `_attach_messages()` 直接读取 `public.ai_chat_messages` 的 user/assistant 全量消息；其中包含 transcript、审批、工具返回和中间进度。前端只是渲染路由返回的 `messages`，所以问题应在后端读侧投影解决。项目对话记录写侧由 `_materialize_project_conversation_record()` 独立负责，原本已保存完整 `event.messages`。

## 设计

- 新增 `agentops_local/ai_usage/work_record_projection.py`，集中处理工作记录投影。
- 保留全部 user 消息，清理环境上下文和明确的 Codex 信封。
- 只保留最后一条可见 assistant 消息作为任务总结。
- 仅在检测到 transcript/approval 信封时清理 runtime-like 行，普通业务 JSON、`tool_call` 字段和以 `tool`、`retry reason`、`planned action` 开头的文本保持原样。
- `_attach_messages()` 继续查询原始数据库消息，只在返回响应前调用投影。
- 不在 `_materialize_project_conversation_record()` 中调用投影；数据库 `project_conversation_records.messages` 与 conversation_record Wiki 继续使用原始完整 `event.messages`。
- 不修改表结构、不迁移、不清理存量、不删除历史。

## 分阶段实施与验证

1. 纯函数红绿测试：用户多条提示、只留最后总结、信封清理、审批 JSON 丢弃、普通 JSON 和关键词文本保留。
2. 路由级验证：用隔离运行时映射候选 `agentops` 包，对未使用的 ClickHouse/认证依赖做最小桩，执行 `_attach_messages()` 现有测试。
3. 知识库边界核对：静态确认写侧仍传入原始 `event.messages`；若配置隔离 PG，再执行完整项目对话记录测试。
4. 发布前：补真实工作台登录会话的接口验收，确认工作记录只返回用户输入和最终总结，知识库对话记录仍完整。

## 风险与限制

- 未配置 `SB_MEMORY_TEST_DSN`，本轮无法证明真实 PG/Wiki 写入结果；已如实记录 14 项 skipped。
- 当前没有提交、推送或生产发布，因此不能宣称线上已修复。
- 过滤规则只移除明确运行时信封，避免过度清理正常业务文本；若未来新增 Codex 信封格式，应先补测试再扩展。
- 真实员工正文和凭据不进入普通 Markdown 或证据。
