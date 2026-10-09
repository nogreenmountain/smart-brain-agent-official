# Smart Brain Agent 正式版

2026-10-09 当前源码入口：[deploy/current/SOURCE.md](deploy/current/SOURCE.md)。当前已发布修复与不同后端服务的实际源码快照已保存；[本轮验收](docs/releases/repository-source-20261009.md)记录范围。

要按当前项目部署，请使用 [codex/reproducible-deployment-20261009 分支](https://github.com/nogreenmountain/smart-brain-agent-official/tree/codex/reproducible-deployment-20261009) 的 `docs/deployment/AI-DEPLOY.md`。下面原 profile 介绍保留为历史；`employee` Monitor、项目 Key 绑定和适配器已取消，不是当前部署入口。

这是 Smart Brain Agent 的可复用部署基线，目标是在 Ubuntu 或 Windows 电脑上，根据部署需求快速初始化局域网、公网、RAG、员工端或离线环境。

## 本仓库定位

- 当前仓库是从原始 `smart-brain-agent` 的已提交基线和已确认的功能成果整理出的独立正式版快照。
- 原仓库不被删除、不被覆盖，仍作为历史来源和回滚参考。
- 当前工作区中与 Personal API Key / AI Gateway 相关的功能候选已保留，但仍标记为候选实现，不能自动宣称生产可用。
- 本仓库不包含真实 `.env`、API Key、Cookie、数据库密码、数据库 dump、用户正文或真实模型响应。

## 支持的部署场景

- `minimal`：低资源本地验证；
- `lan`：局域网部署；
- `rag`：局域网 + embedding/reranker；
- `public-relay`：公网 HTTPS 中继；
- `employee`：员工 Monitor 试点；
- `air-gapped`：离线镜像导入。

部署 profile 和 AI 执行顺序见：

- `docs/deployment/deployment-profiles.md`
- `docs/deployment/ai-deployment-runbook.md`
- `infra/manifests/release-manifest.example.yaml`

## 当前快照来源

- source commit：`8280adda3846af082a386a2c3fd20da8c01dca4a`
- snapshot type：working-tree overlay on committed baseline
- private operational logs：未复制
- production environment：2026-10-08 已只读核对，未修改；详见状态入口

## 推荐部署原则

1. 先运行 preflight，确认 OS、Docker、内存、磁盘、端口和网络；
2. 明确选择 profile，不根据目录猜测要启动的服务；
3. 真实 Secrets 由用户或安全存储注入，不提交仓库；
4. 先备份，再迁移数据库；
5. 基础服务、API、worker、前端按顺序启动；
6. 通过 health check 和最小 smoke test 后才交付；
7. 失败时恢复上一份 manifest，不使用强制 reset 或破坏性清理。

## 目录导航

- `api/`：AgentOps 基础后端；
- `agentops_local/`：Smart Brain 后端扩展和领域实现；
- `smartbrain-dashboard/`：Smart Brain 前端；
- `dashboard/`：原 AgentOps 前端；
- `supabase/migrations/`：数据库迁移；
- `deploy/`：既有部署和基础设施资源；
- `docs/modularization/`：模块边界、依赖和迁移计划；
- `docs/deployment/`：跨电脑部署规范；
- `infra/manifests/`：版本清单模板。

## 重要限制

当前 snapshot 仍保留历史兼容代码和候选实现。第一次在新电脑部署时应使用 `minimal` 或隔离的 `lan` 环境，不应直接连接生产数据库、不应直接启用公网入口、不应自动启用真实模型或 Personal Gateway。

## 开发和生产状态入口

先读 [当前状态](docs/CURRENT.md)，再读 [2026-10-08 生产快照](docs/ops/server-state-20261008.md)、[本地开发快照](docs/ops/local-workspace-state-20261008.md)及对应任务。记录更新时间与生产核对时间分开。

本次同步保存源码和只读版本清单，没有发布到生产。开发源码和线上镜像存在差异，验证范围和未完成项写在任务记录中。公开根 AGENTS.md 只保存接续规则。
