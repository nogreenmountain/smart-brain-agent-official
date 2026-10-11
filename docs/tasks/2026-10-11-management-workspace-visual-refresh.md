# 管理工作台视觉刷新任务

状态：已提交并推送；生产部署被容量门禁阻断

范围：保留 2026-10-10 已验收的管理工作台功能，调整前端视觉和布局层级，解决页面堆盒子、浅蓝色块重复和操作区层级不统一问题。

权威源码：`smartbrain-dashboard/app/(with-shell)/admin/page.tsx`、`smartbrain-dashboard/app/globals.css`

计划：`docs/plans/2026-10-11-management-workspace-visual-refresh.md`

核对时间：2026-10-11 13:12（Asia/Shanghai）

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

## 未完成

- 已提交并推送：源码提交 `deec447`，发布记录提交 `46d0112`，分支 `official/codex/project-memory-no-adapter`。生产仍未部署；18:05–18:06（Asia/Shanghai）重核 Docker 可用空间约 `39.82 GiB`，低于 40 GiB 硬储备线，生产页面保持上一版本。
- 浏览器证据使用合成 fixture，只证明本地构建产物的布局与交互回归，不替代真实成员数据和生产验收。
