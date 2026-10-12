# 管理工作台 AGENTS 入口回归修复发布记录

## 发布身份

- 发布编号／关联任务：`management-workspace-visual-refresh-20261012-r2` / `docs/tasks/2026-10-11-management-workspace-visual-refresh.md`
- 发布负责人／验证人：Codex（生产只读核对）
- 目标环境与精确对象：生产 `smartbrain-agentops-dashboard-1`，仅管理工作台前端
- 授权来源、范围和有效期：用户已授权“提交、推送、部署生产，然后核对”；本次只涉及前端入口发现性和布局，不扩展到 API、数据库、权限或 AGENTS 后端
- 状态：已验收（生产静态资源与入口核对）；真实成员登录后的浏览器点击仍未核对
- 记录更新时间／最后现场核对时间：2026-10-12 13:25（Asia/Shanghai）
- 预期行为：管理工作台概览页明确显示 `AGENTS.md 设置`，按钮打开既有 `AGENTS 规则` 设置 tab；既有初始化、上传、下载、版本历史、重新初始化和 CAS 冲突流程保持可用

## 发布前后版本清单

| 组件 | 旧版本与身份 | 候选版本与身份 | 实际生效版本与核对时间 | 源码和构建证据 |
|---|---|---|---|---|
| 管理工作台前端 | `smartbrain-agentops-dashboard-rollback-agents-visibility-20261012-r1`，镜像 `sha256:6dc4244535c779ff4ce4ab9ce08f694aee15749732ae10aaae6930a948a6500f`，停止保留 | `smartbrain-management-workspace-frontend-agents-visibility-candidate-kept-20261012-r1`，镜像 `sha256:e2db095017cf968ef60fab937d47b124784cdf2dce51556b488e34d0cfd7fa56`，停止保留 | `smartbrain-agentops-dashboard-1`，容器 `566de53e9ff3aa963883f2faaaa60ad24aaa39cbbdf771dad7fd7ef0a3269233`，镜像 `sha256:e2db095017cf968ef60fab937d47b124784cdf2dce51556b488e34d0cfd7fa56`，`StartedAt=2026-10-12T05:10:37.195456328Z`，`RestartCount=0`；2026-10-12 13:23 复核 | 候选源码归档 SHA `f19cc72c7ab3e7c343d7803c7967712092eb9e653bbe7253b36f0456b7e32e9f`，115 文件；源码清单中 `admin/page.tsx` SHA `e755726d16a0d680dd539b88cd5c02defa57a8f05f41fe6f2153a6e83a61d32c`、`globals.css` SHA `7531a719f8247ac25a46e39c31a8111489b0454e260eceb15853676f4f2ecaf2` |
| API | `smartbrain-api-20260923-filter-internal-r1`，容器 `621935d93b37fe1a6a9245307686ee1e0fd4ca8afc4497b914cf4085e3c46227` | 未变更 | 同旧版本；镜像 `sha256:aa31ae74b5efa668c13bd617d717b8b7e17f5c62eeee39f5ba8296506a1f32d2`，启动时间保持；2026-10-12 13:23 复核 | 本次无 API/数据库变更 |
| Edge | `smartbrain-edge-1`，容器 `f72614f0f738bd35815aeb2455dc97df99d06d1dc480e17db70ceeeb66d42e73` | 未变更 | 同旧版本；镜像 `sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10`，启动时间保持；2026-10-12 13:23 复核 | 本次无 edge 配置变更 |

## 数据迁移与兼容性

- 无数据库迁移、DDL、路由、权限、Key 或 AGENTS 后端变更。
- 生产新旧前端共用现有 API 合约和 AGENTS 操作接口；既有 `ProjectAgentsPanel` 功能未重写。
- 生产备份登记服务数 20，`maintenance.pending` 不存在；本次仅记录发布证据，没有执行数据库恢复。

## 发布步骤与实际结果

| 顺序 | 目标与前置条件 | 动作及预期结果 | 实际时间、退出码和证据 | 失败或中断处理 |
|---|---|---|---|---|
| 1 | 管理页和 AGENTS 面板回归通过 | 运行管理页专项测试和 AGENTS 面板测试 | 52 passed；`.artifacts/management-workspace-agents-visibility-20261012/frontend-regression.log` | 既有完整套件 Blob 断言失败保留，未改 API |
| 2 | 前端源码清单和构建环境固定 | 执行 Next production build，生成候选镜像 | build exit 0；镜像 `sha256:e2db095017cf968ef60fab937d47b124784cdf2dce51556b488e34d0cfd7fa56`；`candidate-verified.json` | 仅有既有 hook dependency warning |
| 3 | 生产前容量、备份和维护门禁通过 | 核对 Docker、三处数据盘、MemAvailable、backup registration、`maintenance.pending` | 候选记录：Docker `43,598,499,840` 字节、`/srv/smartbrain` `33,306,923,008` 字节、backups `458,929,553,408` 字节、cold `271,934,038,016` 字节、MemAvailable `8,313,225,216` 字节；backup services 20；通过 | 未执行全局 prune、日志删除、历史容器删除或 ClickHouse parts 清理 |
| 4 | 只切换前端并保留回滚对象 | 停止旧前端、改名为回滚容器、启动新镜像 | promote exit 0；生产新容器和回滚容器身份已保存于 `promoted.json` | 首次尝试因候选容器仍运行而安全中止；仅停止该候选后重试，未影响生产 |
| 5 | 发布后核对入口、静态资源和权限边界 | 请求页面、匿名接口，逐个比较 HTML 引用脚本与容器文件 | `/login` `/wiki` `/admin` `/workday` `/health/ready`=200；匿名 keys/records=401；12 个 admin 脚本均 200 且与容器字节一致；新 chunk 标记存在 | HTML 不含客户端文案属预期，文案在客户端 chunk；真实登录浏览器未执行 |

## 发布后验收

| 验收标准 | 实际入口与身份 | 实际结果和时间 | 证据 |
|---|---|---|---|
| 管理页入口可发现 | 生产 `/admin` 与 `8-d9836e37508df5e5.js` | 新 chunk 200，包含 `AGENTS.md 设置`、`打开 AGENTS.md 设置`、`AGENTS 规则`、`agents-settings-callout`；2026-10-12 13:25 | `closeout-public-assets.json`、`closeout-markers.json` |
| 生产静态资源完整 | `/admin` HTML 引用的 12 个脚本 | 12/12 200，12/12 与容器字节一致；2026-10-12 13:25 | `closeout-public-assets.json` |
| 页面与权限边界 | edge → frontend/API | 页面五路 200；匿名 keys/records 401；2026-10-12 13:23 | `closeout-production-readback.jsonl` |
| 本地功能与布局 | 构建产物 fixture，1440/1024/375/many-projects | 52 项管理/AGENTS 测试通过；fixture 无横向溢出、JS 错误为 0；不替代真实账号验收 | `frontend-regression.log`、`fixture-acceptance.json`、PNG 截图 |
| API、edge、回滚对象 | 生产容器身份 | API/edge 指纹未变；旧前端和候选前端停止保留；2026-10-12 13:23 | `closeout-production-readback.jsonl` |

## 回退方案

- 触发条件：新前端 `/admin` 或相关公共入口持续异常、静态资源不一致、或真实业务回归；由发布负责人确认后执行。
- 回退目标：停止 `smartbrain-agentops-dashboard-1`，恢复停止保留的 `smartbrain-agentops-dashboard-rollback-agents-visibility-20261012-r1`（实际名称为 `...20261012-r1`）并恢复原网络与重启策略；不回退 API 或数据库。
- 生产实际回退：未执行；旧前端仍停止保留。
- 回退后必须重新核对五个页面、匿名 401、前端静态资源一致性、API/edge 身份和新增数据不受影响。

## 收尾

- 当前生产前端运行本次 AGENTS 入口修复；API、edge 和数据层未改。
- 证据目录：`.artifacts/management-workspace-agents-visibility-20261012/`；远端归档目录为 `/srv/smartbrain-backups/backups/management-workspace-agents-visibility-20261012-r1/`，不公开私有配置或员工内容。
- 真实成员登录后的项目列表、callout 点击和 AGENTS 操作闭环未核对；后续若要补做，需单独使用授权账号并记录实际结果。
- 任务和 CURRENT 已更新；仅本次相关文件纳入 Git，其他 dirty 工作树改动不纳入。
