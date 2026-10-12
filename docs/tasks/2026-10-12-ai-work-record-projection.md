# AI 工作记录投影修复任务接续记录

## 任务身份与范围

- 任务编号：ai-work-record-projection-20261012
- 负责人／集成负责人：Codex
- 创建／更新时间：2026-10-12 16:00 +08:00
- 开发阶段：候选验证完成，进入提交、推送和受控生产发布
- 部署范围：生产主 API 单容器受控替换；前端、edge、数据库和个人代理不变
- 目标及可观察的验收标准：AI 工作记录只显示用户真实输入和最后一条可见 AI 总结；Codex transcript、工具调用、审批请求、重试原因、计划动作和环境上下文不展示；完整原始对话继续写入项目对话记录/Wiki。
- 本轮授权范围、来源、期限：用户要求“只抓取我输入的提示词和输入信息，以及 AI 完成任务后的最终总结；完整对话记录储存到知识库对应项目的对话记录类型”。用户已于 2026-10-12 明确授权提交、推送和生产部署；按当前发布门禁执行。
- 前置依赖／相关任务：项目对话记录保存链路、AI 使用记录查询路由。

## 代码与版本

- 权威源码目录：C:\Users\test\.codex\worktrees\deb4\智慧大脑agent - 服务器端
- 工作目录／分支／基线提交：codex/project-memory-no-adapter；基线 9f497dc975a79fd1849ba05817e64bf236fcbc5d
- 本任务变更文件：
  - agentops_local/ai_usage/work_record_projection.py
  - agentops_local/api/routes/v4/ai_usage.py
  - agentops_local/tests/test_ai_work_record_projection.py
- 本任务未提交修改及保存方式：保留在上述工作树；证据在 .artifacts/ai-work-record-projection-20261012/。
- 既有其他任务修改：工作树原有修改保持；未整体提交 dirty 工作树。
- Git 提交、审查与推送状态：未提交、未推送。
- 关联发布记录／最近生产核对时间：无；生产未改、未重启、未迁移、未删除历史。

## 根因与设计

`agentops_local/api/routes/v4/ai_usage.py::_attach_messages()` 原先把 `public.ai_chat_messages` 中的 user/assistant 全量消息直接返回工作记录接口，前端因此看到 Codex 运行时信封和中间过程。修复新增独立投影模块，仅在工作记录读侧筛选：保留所有清理后的 user 消息，保留最后一条清理后的可见 assistant 消息，过滤明确的 transcript/approval/runtime 内容。

`agentops_local/api/routes/v4/ai_gateway.py::_materialize_project_conversation_record()` 未接入该投影，仍把 `event.messages` 原样写入 `project_conversation_records` 和 `conversation_record` Wiki 页面。因此工作记录展示与知识库完整存储是双投影，历史数据不回改、不删除。

## 已完成与未完成

| 项目 | 状态 | 证据或说明 |
|---|---|---|
| 工作记录投影实现 | 完成 | `work_record_projection.py`；只改变 AI 使用记录读侧 |
| 用户输入/最终总结筛选 | 完成 | 8 个投影回归用例通过 |
| 误删边界收紧 | 完成 | 普通 JSON、含 `tool_call` 文本、以 `tool`/`retry reason`/`planned action` 开头的业务文本均保留 |
| 路由 `_attach_messages()` 集成 | 完成 | 隔离导入实际路由的 8 个测试通过 |
| 知识库写侧未串线 | 静态核对完成 | `_materialize_project_conversation_record()` 仍使用原始 `event.messages`；未调用投影函数 |
| 隔离 PG 完整双写验收 | 未执行 | `SB_MEMORY_TEST_DSN` 未配置；相关测试 14 项 skipped，不能视为通过 |
| 真实登录工作记录接口验收 | 未执行 | 本轮未部署，未使用员工会话或生产正文 |
| 提交、推送、生产部署 | 未执行 | 等待用户明确授权 |

## 验证记录

| 时间 | 代码版本或 hash | 环境与命令 | 退出码和结果 | 证据位置 | 验证范围与限制 |
|---|---|---|---|---|---|
| 2026-10-12 15:59 | 工作树候选 | backend-venv `pytest agentops_local/tests/test_ai_work_record_projection.py -q` | 0，8 passed | `.artifacts/ai-work-record-projection-20261012/projection-tests.log` | 投影纯函数与边界 |
| 2026-10-12 15:59 | 工作树候选 + 隔离运行时 | `run_route_tests.py` 加载候选路由，外部 ClickHouse/认证边界为最小桩 | 0，8 passed，1 pytest warning | `.artifacts/ai-work-record-projection-20261012/route-tests.log` | 验证 `_attach_messages()`，未连接生产服务 |
| 2026-10-12 15:59 | 工作树候选 | `pytest agentops_local/tests/test_project_conversation_pg.py -q` | 14 skipped | `.artifacts/ai-work-record-projection-20261012/project-memory-tests.log` | 未配置 `SB_MEMORY_TEST_DSN`，PG/Wiki 实写未验收 |
| 2026-10-12 15:59 | 工作树候选 | `py_compile` 三个 Python 文件；`git diff --check` | 0 | `.artifacts/ai-work-record-projection-20261012/pycompile.log`、`diff-check.log` | 语法和空白检查 |

## 运行中的任务

状态：未核对生产运行任务；本轮没有启动服务、迁移、模型调用或长任务。

## 不可重跑的动作

无。本轮未执行生产写入、Key 操作、备份、迁移、模型请求或服务重启。

## 下一步

1. 如需完整验收，提供隔离 `SB_MEMORY_TEST_DSN`，运行项目对话记录 PG/Wiki 测试并核对原始完整消息仍保存。
2. 用户明确授权后，才创建提交、推送和生产发布记录；发布前需补真实登录工作记录端到端验证。
3. 生产发布后只读核对工作记录接口返回形状，并确认项目对话记录仍含完整原始消息；不回改历史记录。

- 生产镜像构建入口：deploy/ai-work-record-projection-20261012/Dockerfile.api-overlay，同时复制路由与新增投影模块。
