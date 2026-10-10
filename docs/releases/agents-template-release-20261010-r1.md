# AGENTS 模板重新初始化实际发布（主 API＋主前端）

关联任务：[agents-template-reinitialize-20261010](../tasks/2026-10-10-agents-template-reinitialize.md)（后端与新面板）与 [management-workspace-layout-20261010](../tasks/2026-10-10-management-workspace-layout.md)（前端同一镜像一并发布）。方案见 [2026-10-10-agents-template-reinitialize](../plans/2026-10-10-agents-template-reinitialize.md)。发布机制沿用 conversation-summary-stats-20261008-r1 的镜像叠加构建＋容器替换流程。

## 发布身份

- 发布编号／关联任务：`agents-template-release-20261010-r1`／上述两任务
- 发布负责人／验证人：Codex
- 目标环境与精确对象：生产主 API 容器 `smartbrain-api-20260923-filter-internal-r1`（16:35 核对 Id `e6a1a794f833…`、Image `sha256:8eac15848ae9…`、2026-10-08T14:08:37Z 启动、RestartCount 0）与主前端容器 `smartbrain-agentops-dashboard-1`（Id `4d2d06eca852…`、Image `sha256:295d3a7244d5…`、2026-10-08T12:06:49Z 启动）；MCP、个人代理、edge、数据库不在本次范围
- 授权来源、范围：用户 2026-10-10 指示"提交，推送，部署成产"；仅替换上述两容器，无迁移、无模型调用、无 Key/路由变更；容量门槛按现行门禁实时核对
- 状态：准备中——16:35 实时核对 Docker 盘可用 42,886,754,304 字节（39.94 GiB）低于 40 GiB 门槛，须先满足门槛再构建
- 记录更新时间：2026-10-10 16:45（Asia/Shanghai）；最后现场核对时间：2026-10-10 16:35–16:38
- 预期行为：已有 AGENTS.md 的项目可由管理员预览模板差异并 CAS 确认重置为最新模板，旧版本保留在 `project_agents_file_versions` 并可列表/下载；内容相同返回 unchanged 不写库；管理工作台紧凑布局随同一前端镜像生效
- 影响范围与验收标准：主 API 新增 4 条路由（匿名 401，旧版本为 404）；主前端脚本与容器逐字节一致；其他公网入口 200/401/410 行为保持；既有 AGENTS 指纹不变

## 发布前后版本清单

| 组件 | 旧版本与身份 | 候选版本与身份 | 实际生效版本与核对时间 | 源码和构建证据 |
|---|---|---|---|---|
| 主 API | 容器 `e6a1a794f833…`／镜像 `8eac15848ae9…`（2026-10-08 conversation-summary 构建），`project_agents.py` SHA `8fe177fb…` | 旧镜像为基底的单文件叠加镜像（仅替换 `project_agents.py`，候选 SHA `6B7D17F0…`） | 未生效 | `.artifacts/agents-template-release-20261010-r1/`（构建后补镜像/容器 Id） |
| 主前端 | 容器 `4d2d06eca852…`／镜像 `295d3a7244d5…`（2026-10-08 构建） | 当前工作树 114+ 文件源码整体重编译 runtime 镜像（含管理工作台布局与 AGENTS 面板变更） | 未生效 | 同上；node_modules 沿用 company-memory-updater-20261008-r1 只读绑定 |

候选源码提交与文件清单 hash 在提交后补记；构建平台为生产主机 Docker（containerd store），网络隔离 `--network=none`。

## 数据迁移与兼容性

- 迁移：无。新端点只使用既有 `project_agents_files`／`project_agents_file_versions` 表。
- 兼容性核对（2026-10-10 09:54 只读，证据 `.artifacts/agents-template-reinitialize-20261010/backend/current-readonly.json`）：生产 `archive_project_agents_version` 触发器已安装且启用（迁移源码中 CREATE TRIGGER 缺失系仓库脚本陈旧，生产实际存在且引用列均存在）；新代码沿用 `upload_agents` 既有"显式 INSERT 历史行＋files upsert"模式，触发器 ON CONFLICT DO NOTHING 幂等共存；版本表 PK `(project_id,version)`、内容 1–65536 字节检查均满足（模板约 639 字节）。
- 新旧应用数据兼容：部署本身不写业务表；重置端点上线后产生的归档行不回退（同 Key 撤销类不可回退状态）。
- 备份：发布前核对 backup inactive/success、登记 20 服务；本发布不新增备份，运行镜像与证据按惯例归档到 `/srv/smartbrain-backups/backups/agents-template-release-20261010-r1`（非冻结备份/恢复验收）。

## 发布步骤与实际结果

| 顺序 | 目标与前置条件 | 动作及预期结果 | 实际时间、退出码和证据 | 失败或中断处理 |
|---|---|---|---|---|
| 1 | 生产只读预检：目标容器身份/代际、backup 终态、无 pending、edge 双视图、依赖目录存在 | 16:35 核对通过：1025 容器/39 运行；backup inactive/success/MainPID 0/Job 空；无 maintenance.pending；node_modules 依赖与 release_lib 在位；`agents-template-release-20261010-r1` 目录名空闲 | 已完成，本记录预检段 | — |
| 2 | Docker 盘 ≥40 GiB | 当前 39.94 GiB，缺口约 60 MiB，构建后预计再消耗约 0.2–0.3 GiB；须先按授权清理满足门槛 | 待执行 | 门槛不满足不进入构建 |
| 3 | 源码打包 | 本地生成 source.tar.gz＋逐文件 manifest（API 候选 1 文件＋前端全部源文件＋两个 Dockerfile），SHA 固定 | 待执行 | — |
| 4 | 候选构建（双锁、verify_backup==20、AST 函数保留校验） | API 叠加镜像＋候选容器 `/health/ready` 通过；前端隔离编译＋runtime 镜像＋候选容器 `/login` 通过；生产零切换 | 待执行 | 失败保留候选与日志，不切换 |
| 5 | 候选验收 | 候选 API 新路由存在（匿名 401 而非 404）；候选前端脚本含新按钮文案；既有函数 AST 全保留 | 待执行 | — |
| 6 | promote dry-run | 全量断言（代际、systemd 无引用、登记 20、四盘、内存、edge、AGENTS 指纹）通过 | 待执行 | — |
| 7 | promote | 旧容器 restart=no→停止→断网→改名 `-rollback-agents-20261010-r1`；新容器按 clone_config 同配置创建并启动，ready 通过 | 待执行 | 异常按 promote 脚本自动恢复原名称/网络/重启旧容器 |
| 8 | 公网验收 | `/admin` `/wiki` `/login` `/workday` `/health/ready` 200；匿名新路由 401（旧 API 为 404 的前后对照）、匿名 Key/records 401、退休下载 410；公网脚本与容器逐字节一致 | 待执行 | — |
| 9 | 终态观察＋归档 | 无关容器代际保持、旧容器停止保留、backup/登记/edge/四盘复测；新镜像 docker save＋证据 0600 归档并独立 SHA 复核 | 待执行 | — |
| 10 | 文档与镜像 | 本记录补实际、任务/CURRENT 更新并镜像 E 盘逐字节核对；提交推送 | 待执行 | — |

## 发布后验收

| 验收标准 | 实际入口与身份 | 实际结果和时间 | 证据 |
|---|---|---|---|
| 登录和本次业务流程（管理员预览→CAS 重置→版本历史下载） | 公网需真实管理员会话；本轮验收以匿名 401/404 前后对照＋候选容器内自检为准，真实员工闭环操作不代替 | 未执行 | 待填写 |
| 匿名／越权边界 | `GET /v4/projects/{id}/agents/template-preview`、`/agents/versions`、`/agents/versions/{v}/download` 匿名 401；`POST reset-to-template` 匿名 401 | 未执行 | 待填写 |
| 生效版本、绑定与相关服务健康 | 两目标容器新 Id＋新镜像 Id，IP/网络/alias 保持；edge 双视图不变；backup 登记 20 | 未执行 | 待填写 |
| 重启或恢复能力 | 旧容器停止保留，可经名称/网络/重启恢复；不执行整机或数据库恢复 | 未执行 | 待填写 |

## 回退方案

- 触发条件：promote 后 readiness/公网验收失败或代际断言失败；决策负责人：发布负责人（Codex）按现场执行，用户可随时指示回退。
- 回退目标：旧 API 容器 `e6a1a794f833…`（镜像 `8eac15848ae9…`）、旧前端容器 `4d2d06eca852…`（镜像 `295d3a7244d5…`），promote 时改名 `-rollback-agents-20261010-r1` 停止保留；最近可用性核对：16:35 两容器 Running/RestartCount 0。
- 回退层次：应用层——新容器停止改名 `-failed-…`，旧容器恢复原名/原 IP/alias/重启策略并启动，ready 复核；配置层——本次无配置变更；路由/edge——不变更，无需回退；数据库——本次无迁移，部署不写业务表，无需回退（上线后用户主动重置产生的新归档行属业务数据，不随应用回退删除）。
- 旧应用对当前数据兼容：部署本身不写表，旧应用直接读现有表可运行；兼容性以只读指纹前后一致核对。

| 顺序 | 精确目标和前置条件 | 回退动作及预期结果 | 失败或中断处理 |
|---|---|---|---|
| 1 | promote 脚本异常分支自动执行（机制同 conversation-summary r2，已生产实证一次） | 新容器停止改名；旧容器恢复名称/网络/重启策略并启动至 ready；指纹核对 | 记录错误并保留现场，不重复自动重试 |
| 2 | 手动回退（自动失败时） | 按 `promote-rollback` 证据逐容器恢复 | 待填写 |

## 回退验证与实际执行记录

| 类型 | 时间与环境 | 结果 | 证据及局限 |
|---|---|---|---|
| 静态检查／dry-run | 待执行 | 未执行 | 不等于生产实际回退 |
| 生产实际回退 | 未执行 | 未执行 | 未执行则不称恢复演练通过 |

## 收尾

- 实际终态、尚未完成的验收与运行任务：待填写。
- 保留的旧版本、备份、证据及后续清理条件：旧两容器与旧镜像按惯例停止保留；清理需单独授权。
- 任务接续记录与 CURRENT 更新位置：待填写。
