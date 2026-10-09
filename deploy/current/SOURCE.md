# 当前源码与运行快照

核对时间：2026-10-09 13:30–13:45（Asia/Shanghai）。基线 official/main `431022ba5fe5169aa6be97a5e602f5995692ab91`。

本分支保存已发布的对话摘要、Company Memory 更新器、无适配器归属、AI 工作台滚动及个人代理并发修复，以及七组实际后端 Python 模块快照。不同服务的历史版本不同，不能只用一个 `agentops_local` 目录代表全部线上组件。

`runtime-source-manifest.json` 记录每个组件的 Image ID 和实际源码 SHA256。`runtime-sources/` 保留原始字节，不包含 Env、业务数据、模型响应或私有配置。worklog-worker 包含实际 bind mount 的两份修复源码；其他 workers 快照来自 material parser，同镜像仍须按服务核对挂载。

源码开发在 `agentops_local/`、`smartbrain-dashboard/`、`plugins/company-memory/`、`supabase/migrations/` 中进行。当前线上复现以镜像和实际运行快照为准；历史 overlay Dockerfile 保留用于溯源，不能直接重放旧发布脚本。

部署入口在后继分支 `codex/reproducible-deployment-20261009` 的 `docs/deployment/AI-DEPLOY.md`。当前源码分支不声称包含完整私有镜像、Secrets 或生产数据。原始 C/E 工作树保留，本分支只整理确定路径；生产改动为零。
