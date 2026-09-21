# 推荐仓库规划

## 当前阶段：单仓库

当前继续使用一个 canonical monorepo。先通过目录边界、CODEOWNERS、路径 CI 和模块契约治理协作，不创建新的 GitHub 仓库。

## 未来候选仓库

只有满足模块契约和独立发布门槛后，才考虑以下仓库：

| 仓库 | 初始内容 | 不包含 | 优先级 |
|---|---|---|---|
| `smartbrain-employee-agent` | `employee_telemetry`、Monitor 载荷、客户端协议 | 业务数据库、后端权限、真实配置 | 中 |
| `smartbrain-observability` | OTEL builder、ClickHouse schema、Trace contract | SmartBrain 业务 API | 中 |
| `smartbrain-infra` | Compose profile、部署脚本、备份、health/rollback | 业务 Python/前端源码、Secrets | 中 |
| `smartbrain-shared` | 稳定 shared types、content-kernel | 业务领域逻辑、数据库连接 | 低，需接口先稳定 |

## 暂不拆仓

以下继续留在主仓库：

- platform-core；
- project-management；
- content-rag；
- project-memory；
- wiki；
- work-records；
- ai-usage；
- personal-gateway；
- legacy-agentops。

这些模块仍存在数据库、权限、内部 import 或运行时耦合。

## 每个未来仓库的最低要求

- README.md；
- OWNERS.md；
- CODEOWNERS；
- CHANGELOG.md；
- CONTRIBUTING.md；
- `.env.example`；
- `docs/`；
- `tests/`；
- 独立 CI；
- 独立版本号和回滚说明；
- 不含真实 Secrets、数据库 dump、用户正文和运行日志。

## GitHub 操作边界

本阶段不创建仓库、不添加 remote、不推送分支、不创建 Actions、不配置 Secrets、不修改分支保护。未来执行前必须单独展示仓库清单和文件归属，并再次确认。
