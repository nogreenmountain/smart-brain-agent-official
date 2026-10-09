# 正式仓库整理与可复现部署

任务reproducible-repository-20261009，负责人Codex，2026-10-09 13:32开发中。用户授权整理nogreenmountain/smart-brain-agent-official并按分支推送，使AI按步骤和前置条件复现当前项目。生产仅只读核对，不部署、迁移、修改Key或重启；本轮推送授权直接来自该请求。

正式远端main基线431022ba5fe5169aa6be97a5e602f5995692ab91。原C盘deb4和E盘脏树保留；新独立managed worktree为C:/Users/test/.codex/worktrees/reproducible-deployment/智慧大脑agent - 服务器端。源码分支codex/current-source-20261009；后继部署分支codex/reproducible-deployment-20261009基于源码分支。只推明确分支，不强推、不改main、不整体提交共享脏树。

阶段：核对运行镜像/源码/实际路由和私有前置条件→逐项保存最新已验证源码与安全来源清单→补齐固定镜像/配置/离线与数据库路径/AI执行入口和验收工具→独立审查、测试和干净checkout验证→提交推送、远端ref核对、更新接续入口。现场结论须记录核对时间，旧发布runner不得重放。

复现分为当前确切镜像+私有配置/数据恢复，以及源码新建空环境；前者需受控镜像与数据交付，业务数据和Secrets不上传公开Git。新建环境不得使用旧seed默认密码、旧Monitor或适配器，Langfuse和reconcile timer保持禁用。生产完整PG恢复尚未通过，不能由仓库整理推导已验收；必须明确所需交付物和未验证边界。

本轮证据保存原C盘.artifacts/reproducible-repository-20261009及独立工作树对应目录。当前没有新生产发布或用户数据导出；运行核对与任务身份将追加到本记录。
