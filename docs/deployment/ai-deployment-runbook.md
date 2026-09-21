# AI 部署 Runbook

本 Runbook 用于另一台电脑上的 AI 或人工执行部署。它描述检查顺序，不包含任何真实密钥、Cookie、数据库密码或用户正文。

## 0. 安全边界

- 默认只读检查，不自动修改生产或已有部署。
- 不打印 `.env` 内容、API Key、Access Token、Cookie、数据库密码、私钥和真实模型正文。
- 发现已有容器、数据库或配置时先停止，输出差异和回滚点。
- 数据库迁移、公网入口、systemd、nginx、真实模型调用和密钥写入必须得到明确授权。

## 1. 读取需求

将自然语言需求转换成结构化结果：

```yaml
profile: lan
features:
  wiki: true
  rag: false
  ai_gateway: false
network: private
data_policy: preserve
upgrade_existing: false
```

如果 profile、网络范围或数据保留策略不明确，先询问，不猜测。

## 2. Preflight

只读检查：

1. OS、架构和用户权限；
2. Docker/Compose 版本；
3. CPU、内存、磁盘；
4. GPU/驱动（需要 RAG 时）；
5. 端口占用；
6. 旧 SmartBrain/AgentOps 容器；
7. 旧 manifest 和数据库 schema 版本；
8. 网络/DNS/TLS 条件；
9. 镜像 digest 或离线镜像包；
10. 备份目录和可回滚版本。

Preflight 未通过时，不启动服务、不执行迁移。

## 3. 配置

只从 `.env.example` 和 profile 模板生成变量名。真实值由用户、安全存储或受控环境注入。

配置生成后只显示：

- 变量名；
- 是否已设置；
- 是否为必填；
- 是否需要重新启动。

不显示变量值。

## 4. 部署顺序

1. 保存当前 manifest、Compose 和配置的 hash；
2. 创建或确认备份；
3. 校验镜像和 release manifest；
4. 启动 PostgreSQL/Redis 等基础服务；
5. 执行经过批准的数据库迁移；
6. 启动 API；
7. 启动 worker；
8. 启动前端；
9. 启动可选 RAG、OTEL、nginx 或 relay；
10. 执行 health check；
11. 执行最小业务 smoke test；
12. 生成部署报告。

## 5. 验证

最小验证不得使用真实用户正文或真实模型费用：

- API `/health`；
- Web 首页和登录壳层；
- 数据库连接；
- Redis PING；
- ClickHouse 连接（已启用时）；
- RAG 健康检查（已启用时）；
- Wiki 只读接口（已启用时）；
- 权限边界和匿名请求拒绝；
- 版本/manifest 一致性。

## 6. 失败处理

- 配置失败：保留生成文件的权限，删除临时文件，不触碰已有服务。
- 镜像失败：停止本次启动，保留旧版本。
- 迁移失败：停止后续服务，按迁移回滚说明处理，不执行强制 reset。
- 健康检查失败：输出日志摘要（脱敏），恢复上一 manifest。
- 公网/TLS 失败：保持公网入口关闭，不降级为明文公网。

## 7. 交付报告

报告至少记录：profile、commit、manifest hash、镜像 digest、schema 版本、启用功能、验证结果、备份位置、回滚命令和未解决风险。
