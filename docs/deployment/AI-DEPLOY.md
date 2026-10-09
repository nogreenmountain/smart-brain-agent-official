# 将当前智慧大脑部署到一台新机器

入口版本：current-20261009-streaming-ch-r1；个人API现场核对2026-10-09 16:40、ClickHouse合并资源配置17:51（北京时间），其余组件沿用13:30–14:05快照。当前分支包含个人API流式修复和CH后台合并限并行配置，先读本文件再执行。

## 交给 AI 的任务文本

> 使用本分支，在一台新的、获授权的 Linux 主机复现 current-20261009。先读 AGENTS.md、docs/CURRENT.md 和 docs/deployment/AI-DEPLOY.md；逐项核对前置条件。使用 deploy/current/compose.yaml、release-lock.json 和 verify.py。取得项目方受控交付的镜像、私有配置和经验证的数据备份；缺失项必须点名报告。先隔离恢复数据，再启动业务、验证权限与对话闭环，最后配置 HTTPS 和生命周期。保留每阶段命令、版本与结果。不要执行旧 release runner、旧 seed、Monitor/适配器安装或试点网关脚本。不要把机密打印到聊天、日志或 Git。

## 1. 选择复现目标

| 目标 | 输入 | 输出与边界 |
|---|---|---|
| **restore：原项目原样复现** | 固定镜像包、原私有配置、同一恢复点的 PG/CH/文件/上游授权状态 | 账号、项目 UUID、知识库、历史请求与权限保留；要求恢复验收 |
| fresh：相同版本的空项目 | 同一镜像包、新 Secrets、当前结构基线、新管理员、上游授权 | 功能版本相同，账号与业务数据新建；不能称原生产数据恢复 |
| source：修改后重新构建 | 本分支、锁定依赖、构建网络、现有基础服务镜像 | 新 Image ID；需新版本清单与重新验收，不能冒充 restore |

Git 保存代码、配置模板和结构，不保存真实密码、员工正文、数据库数据或 OAuth 登录态。仓库与下面的受控交付物共同组成复现输入。首次部署在新主机／新数据目录进行；不能将这些步骤直接套到原生产主机。

## 2. 必须准备的条件

| 项目 | 条件及检查 |
|---|---|
| 主机 | Linux x86_64，建议 Ubuntu 24.04；Python 3.12+、Git、Docker Engine 29.x，启用 containerd image store；Compose 2.33.1+（raw env_file / gpus） |
| 内存与 CPU | 启动检查要求可用内存至少 4.5 GiB，保留既有资源门槛；这只是门槛。当前现场约 16 GiB／12 CPU，不能据此承诺 30 人全功能峰值。新全栈可从 32 GiB／8+ CPU 规划，再实测 |
| 磁盘 | 镜像包约 6.15 GB，21 个唯一镜像；解包/导入按 lock 中大小预留。操作后 Docker 保留 40 GiB，数据和备份目录各保留 250 GiB。建议独立 SSD 数据与备份盘；不要靠删除历史证据绕过检查 |
| GPU/RAG | 当前 embedding 与 reranker 配置为 CUDA，需 NVIDIA GPU、匹配驱动、Container Toolkit 和模型缓存。`--profile rag` 请求 GPU。CPU 模式是明确的配置变更，须重新验收性能 |
| 网络 | HTTPS 域名／可信 IP 证书、DNS、443 入站、镜像/依赖/模型下载或受控离线输入。内部 PostgreSQL、Redis、CH、MCP 不暴露公网 |
| 模型上游 | 合法有效的原 Codex 上游和授权；`PERSONAL_UPSTREAM_URL` 从新主机可达。原环境依赖另一台 Windows 主机，不是 Git 内自带服务。禁止回落代码中的旧 LAN 默认地址 |
| 模型目录 | BAAI/bge-m3、bge-reranker-v2-m3 与 MCP fastembed 缓存；离线时必须完整交付。仅有 Docker 镜像不代表模型已缓存 |
| 操作权限 | 管理新主机 Docker／文件／数据库；读取受控包。数据迁移、真实模型验证、域名切换按实际授权执行 |

原现场ClickHouse后台合并资源配置已于17:49调整为pool2/ratio1，发布后效果见夜间发布记录；长期容量和完整冻结备份恢复仍未验收。不能把短观察称为全平台恢复通过。

## 3. 受控交付物

本轮已生成受控包，保存在原服务器：

个人API增量包：`/srv/smartbrain-backups/backups/personal-api-streaming-20261009-r2/images/`。基线包与增量包均须交付；先按base lock导入旧21镜像，再按delta lock导入1个修复镜像，最终current lock校验21个当前镜像。不要只用基线包启动本分支。

`/srv/smartbrain-backups/backups/repository-current-20261009-r1/`

- `images/images.tar` + `images/bundle-manifest.json`：当前 21 镜像，包含全部 30 服务所用版本。
- `config.private.tar.gz`：实际 30 服务 Env、模型网关/出口配置和三个静态站点，共 48 文件；**含机密，不进入 Git**。
- `config/bundle-manifest.json`：私有输入文件校验。复制到新主机后先校验再改主机地址。
- 未包含：PG/CH 业务数据、Redis 队列/会话、上传文件、Supabase 文件、模型缓存、模型网关 OAuth 状态、出口状态、TLS/SSH 私钥。这些须按同一恢复点另行交付。

项目管理员通过受控 SSH／存储交付，不上传公开 Release。包的身份见 `deploy/current/controlled-artifacts.json`。原备份目录只作为交付来源，不能拿一份未经恢复验证的旧 online 备份填写“已通过”。

若将来需要重新导出同版本镜像，在有全部 lock 镜像的来源主机执行：

```bash
python3 deploy/current/images.py export --directory /受控备份盘/新的包目录
```

工具检查原镜像、容量和 OCI 身份；输出目录必须全新且在 checkout 外。不要重跑本轮已经生成的包。

## 4. 获取仓库、固定版本

```bash
git clone --branch codex/overnight-operations-20261009 --single-branch \
  https://github.com/nogreenmountain/smart-brain-agent-official.git /opt/smartbrain-current
cd /opt/smartbrain-current
git rev-parse HEAD
python3 deploy/current/verify.py sources
```

保存实际提交 SHA。部署期间不要拉取移动分支；后续更新按发布记录处理。

## 5. 准备配置和导入镜像

在 checkout 外创建 `/etc/smartbrain-current`、`/srv/smartbrain-current-state`、`/srv/smartbrain-current-backups`；配置根 0700。放入受控 Env/配置/站点。fresh 可从 `env-examples/` 复制模板并填写所有 `__SET_*__`；restore 使用原配置并按新主机调整地址。

```bash
cp deploy/current/.env.example /etc/smartbrain-current/deployment.env
# 编辑外部 deployment.env；不要 source 它，不要在终端输出 Secret。
# 13:30基线21镜像包使用保留的base lock验证导入。
python3 deploy/current/images.py verify --directory /受控路径/基线/images --lock deploy/current/release-lock-base-20261009.json
python3 deploy/current/images.py import --directory /受控路径/基线/images --lock deploy/current/release-lock-base-20261009.json
# 再导入16:39个人API流式修复的单镜像增量包。
python3 deploy/current/images.py verify --directory /受控路径/流式修复/images --lock deploy/current/release-lock-streaming-delta.json
python3 deploy/current/images.py import --directory /受控路径/流式修复/images --lock deploy/current/release-lock-streaming-delta.json
python3 deploy/current/verify.py images
python3 deploy/current/verify.py bundle --bundle-root /受控路径/config
```

ClickHouse资源配置来自本分支 `deploy/current/clickhouse/backup-disk.xml`，SHA256为 `ecf3efd265105bff68ee400364c073f53e256da913b9255d418f7e253ee284b1`。它保留原备份磁盘路径并追加pool2/ratio1及相关阈值1。Compose已挂载此仓库文件；请保留本分支XML，不要用13:30历史配置包或旧分支覆盖。先按原manifest核验私有配置包，原包及镜像包无需重写；`verify.py sources`同时核对新XML。新机CH启动后必须读回两个预算与三个阈值，实际业务数据恢复仍须独立验收。

模板 Env 采用 raw 格式，不做 `$`、引号或反斜杠展开。目录／文件从受控包复制后再设置服务权限：Env 0600；两个模型配置归 UID10001/GID10001、0640；三个静态站点归 UID101/GID101、目录0750／文件0640。保持配置根0700。不要把原完整 Env 中的 PATH/HOSTNAME 注入不同代基础镜像；模板列出了需要保留的业务变量。

关键对应关系：

- API/个人代理/read/MCP/worker 的 DB 名、账号、密码指向**新** PostgreSQL；GoTrue/Storage/PostgREST DSN 使用各自角色，URL 中密码须正确百分号编码。
- Supabase JWT Secret、GoTrue JWT、PostgREST JWT、Storage JWT、对应 anon/service-role JWT 必须互相匹配；Cookie/MCP Secret 在 restore 保留原值，否则旧会话／Token 会失效。
- `SB_GATEWAY_ALLOWED_USER_IDS` 使用恢复后的真实成员 UUID 列表，逗号分隔；不能用项目 UUID 或示例成员。`SB_GATEWAY_TRUSTED_INSTANCES` 保持可信上游实例映射，关联原 Key/记录库。
- 项目 UUID 来自项目自己的新 AGENTS.md；原 CLI 会话有旧规则时须重新启动。当前不使用适配器、不绑定个人 Key 到项目。
- 在 `api` 等 Env 中逐项核对 `ANTHROPIC_BASE_URL` 和功能模型名；不同组件原值可能不同，不能只改一个服务。Compose 明确设置个人代理 upstream，避免旧 LAN 默认。
- `PUBLIC_HOST`、所有公开 URL、MCP allow hosts/origins、GoTrue回调、TLS、CLI Token URL统一；同机访问以 HTTPS 为准。前端 Next.js build-time 常量不能靠运行 Env 自动改写，换域名需检查实际 JS 地址；必要时重新构建前端并记录版本差异。
- RAG 模型名/版本、feature flags保留当前模板；`AI_WORKLOG_BACKFILL_START_DATE` restore 保留原策略，fresh 留空需记录。不要恢复退休 Monitor、Langfuse 或 reconcile timer。

从 release-lock 的 `state_directories` 创建全部11个目录。新目录按服务 UID 分配：应用与模型缓存10001，Storage1000，PostgreSQL按镜像 postgres UID，Redis/CH按各自镜像 UID。已有数据按其恢复清单的所有权恢复，禁止对不明共享目录递归 chown。

## 6. 数据恢复／初始化，业务 writer 先保持停止

先配置外部文件并渲染，渲染结果仅保存受控目录：

```bash
docker compose --env-file /etc/smartbrain-current/deployment.env \
  -f deploy/current/compose.yaml --profile rag --profile workers config --quiet
docker compose --env-file /etc/smartbrain-current/deployment.env \
  -f deploy/current/compose.yaml up -d postgres redis clickhouse
```

等最终 PostgreSQL TCP readiness；入口脚本的临时数据库进程不能算初始化完成。新主机 PostgreSQL数据目录必须为空或已由恢复流程完整恢复。

**restore 路径：**

1. 将同一恢复点的 PG custom dump／角色与 ACL 方案恢复到隔离数据库；账号、项目、Key映射、对话表、RLS和业务函数一起恢复。先检查目录列表和备份SHA；普通逻辑恢复用 `pg_restore --exit-on-error --no-owner --no-acl`，不对现有业务库执行 `--clean`。原ACL须按受控清单恢复并验证。
2. 使用 `postgres/supabase-roles.sql`校正 Supabase 角色密码、schema所有权与权限；脚本由容器Env读取密码，不把密码写进命令。数据库名指向恢复库，不改变原生产。
3. 恢复 CH 数据库/表/物化视图、上传文件、Storage文件、Redis持久化/队列、网关授权状态和缓存；检查 PG文件引用、模型向量维度、CH历史页、队列 pending 数。已有任务可能被 worker 重放，验收前不启动 workers。
4. 执行 `postgres/validate.sql`并对照原备份校验账号/项目/成员/对话/Key数量和内容hash、跨用户拒绝、撤销Key拒绝、文件读回；结果保存在受控证据目录。

**fresh 路径：**

1. Supabase固定镜像初始化结束后，创建全新业务库，使用 TEMPLATE template0。先创建必要角色，再执行 `postgres/schema-current.sql`。本轮实际相同镜像的隔离 PG 空库结构恢复已通过；该文件去掉旧所有者/ACL，含函数、RLS、索引和触发器，不含用户或业务数据。
2. 用容器的 `psql -X -v ON_ERROR_STOP=1`执行结构文件；再针对新库运行 `postgres/supabase-roles.sql`并执行`postgres/bootstrap-empty.sql`。SQL通过私有 `POSTGRES_DB`和`SUPABASE_DB_PASSWORD`Env传值。不要在初始化完的同名库重复装完整schema，也不要按文件名盲目重放全部历史migration。
3. 更新全部DSN到新业务库。Supabase服务就绪后，用GoTrue管理员接口创建你自己的管理员，密码由私有请求文件提供；然后通过受控SQL将该UUID的`public.users.is_system_admin`设true。只创建授权管理员，不运行 `create_users.py`、seed.server.sql 或 Initialize-Database.ps1 的默认密码账号。
4. CH新数据库先用 `render_sql.py --env-file /etc/smartbrain-current/env/clickhouse.env --output /etc/smartbrain-current/clickhouse-current.sql` 渲染受控DDL，再执行该文件；字典密码占位符不可直接执行。补充经管理员核对的模型价格表数据。原结构模板是 `clickhouse/schema-current.sql`（业务库名默认otel_2；修改时整份映射）。collector当前`create_schema=false`，不负责补业务DDL。新库不恢复历史统计；CH结构与数据恢复须独立验收。
5. 新建项目、员工和个人Key由产品界面正常创建。填写真实成员allowlist和可信上游配置，准备模型缓存。empty schema不是有业务数据的restore。

数据与权限验证完成后，复制 `restoration.example.json`到外部`restoration.json`；逐项填写实际结果、核对时间和证据目录，最后才设置 verified=true。不要跳过 false，也不要用本轮空PG结构测试替代整库恢复证据。

## 7. 启动、验收与 HTTPS

```bash
python3 deploy/current/verify.py preflight \
  --config /etc/smartbrain-current/deployment.env --mode restore --profiles rag,workers
# fresh 要改 --mode fresh，并确保 receipt.mode 一致。
docker compose --env-file /etc/smartbrain-current/deployment.env -f deploy/current/compose.yaml \
  up -d auth postgrest storage-api auth-gateway egress-proxy ai-gateway otelcollector
docker compose --env-file /etc/smartbrain-current/deployment.env -f deploy/current/compose.yaml \
  --profile rag up -d rag-embedding-service rag-reranker-service
docker compose --env-file /etc/smartbrain-current/deployment.env -f deploy/current/compose.yaml \
  up -d api personal-key-api-r1 workday-gateway-read collaboration-api wiki-mcp \
  agentops-dashboard workday-records-unified personal-gray-web smartbrain-monitor-removal smartbrain-monitor-removal-public edge
python3 deploy/current/verify.py smoke --url http://127.0.0.1:8080
```

设置主机HTTPS入口：复制 `nginx/https-ingress.conf.example`到**新主机**Nginx配置，替换域名及实际证书路径，nginx -t后reload。edge只绑定loopback8080。需要原SSH中继时，独立核对新relay账号、known_hosts和转发端口后启用`--profile relay`；不要占用原生产中继端口。公网smoke再执行一次，保持严格TLS。

浏览器／CLI业务验收必须全部记录：

| 检查 | 成功标准 |
|---|---|
| 登录和权限 | 自己可登录；匿名401，跨用户／跨项目403或404；原撤销Key失效 |
| 页面/静态文件 | root/wiki/workday/admin/personal页面正常；两代_next资源无404，刷新无JS错误 |
| Company Memory | 网页下载当前更新器及插件；新CLI会话初始化MCP，工具可查询项目与材料 |
| 对话记录 | 提交一条简短结果摘要；不上传思考过程、工具日志和全部上下文；返回可读回ID，项目/成员/时间准确；知识库及统计实际读回 |
| 请求归属 | CLI按项目AGENTS UUID；前端工作记录显示同项目，内部auto-review／后台请求不冒充用户对话 |
| 个人代理 | 8执行/24等待/60秒排队/DB并发3；5/10/20/30合成梯度，等待模型时DB不占连接；满/超时503，取消释放；真实模型小额度另授权 |
| RAG/文件 | CUDA设备可见，两模型health就绪；材料上传、解析、检索、权限过滤与文件下载通过 |
| Workers | 启动前核对pending任务与模型预算，逐个启用workers profile；日报/审批/解析/Wiki实际完成，日志无重复与长期重试 |
| 恢复 | 停启、重启新主机、数据持续、备份恢复验证，保留命令与证据 |

核对队列后启动六workers，再建立systemd：`systemd/smartbrain-current.service.example`仅新主机模板，按checkout路径、receipt mode和选择的profiles修改；通过stop/start及重启测试后才enable。Docker重启策略与systemd作为同一部署的生命周期，不复制旧原生产CID绑定unit。

## 8. source 构建与后续更新

精确复现优先导入本轮镜像；源码新构建路径见 [SOURCE-BUILD.md](SOURCE-BUILD.md)。七组Python代码快照和hash已固定，但apt构建包、历史前端产物及外部授权不能由Git凭空产生。新镜像需新Image ID/配置/验收记录，不能把release-lock中的旧ID替换成移动tag后仍称同版本。

升级先保存旧镜像/Env/状态、备份并验证恢复、迁移兼容性、候选验收，然后切换入口。发生失败先停本次新writer并保留日志；不删除volume、不prune、不down -v、不重放签发Key/迁移/备份runner。完整回退是否成功单独记录。

## 本分支的实际验证范围

当前源码相关前端66项、代理33项、部署工具21项通过；Compose30服务全profile解析；1425运行源码hash一致；相同生产PG镜像隔离空库schema与结构gate通过。受控镜像与静态/配置包已准备，生产业务容器没有重启。

**尚未完成的是一台全新机器的完整业务数据恢复、全部30服务冷启动、GPU/上游授权和真实员工全流程验收。**本文件给出这些验收的执行步骤与硬前置条件；交付时不得将它们填写为passed。详细记录见 [仓库交付验收](../releases/reproducible-repository-20261009.md)。
