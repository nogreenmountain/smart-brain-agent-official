# 从源码构建新候选镜像

此路径产生新镜像版本。当前原样复现继续使用 [AI-DEPLOY](AI-DEPLOY.md) 的受控镜像包。

## 后端

Python3.12.11基础镜像固定digest、uv0.6.14、api/uv.lock及附加依赖hash lock已保存。所有运行模块来自各自实际快照，避免用未发布的canonical候选覆盖另一组件。

在仓库根目录，以api为例：

```bash
docker buildx build --load \
  --build-context api-src=./api \
  --build-context jockey-src=./api/jockey \
  --build-context runtime-src=./deploy/current/runtime-sources/api/agentops \
  -f deploy/current/dockerfiles/Dockerfile.backend \
  -t smartbrain-source-api:current-20261009 deploy/current/dockerfiles
```

依次将runtime-src替换为personal-api、workday-read、collaboration-api、mcp、workers、worklog-worker目录，并使用不同本地tag。MCP命令是`python -m agentops.wiki_mcp.server`；其他实际命令见compose。统一Dockerfile的默认启动命令只适用于main API，Compose中的组件command必须保留。worklog-worker快照包含实际两份挂载修复；新build不要再叠加旧hotfix文件。

源构建需要基础镜像、apt/PyPI及tiktoken下载网络；apt包未按快照日期固定，所以不承诺字节一致。构建后检查依赖锁、uid10001、组件import、匿名鉴权、工具协议与对话简短提交，再运行已有相关回归。根据新Image ID生成**新的**部署清单，保留原release-lock。

## 当前前端

`smartbrain-dashboard/package-lock.json`固定npm依赖；Next15.5.23、React19。可以使用仓库的`smartbrain-dashboard/Dockerfile`与npm ci构建候选：

```bash
docker build -f smartbrain-dashboard/Dockerfile \
  -t smartbrain-source-dashboard:current-20261009 smartbrain-dashboard
```

该历史Dockerfile使用node20-alpine移动基础镜像；发布前固定实际基础digest与平台，记录新版本。检查构建期NEXT_PUBLIC变量，禁止将旧生产主机地址带入新host。

当前root/wiki/personal页面仍由历史workday-records-unified前端提供，admin/workday/插件下载由新frontend提供。仓库没有证明历史root frontend的所有源码与原镜像逐字节一致；原样复现需其受控镜像。不要从同一个新frontend build猜测两套页面都可替代，必须做页面和静态资源兼容验收。

## 基础服务、RAG与外部授权

PostgreSQL、Redis、CH、Supabase组件、OTel、两个RAG服务、CLI模型网关与出口代理优先导入锁定镜像。仓库中的RAG源码和旧Dockerfile供开发参考；不同构建依赖和模型权重必须重新锁定、测量显存与延迟。仓库无法重新生成原OAuth登录态和外部Windows上游授权。

源构建完成不代表全项目已部署。正式交付仍需AI-DEPLOY中的数据、权限、MCP、对话、30并发、文件/RAG、生命周期与恢复验收。
