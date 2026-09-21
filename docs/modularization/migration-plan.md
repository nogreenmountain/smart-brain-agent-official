# 本地迁移计划（可回滚）

本计划只描述未来如何在当前 monorepo 内治理边界。尚未开始代码移动。

## 批次 0：冻结和基线

- 目标：区分用户已有修改和模块化变更。
- 操作：记录 HEAD、工作区清单、未提交 Key/Gateway 候选；创建模块化专用分支前先得到确认。
- 验证：`git status`、文件 hash、无敏感内容扫描。
- 回滚：删除模块化分支，不触碰 `main` 和用户已有修改。

## 批次 1：部署契约

- 目标：加入 profile、manifest、preflight 和 runbook，不移动业务代码。
- 操作：只新增模板和文档；不覆盖现有 Compose。
- 验证：YAML/Markdown 静态检查、profile 引用完整性、敏感字段检查。
- 回滚：删除本批次新增文件。

## 批次 2：共享接口边界

- 目标：建立 platform-core、shared-types、content-kernel 的接口，不复制实现。
- 前置：用户确认迁移分支和目标目录；确认不纳入未提交 Gateway 候选。
- 验证：单元测试、类型检查、API contract 测试。
- 回滚：恢复 import 兼容层，保留原路径。

## 批次 3：前端 API client 分域

- 目标：把单体 `smartbrain-dashboard/lib/api.ts` 拆为逻辑 client，但保持旧导出兼容。
- 前置：API 路径矩阵和类型归属评审通过。
- 验证：Vitest、TypeScript noEmit、Next build、页面 smoke test。
- 回滚：保留旧 `api.ts` facade，撤销新 client 引用。

## 批次 4：后端领域目录治理

- 目标：按领域整理 route/service/query，不改变 URL 和数据库表。
- 前置：数据库表归属和权限 port 评审通过。
- 验证：pytest、import smoke、API contract、权限回归。
- 回滚：使用兼容 import facade 恢复原路径。

## 批次 5：worker 和基础设施 profile

- 目标：为 worker、RAG、OTEL 和部署建立独立入口与 profile。
- 前置：服务 health contract、manifest 和备份/恢复脚本通过审查。
- 验证：本地隔离 Docker 环境、doctor、backup/restore dry-run。
- 回滚：停用新 profile，恢复旧 Compose 文件；不得使用 `git reset --hard`。

## 批次 6：候选独立仓库评估

- 目标：只评估 employee-agent、observability、infra 是否满足分仓门槛。
- 前置：至少一个版本周期接口稳定、独立 CI 和回滚通过。
- 验证：生成文件归属表、历史保留方案和独立构建报告。
- 回滚：不创建仓库，继续留在 monorepo。

## 严禁操作

- `git reset --hard`；
- `git clean -fd`；
- 强制推送；
- 未确认的数据库迁移；
- 未确认的 Docker/systemd/nginx 变更；
- 读取或提交真实密钥、Cookie、dump、用户正文和模型响应。
