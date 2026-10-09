# 当前部署入口

先读 [AI-DEPLOY](../../docs/deployment/AI-DEPLOY.md)。Python工具只依赖标准库。

| 文件 | 用途 |
|---|---|
| compose.yaml | JSON格式的合法Compose YAML；30服务，固定Image ID，无自动pull/build |
| release-lock.json | 现场镜像、平台、required Env、目录和资源门槛 |
| .env.example、env-examples | 主机参数和逐服务私有Env模板；复制到checkout外 |
| verify.py | 源码、镜像、受控包、前置条件与匿名HTTP契约检查 |
| images.py | 固定镜像导入/导出与Docker29 OCI身份校验 |
| postgres、clickhouse | 只读结构快照/角色脚本/验收SQL；不含业务数据 |
| runtime-sources | 七组运行Python源码及hash；按组件溯源 |
| nginx、systemd | 当前路由、外部HTTPS与新主机生命周期模板 |
| controlled-artifacts.json | 私有交付包安全摘要，无Secrets |

默认不启用workers、RAG、relay profile；完整当前业务部署按runbook显式启用。退休的Monitor、适配器、项目Key绑定、Langfuse和reconcile timer不在启动拓扑。Monitor removal服务只是既有静态卸载入口。

禁止把旧deploy目录、历史Dockerfile或CURRENT历史页当成当前一键脚本。
