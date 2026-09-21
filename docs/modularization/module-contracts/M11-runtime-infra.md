# M11 — runtime-infra

## 业务职责

管理 Compose、Dockerfile、nginx、公网中继、Jockey、备份、恢复和部署脚本。

## 不负责

不负责业务领域逻辑、数据库表所有权或模型请求正文。

## 当前实现

- `deploy/`
- 根目录 Compose/Dockerfile；
- `scripts/`；
- 备份和运行时配置。

## 输入输出

- 输入：已批准的镜像、环境变量名、服务契约和部署目标。
- 输出：可复现部署、健康检查、回滚/恢复脚本和运行清单。
- 公共接口：环境变量 contract、服务端口/health contract、镜像和迁移版本清单。

## 安全边界

不得把 `.env`、密码、Key、数据库 dump、Cookie 或真实用户正文纳入仓库或日志。

## 独立性

可独立维护，但任何生产部署、数据库迁移、systemd/nginx 修改都必须单独审批和可回滚验证。
