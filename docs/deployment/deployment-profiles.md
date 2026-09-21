# SmartBrain 部署 Profile

部署 profile 是“需求 → 服务拓扑”的唯一入口。AI 或人工部署时必须先选择 profile，再执行 preflight；不得通过猜目录或临时拼接 Compose 命令决定服务。

## Profile 总览

| Profile | 适用场景 | 默认服务 | 不包含 |
|---|---|---|---|
| `minimal` | 低资源、本地功能验证 | Web、API、PostgreSQL、Redis | ClickHouse、RAG、公网入口、员工端 |
| `lan` | 局域网完整业务 | Web、API、PostgreSQL、Redis、ClickHouse、Wiki worker | 公网中继、真实员工端 |
| `rag` | 需要知识检索 | `lan` + embedding、reranker、材料卷 | 公网中继、员工端 |
| `public-relay` | 公网 HTTPS | `lan`/`rag` + nginx、relay、TLS | 不自动启用真实模型或新 Key |
| `employee` | 员工 Monitor 试点 | `lan`/`rag` + Monitor API、员工载荷 | 不自动发布安装包到公网 |
| `air-gapped` | 离线或受限网络 | 本地镜像导入后的 `minimal`/`lan` | 在线 pull、自动外部访问 |

## 选择规则

1. 没有明确需求时使用 `minimal`，不自动启用公网、RAG、员工端或 AI Gateway。
2. 需要局域网业务时使用 `lan`。
3. 只有在硬件、模型和磁盘检查通过后才追加 `rag`。
4. `public-relay` 必须单独确认域名、TLS、端口和隧道配置。
5. `employee` 必须先确认员工身份协议和安装包来源。
6. `air-gapped` 只允许使用 manifest 中已校验的本地镜像。

## 功能开关

功能开关必须在 profile 或用户明确输入中声明：

- `web`
- `api`
- `postgres`
- `redis`
- `clickhouse`
- `rag`
- `wiki`
- `member_wiki`
- `ai_usage`
- `ai_gateway`
- `employee_monitor`
- `public_access`
- `tls`

未声明的功能默认关闭。部署工具不得因为发现某个文件存在就自动启动对应服务。

## 资源门槛

资源门槛应由 release manifest 提供，不能写死在 AI 对话中。至少检查：

- Docker/Compose 版本；
- 可用内存；
- 可用磁盘；
- GPU 和驱动（仅 RAG）；
- 端口占用；
- DNS/外网连通性（仅公网 profile）；
- 本地镜像 digest（离线 profile）。
