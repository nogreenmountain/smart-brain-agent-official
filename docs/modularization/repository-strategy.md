# 仓库拆分方案比较

## 方案 A：先治理单一 monorepo（推荐）

建议目录目标：

```text
apps/
  web-smartbrain/
  web-agentops/
  api/
  worker/
packages/
  platform-core/
  api-client/
  shared-types/
  content-kernel/
domains/
  project-management/
  content-rag/
  project-memory/
  wiki/
  work-records/
  ai-usage/
  personal-gateway/
infra/
employee-agent/
docs/
```

优点：

- 保留原子提交和跨模块调试能力；
- 数据库迁移、共享类型和 API 契约仍可同步审查；
- 适合当前 Git 协同经验和现有强耦合；
- 可以先用 CODEOWNERS、目录权限和 CI job 建立负责人边界；
- 回滚只需回滚一个经过审查的提交或 PR。

缺点：

- 仓库仍较大；
- 权限隔离不如独立仓库；
- CI 需要按路径拆分，否则反馈慢；
- 旧 AgentOps 与 SmartBrain 的边界需要持续治理。

## 方案 B：前端、后端、基础设施分仓

建议仓库：

- `smartbrain-web`
- `smartbrain-api`
- `smartbrain-infra`
- `smartbrain-docs`

优点：

- 组织结构直观；
- 前端、后端、部署可以分别设置负责人和发布节奏；
- 比按领域拆仓少很多仓库。

缺点：

- 当前前端和后端共享类型、认证和 API client，版本协调成本高；
- 数据库迁移仍横跨后端和 infra；
- Wiki、RAG、用量和 Gateway 仍会在后端内部循环；
- 跨仓库回滚和联调更复杂；
- 不能解决 SmartBrain 与 AgentOps 的内部耦合。

## 方案 C：按业务领域多仓库

可能仓库：

- `smartbrain-platform-core`
- `smartbrain-projects`
- `smartbrain-content-rag`
- `smartbrain-project-memory`
- `smartbrain-wiki`
- `smartbrain-work-records`
- `smartbrain-ai-usage`
- `smartbrain-personal-gateway`
- `smartbrain-observability`
- `smartbrain-employee-agent`
- `smartbrain-infra`
- `smartbrain-shared`

优点：

- 领域负责人和权限隔离最清晰；
- 未来可独立发布和扩容；
- 可针对高风险模块单独做安全审查。

缺点：

- 当前代码还没有稳定领域接口；
- 数据库迁移和 RLS 归属会非常复杂；
- 需要大量版本、包发布和兼容策略；
- 需要更多 CI、仓库权限、Secrets 和发布流水线；
- 当前团队容易把“复制代码”误当作拆分；
- 跨模块故障回滚和本地调试最困难。

## 对比矩阵

| 维度 | A：monorepo | B：前后端/infra | C：按领域多仓 |
|---|---|---|---|
| 开发复杂度 | 低到中 | 中 | 高 |
| Git 协同难度 | 低 | 中 | 高 |
| 发布难度 | 低，可按路径发布 | 中 | 高 |
| 版本管理 | 单提交原子 | 跨仓版本 | 多包多仓版本 |
| CI/CD 数量 | 少，可路径过滤 | 中 | 多 |
| 权限隔离 | 目录/CODEOWNERS | 仓库级 | 最强 |
| 数据库迁移 | 最容易统一审查 | 仍有跨仓协调 | 最复杂 |
| 本地开发 | 最好 | 中 | 最差 |
| 跨模块调试 | 最容易 | 中 | 最难 |
| 共享类型 | 本地共享 | 包发布/同步 | 版本化包 |
| 回滚 | 最简单 | 需协调多个仓库 | 最难 |
| 当前团队适配度 | 最高 | 中 | 低 |
| 未来扩展 | 足够 | 较好 | 最强但成本高 |
| 失败恢复 | 单仓可恢复 | 跨仓协调 | 多仓恢复 |

## 推荐结论

推荐采用 **方案 A：先在 monorepo 内完成模块边界治理**，然后只把满足以下条件的模块逐步拆出：

1. 不再直接读取其他领域内部表；
2. 公开 API/事件/共享类型已稳定至少一个版本周期；
3. 可以独立运行单元测试和集成测试；
4. 有独立 README、OWNERS、CODEOWNERS、CHANGELOG 和回滚步骤；
5. 数据库迁移归属清晰；
6. 不需要复制认证、权限和敏感数据处理；
7. 有独立 CI 和发布责任人。

最可能首先独立仓库化的候选是 `employee-agent`、`observability` 或部分 `runtime-infra`，而不是项目 Wiki、AI 用量或 Personal Gateway。

## 本阶段明确不做

- 不创建 GitHub 仓库；
- 不添加 remote；
- 不创建或推送分支；
- 不使用 `git subtree` 或 `git filter-repo`；
- 不移动代码；
- 不执行数据库迁移；
- 不修改部署和生产环境。
