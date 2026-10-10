# AGENTS 模板重新初始化实际发布（主 API＋主前端）

关联任务：[agents-template-reinitialize-20261010](../tasks/2026-10-10-agents-template-reinitialize.md)（后端与新面板）与 [management-workspace-layout-20261010](../tasks/2026-10-10-management-workspace-layout.md)（前端同一镜像一并发布）。方案见 [2026-10-10-agents-template-reinitialize](../plans/2026-10-10-agents-template-reinitialize.md)。发布机制沿用 conversation-summary-stats-20261008-r1 的镜像叠加构建＋容器替换流程。

## 发布身份

- 发布编号／关联任务：`agents-template-release-20261010-r1`／上述两任务
- 发布负责人／验证人：Codex
- 目标环境与精确对象：生产主 API 容器 `smartbrain-api-20260923-filter-internal-r1`（16:35 核对旧 Id `e6a1a794f8334ffda576f853b34eb6e9c99b70a89c9f785a51b68996fcb7cecb`、旧 Image `sha256:8eac15848ae9…`、2026-10-08T14:08:37Z 启动、RestartCount 0）与主前端容器 `smartbrain-agentops-dashboard-1`（旧 Id `4d2d06eca852aa4d94ec298eafdcfb62b1d850ccfe0711388af66326c70409ac`、旧 Image `sha256:295d3a7244d5…`、2026-10-08T12:06:49Z 启动）；MCP、个人代理、edge、数据库不在本次范围
- 授权来源、范围：用户 2026-10-10 指示"提交，推送，部署成产"，并在容量处置中选择方案 A（删除 2 个无引用悬空镜像＋归档后截断一个 310MB 无轮转候选日志＋清理可再生构建缓存）；仅替换上述两容器，无迁移、无模型调用、无 Key/路由变更
- 状态：**发布成功**。17:10:42–17:10:58 promote 切换完成，17:15 公网验证与终态观察通过，17:16 归档完成
- 记录更新时间：2026-10-10 17:25（Asia/Shanghai）；最后现场核对时间：2026-10-10 17:15–17:16
- 预期行为：已有 AGENTS.md 的项目可由管理员预览模板差异并 CAS 确认重置为最新模板，旧版本保留在 `project_agents_file_versions` 并可列表/下载；内容相同返回 unchanged 不写库；管理工作台紧凑布局随同一前端镜像生效
- 影响范围与验收标准：主 API 新增 4 条路由（匿名 401，旧版本为 404）；主前端脚本与容器逐字节一致；其他公网入口 200/401/410 行为保持；既有 AGENTS 指纹不变

## 发布前后版本清单

| 组件 | 旧版本与身份 | 候选版本与身份 | 实际生效版本与核对时间 | 源码和构建证据 |
|---|---|---|---|---|
| 主 API | 容器 `e6a1a794f833…`／镜像 `8eac15848ae9…`（2026-10-08 conversation-summary 构建），`project_agents.py` SHA `8fe177fb…` | 旧镜像为基底的单文件叠加镜像（仅替换 `project_agents.py`，候选文件 SHA `6b7d17f05dd66496ab5bfc85e7368c76b15ef20915eb1db09c7795bb27eadd12`） | 镜像 `smartbrain-agents-template-api:2026.10.10-r1`（`sha256:aa31ae74b5efa668c13bd617d717b8b7e17f5c62eeee39f5ba8296506a1f32d2`），新容器 `621935d93b37fe1a6a9245307686ee1e0fd4ca8afc4497b914cf4085e3c46227`；17:15:38 终态核对 Running、IP 172.18.0.10 保持 | `.artifacts/agents-template-release-20261010-r1/`：source-manifest.json（117 文件）、build-api.log、candidate-verified.json、promoted.json、final-observation.json |
| 主前端 | 容器 `4d2d06eca852…`／镜像 `295d3a7244d5…`（2026-10-08 构建） | 当前工作树源码整体重编译 runtime 镜像（含管理工作台布局与 AGENTS 面板变更；编译容器 `282babd13603…` network=none、node_modules 沿用 company-memory-updater-20261008-r1 只读绑定） | 镜像 `smartbrain-agents-template-frontend:2026.10.10-r1`（`sha256:743d5093f6c4d6694767593aa60368bd02bfc443fd05c2275d8f1619d7254ea3`），新容器 `85f21545e254d0d6ee85fd03f4ff3c3bed898f32a118e7227dfe8d7007846006`；17:15:38 终态核对 Running、IP 172.18.0.16 保持 | 同上：build-frontend.log、build-runtime.log、retained-assets.json（45 个旧静态资产保留）、public-verified.json |

候选源码提交：`422a157`（后端四端点＋前端面板）、`e44d2ff`（管理工作台布局）、`54ba040` 及本条文档提交（记录登记）；构建平台为生产主机 Docker（containerd store），编译网络隔离 `--network=none`。

## 数据迁移与兼容性

- 迁移：无。新端点只使用既有 `project_agents_files`／`project_agents_file_versions` 表。
- 兼容性核对（2026-10-10 09:54 只读，证据 `.artifacts/agents-template-reinitialize-20261010/backend/current-readonly.json`）：生产 `archive_project_agents_version` 触发器已安装且启用（迁移源码中 CREATE TRIGGER 缺失系仓库脚本陈旧，生产实际存在且引用列均存在）；新代码沿用 `upload_agents` 既有"显式 INSERT 历史行＋files upsert"模式，触发器 ON CONFLICT DO NOTHING 幂等共存；版本表 PK `(project_id,version)`、内容 1–65536 字节检查均满足（模板约 639 字节）。
- 部署期间只读指纹核对：promote 前、promote 后及终态三次核对 `initialize_project_agents()` 函数定义、`project_agents_files` 指纹、`project_agents_file_versions` 行数均与发布前逐字节一致（证据 agents-function-before.private.sql／agents-before-fingerprint.txt／agents-versions-count-before.txt 与 promoted.json、final-observation.json）。
- 新旧应用数据兼容：部署本身未写业务表；重置端点上线后产生的归档行不回退（同 Key 撤销类不可回退状态）。
- 备份：发布前/切换后/终态三次核对 backup inactive/success、登记 20 服务、timer enabled；本发布不新增备份，运行镜像与证据已归档到 `/srv/smartbrain-backups/backups/agents-template-release-20261010-r1`（非冻结备份/恢复验收）。

## 发布步骤与实际结果

| 顺序 | 目标与前置条件 | 动作及预期结果 | 实际时间、退出码和证据 | 失败或中断处理 |
|---|---|---|---|---|
| 1 | 生产只读预检：目标容器身份/代际、backup 终态、无 pending、edge 双视图、依赖目录存在 | 16:35 核对通过：1025 容器/39 运行；backup inactive/success/MainPID 0/Job 空；无 maintenance.pending；node_modules 依赖与 release_lib 在位 | 已完成（16:35–16:38，baseline.json、production-before.private.json） | — |
| 2 | Docker 盘 ≥40 GiB | 16:35 为 42,886,754,304 字节（39.94 GiB）不过线；按用户所选方案 A 处置：删 2 个无引用悬空镜像（09-11/09-14，释放≈0，层共享）；将运行中容器 `smartbrain-api-agents-short-ready-20261008-r1` 的 310,146,177 字节无轮转 json 日志先复制到 `/srv/smartbrain-backups/backups/agents-template-release-20261010-r1/log-rotation/`（0600）再截断——活动写入致源/副本 hash 不一致（源 `c0d3f6fb…`／归档副本 `e5b7e6e29d416ee55efdbfa5618af500e667cd7b44f76ced2521b2b4df784f65`），如实记录；构建后终态门禁一度 42,935,275,520 字节（39.98 GiB）仍不过线，`docker builder prune -f` 清 89.2MB 可再生未用构建缓存（未动任何镜像/容器/卷）后 43,023,749,120 字节（40.07 GiB）通过，候选未重建仅补验 | 已完成（16:57–17:09，log-rotation/、candidate-verified.json `note` 字段、archive-manifest.json） | 未删任何证据镜像/容器；门槛不满足时未进入构建 |
| 3 | 源码打包 | 本地生成 source.tar.gz（327,747 字节）＋逐文件 manifest（117 文件：API 候选 1 文件＋前端全部源文件＋两个 Dockerfile），SHA 固定并上传生产 | 已完成（17:05，source-manifest.json） | — |
| 4 | 候选构建（双锁、verify_backup==20、AST 函数保留校验） | API 叠加镜像 `aa31ae74b5ef…`＋候选容器 `b6d43ac6e2d9…` `/health/ready` 通过；前端隔离编译＋runtime 镜像 `743d5093f6c4…`＋候选容器 `759ddeb95e39…` `/login` 通过；45 个旧静态资产保留；生产零切换 | 已完成（17:06–17:09，build-*.log、candidate-verified.json） | — |
| 5 | 候选验收 | 候选 API 三条新路由匿名 401、旧 API 同路径 404 前后对照；候选前端 chunk `277-cbb62033288e76b7.js`（9,669 字节，SHA `fe505dc8a4c3259ea4c40677e7a32ecf098626c3a6e063603c448ee74216cdd0`）含"重新初始化为最新模板"文案，旧前端无此文案 | 已完成（17:09:39，candidate-acceptance.json） | — |
| 6 | promote dry-run | 全量断言（代际、systemd 无引用、登记 20、四盘、内存 7.67GB、edge 双视图、AGENTS 函数/指纹/版本数）通过 | 已完成（17:10:41，promote-dry-run.json） | — |
| 7 | promote | 旧容器 restart=no→停止→断网→改名 `-rollback-agents-20261010-r1`；新容器按 clone_config 同配置创建并启动，ready 通过；公网 10 项（5×200＋5×401）通过；未触发自动回退 | 已完成（17:10:42–17:10:58，promoted.json、targets-created.json） | 自动回退分支未执行（无异常） |
| 8 | 公网验收 | `/admin` `/wiki` `/login` `/workday` `/health/ready` 200；匿名新路由 401、匿名 Key/records 401；16 个页面脚本公网与容器直连逐字节一致；新文案 chunk 公网可获且 SHA 匹配；45 个 retained 资产全部可访问；edge 双视图 SHA `c22e68d972aeb997dbf5328dd00ca1de968fabe7455e4b8eb23037d28ed78626` 不变 | 已完成（17:15:07，public-verified.json） | — |
| 9 | 终态观察＋归档 | 1030 容器/39 运行、1023 无关容器代际/启动时间/RestartCount 全保持；临时两候选与编译容器停止保留（exit 0）；backup inactive/success/登记 20/timer enabled；四盘 docker 43,020,775,424／根 33,940,869,120／backups 522,315,313,152／cold 271,876,235,264 字节，内存 8,209,711,104 字节；4 个退休下载 410；AGENTS 函数/指纹/版本数三次一致。归档：api-runtime.tar 192,728,576 字节 SHA `87e8ac4cca29239a989c3de57cbad18d239ae4f6b6426575f7e45851ba0f05f3`（OCI 29 描述符逐项复核）、frontend-runtime.tar 72,407,040 字节 SHA `3915b1f969c034c59634c72aa63f76118876d24a11a9a14e70e3b21b6ab0c71d`（15 描述符）、evidence.private.tar.gz 1,038,650 字节 SHA `549b614d4b376a0706629ed131f70b0985d1460ba4bf765e5d2f32aba1b6ceef`，均 0600 | 已完成（17:15:38 终态、17:16:37 归档，final-observation.json、archive-manifest.json） | — |
| 10 | 文档与镜像 | 本记录补实际、README/CURRENT 更新并镜像 E 盘逐字节核对；提交推送 | 本条随文档提交执行 | — |

## 发布后验收

| 验收标准 | 实际入口与身份 | 实际结果和时间 | 证据 |
|---|---|---|---|
| 登录和本次业务流程（管理员预览→CAS 重置→版本历史下载） | 公网需真实管理员会话；本轮以匿名 401/404 前后对照＋候选容器内自检＋本地 21 pytest／205 vitest 为准，真实员工闭环操作未执行、不代替 | 未执行（需真实管理员会话，本轮未授权员工侧操作） | candidate-acceptance.json、implementation-manifest.json |
| 匿名／越权边界 | `GET /v4/projects/{id}/agents/template-preview`、`/agents/versions`、`/agents/versions/{v}/download` 匿名 401（旧 API 同路径 404 对照）；匿名 Key/records 401；退休下载 410 | 通过（17:10:58 切换后即验、17:15:07 复验、17:15:38 终态复验） | promoted.json、public-verified.json、final-observation.json |
| 生效版本、绑定与相关服务健康 | API 容器 `621935d93b37…`／镜像 `aa31ae74b5ef…`，前端容器 `85f21545e254…`／镜像 `743d5093f6c4…`；IP/网络/alias/Env/User/HostConfig 与旧容器逐项一致；edge 双视图不变且 bind 只读；backup 登记 20 | 通过（17:15:38） | final-observation.json |
| 重启或恢复能力 | 旧容器 `e6a1a794f833…`／`4d2d06eca852…` 改名 `-rollback-agents-20261010-r1` 停止、断网、restart=no 保留，可经名称/网络/重启恢复；不执行整机或数据库恢复 | 保留就位（未触发实际回退） | final-observation.json targets 段 |

## 回退方案

- 触发条件：promote 后 readiness/公网验收失败或代际断言失败；决策负责人：发布负责人（Codex）按现场执行，用户可随时指示回退。
- 回退目标：旧 API 容器 `e6a1a794f8334ffda576f853b34eb6e9c99b70a89c9f785a51b68996fcb7cecb`（镜像 `8eac15848ae9…`）、旧前端容器 `4d2d06eca852aa4d94ec298eafdcfb62b1d850ccfe0711388af66326c70409ac`（镜像 `295d3a7244d5…`），现名 `…-rollback-agents-20261010-r1` 停止保留；最近可用性核对：17:15:38 终态确认两容器指纹与发布前一致、未运行。
- 回退层次：应用层——新容器停止改名 `-failed-…`，旧容器恢复原名/原 IP/alias/重启策略并启动，ready 复核；配置层——本次无配置变更；路由/edge——不变更，无需回退；数据库——本次无迁移，部署未写业务表，无需回退（上线后用户主动重置产生的新归档行属业务数据，不随应用回退删除）。
- 旧应用对当前数据兼容：部署本身未写表，旧应用直接读现有表可运行；兼容性以只读指纹前后一致核对（已三次核对一致）。

| 顺序 | 精确目标和前置条件 | 回退动作及预期结果 | 失败或中断处理 |
|---|---|---|---|
| 1 | promote 脚本异常分支自动执行（机制同 conversation-summary r2，已生产实证一次） | 新容器停止改名；旧容器恢复名称/网络/重启策略并启动至 ready；指纹核对 | 本次未触发；脚本内该路径保留 |
| 2 | 手动回退（自动失败时） | 按 `promote-rollback` 证据逐容器恢复 | 本次未触发 |

## 回退验证与实际执行记录

| 类型 | 时间与环境 | 结果 | 证据及局限 |
|---|---|---|---|
| 静态检查／dry-run | 2026-10-10 17:10:41 生产主机 | 通过（全量断言，含 systemd 无引用、四盘、edge、AGENTS 指纹） | promote-dry-run.json；不等于生产实际回退 |
| 生产实际回退 | 未执行（发布一次通过，未触发） | 未执行 | 未执行则不称恢复演练通过 |

## 收尾

- 实际终态：发布成功。新 API/前端容器运行中（Id 见上），旧容器停止保留，无关 1023 容器代际保持，backup 20 登记/timer enabled，四盘与内存门槛达标（17:15:38）。真实管理员会话的功能闭环验收未执行（本轮未授权员工侧操作）；公网匿名边界、脚本逐字节、静态资产、edge 双视图均已验收。
- 保留的旧版本、备份、证据及后续清理条件：旧两容器（`-rollback-agents-20261010-r1`）与旧镜像 `8eac15848ae9…`／`295d3a7244d5…` 按惯例停止保留；临时候选容器 `b6d43ac6e2d9…`／`759ddeb95e39…` 与编译容器 `282babd13603…` 停止保留；清理需单独授权。镜像 tar 与证据归档于 `/srv/smartbrain-backups/backups/agents-template-release-20261010-r1/`（含 log-rotation 保留日志，archive-manifest.json 独立 SHA 清单），非冻结备份/恢复验收点。
- 容量处置如实记录：本次为腾出 Docker 盘，截断了一个运行中候选容器的 310MB 无轮转 json 日志（已先复制归档，活动写入致源/副本 hash 不一致），并清理 89.2MB 可再生构建缓存与 2 个无引用悬空镜像（释放≈0）；未删任何证据镜像/容器/卷。
- 任务接续记录与 CURRENT 更新位置：本条与 [CURRENT](../CURRENT.md) 2026-10-10 17:25 条目同步；E 盘镜像随本条逐字节核对。