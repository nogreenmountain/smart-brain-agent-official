# 管理工作台视觉刷新任务

状态：AGENTS 入口回归修复已提交、推送并完成生产部署；生产静态资源和入口已复核

范围：保留 2026-10-10 已验收的管理工作台功能，调整前端视觉和布局层级，解决页面堆盒子、浅蓝色块重复和操作区层级不统一问题。

权威源码：`smartbrain-dashboard/app/(with-shell)/admin/page.tsx`、`smartbrain-dashboard/app/globals.css`

计划：`docs/plans/2026-10-11-management-workspace-visual-refresh.md`

核对时间：2026-10-12 13:25（Asia/Shanghai）

## 已完成

- 保留紧凑侧栏＋详情布局、项目搜索/状态筛选、按需创建弹窗、项目详情 tab、成员管理、AGENTS 规则和跨项目审批逻辑；未改 API、状态管理、权限判断、提交处理或路由行为。
- 恢复旧版更清晰的标题层级，使用中性灰蓝底色、白色主卡、轻边框和低强度阴影。
- 将顶部视图切换改为轻量 segmented control；项目列表压缩无效留白，选中项目使用左侧强调线。
- 将详情页指标和统计区域降为辅助信息层；编辑区把“保存”作为主操作，知识库、迁移、恢复作为次级操作，删除使用低强调危险样式。
- 添加稳定的视觉标记 `management-workspace`、`management-metrics`、`management-project-form`、`management-project-actions`，样式限定在管理工作台范围内。

## 验证证据

证据目录：`.artifacts/management-workspace-visual-refresh-20261011/`

- `related-regression.log`：管理页、项目成员、团队目录共 49 项通过。
- `admin-page.test.log`：管理页单测 42 项通过。
- `tsc.log`：`npx tsc --noEmit` 退出码 0。
- `build.log`：`npm run build` 退出码 0；仅保留既有 `PersonalApiKeys.tsx:66` hook dependency warning。
- `browser-qa.log` 与 `built-browser/acceptance.json`：使用重新生成的 `.next` 静态产物完成 1440、1024、375 视口验收；无横向溢出、列表内部滚动、JS 错误为 0，搜索/筛选/创建/详情 tab/审批场景通过。
- `built-browser/desktop-overview.png`、`built-browser/viewport-375.png`：本轮最终桌面和移动端截图。

- 视觉刷新原版本已由 `deec447` 提交并推送；生产发布记录和容量核对已分别保存。
- AGENTS 入口回归修复已在当前分支完成：概览页新增 `AGENTS.md 设置` callout 与 `打开 AGENTS.md 设置` 按钮，继续复用 `AGENTS 规则` tab 和既有 `ProjectAgentsPanel` 操作逻辑；`我的项目` 保持在项目导航第一块，移除详情卡残留 `min-height: 100%`。
- 修复源码提交、推送和生产发布已完成；生产前端容器为 `smartbrain-agentops-dashboard-1`，镜像 `sha256:e2db095017cf968ef60fab937d47b124784cdf2dce51556b488e34d0cfd7fa56`，启动时间 `2026-10-12T05:10:37.195456328Z`，重启次数 0。旧前端以停止回滚容器保留，候选容器以停止证据对象保留。
- 生产 `/login`、`/wiki`、`/admin`、`/workday`、`/health/ready` 为 200；匿名 `/v4/ai-gateway/keys`、`/v4/ai-usage/records` 为 401；`/admin` 引用的 12 个静态脚本逐个与生产容器字节一致，新 chunk 实际包含入口与 callout 文案。

## 边界与未完成

- 管理页与 `ProjectAgentsPanel` 回归共 52 项通过，Next build exit 0；完整前端套件仍保留既有跨运行时 `Blob` 实例断言失败，未修改 AGENTS API。
- fixture 浏览器验收覆盖 desktop overview/AGENTS、1024、375、many-projects，无横向溢出和 JavaScript 错误；这证明本地构建产物，不替代真实成员登录后的点击验收。
- 本轮未使用真实成员账号在生产浏览器中点击项目列表、`AGENTS.md 设置` callout 或初始化/上传/下载操作；生产路由、静态资源和 API 权限边界已核对，真实账号端到端结果仍写“未核对”。
- 生产 API、edge、数据库、权限和 AGENTS 后端未改；旧前端和候选前端均保留，后续清理需另行确认。

证据：`.artifacts/management-workspace-agents-visibility-20261012/`；独立发布记录见 `docs/releases/management-workspace-visual-refresh-20261012-r2.md`。


## 2026-10-12 10:04 生产部署完成

核对时间：2026-10-12 10:04（Asia/Shanghai）。先按双锁和容量门禁清理明确无引用的测试/构建对象，删除 `agentops-test-supabase:latest`、`agentops-test-clickhouse:latest`、`candidate26-builder:local` 三个无引用镜像，并退出三个临时模板测试容器，实际释放 `1,519,050,752` 字节（约 1.42 GiB）。未执行全局 prune，未删除运行中业务容器、日志、备份、ClickHouse parts 或历史证据。

候选构建 `smartbrain-management-workspace-frontend:2026.10.12-r6` 已通过源码 manifest、Next build、候选容器 `/login` `/wiki` `/admin` `/workday` 健康核对，镜像 SHA256 为 `6dc4244535c779ff4ce4ab9ce08f694aee15749732ae10aaae6930a948a6500f`。

生产只切换管理工作台前端：新容器 `smartbrain-agentops-dashboard-1` ID `32aaa12fcdd962589a957d845198db71f9e9185cf020fc7958b0730aebdcb346`，启动时间 `2026-10-12T02:04:44.731853423Z`；旧前端保留为停止回退容器 `smartbrain-agentops-dashboard-rollback-20261012-r2`。API ID `621935d93b37fe1a6a9245307686ee1e0fd4ca8afc4497b914cf4085e3c46227`、edge ID `f72614f0f738bd35815aeb2455dc97df99d06d1dc480e17db70ceeeb66d42e73`、镜像和启动时间均保持。

生产终验：`/login`、`/wiki`、`/admin`、`/workday`、`/health/ready` 均 200；匿名 `/v4/ai-gateway/keys` 与 `/v4/ai-usage/records` 均 401；备份登记服务 20、`maintenance.pending` 不存在。Docker 可用空间 `43,803,082,752` 字节（约 40.8 GiB），`/srv/smartbrain`、`/srv/smartbrain-backups`、`/srv/smartbrain-cold` 和内存门禁通过。

第一次切换尝试在页面服务刚恢复时遇到短暂 502，脚本已自动回退且未留下运行中的新容器；随后重试仅切换前端并通过全部终验。生产真实登录后的成员数据布局未使用测试账号做浏览器操作，保留本地 1440/1024/375 fixture 视觉证据，不能把 fixture 说成真实成员浏览器验收。

## 2026-10-12 AGENTS.md 设置入口回归核对与修复

核对时间：2026-10-12 11:42（Asia/Shanghai）。用户反馈管理工作台的 AGENTS.md 设置模块消失。对比 `e44d2ff^`、`e44d2ff`、`deec447` 与当前源码确认：`ProjectAgentsPanel` 及初始化、上传、下载、版本历史、重新初始化为最新模板和 CAS 覆盖逻辑均未删除；视觉刷新将其从概览页常驻内容调整为详情 tab，导致概览页入口发现性下降。生产静态 chunk 仍包含 AGENTS 逻辑，说明不是后端/API 或组件丢失。

本次最小修复：

- 概览页增加显式 `AGENTS.md 设置` callout，按钮进入既有 `AGENTS 规则` tab；保留旧 tab 文案以兼容现有验收和用户路径。
- `我的项目` 保持在项目导航第一块并使用主视觉标记，项目列表作为次级目录。
- 删除详情卡残留 `min-height: 100%`，避免右侧高度把空白扩散到工作台；未改 API、权限、状态、提交逻辑和 AGENTS 操作组件。

验证证据目录：`.artifacts/management-workspace-agents-visibility-20261012/`。管理页和 `ProjectAgentsPanel` 回归共 52 项通过；Next build exit 0，仅有既有 `PersonalApiKeys.tsx:66` hook dependency warning；fixture QA 的 desktop overview/agents、1024、375、many-projects 均通过，无横向溢出和 JavaScript 错误。截图与 JSON 仅为本地构建 fixture 证据，不代表真实生产登录验收。
