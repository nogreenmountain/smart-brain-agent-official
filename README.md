# Smart Brain Agent 当前部署版本

把本分支交给 AI，从 [AI 部署入口](docs/deployment/AI-DEPLOY.md) 开始。它列出前置条件、受控输入、配置、数据恢复、启动顺序、验收和失败处理。

| 分支 | 用途 |
|---|---|
| [codex/current-source-20261009](https://github.com/nogreenmountain/smart-brain-agent-official/tree/codex/current-source-20261009) | 当前修复源码、测试和七组实际运行模块 |
| [codex/reproducible-deployment-20261009](https://github.com/nogreenmountain/smart-brain-agent-official/tree/codex/reproducible-deployment-20261009) | 在源码分支上增加固定镜像部署、检查工具和AI操作步骤 |

`deploy/current/release-lock.json`固定30业务服务的21镜像；实际源码1425文件逐个SHA核对。原项目原样复现需要受控镜像、私有配置和数据恢复输入；源码build与fresh空环境另列，不能冒充原生产恢复。

当前已取消适配器、项目Key绑定和Monitor采集；Langfuse及reconcile timer不启动。旧部署文件保留历史，但当前只使用deploy/current入口。

[当前状态](docs/CURRENT.md) · [交付验收与限制](docs/releases/reproducible-repository-20261009.md) · [源码构建](docs/deployment/SOURCE-BUILD.md)

本轮保存源码/部署分支和受控镜像配置包，没有部署到新主机或重启生产。Git不包含真实Env、数据库数据、员工正文或OAuth登录态。
