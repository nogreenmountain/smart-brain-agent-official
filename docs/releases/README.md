# 发布记录索引

本目录保存按 [发布模板](../templates/release.md) 建立的新记录。现有 `docs/ops` 历史发布文档继续保留；本索引不证明当前生产状态或回退目标可用性。

## 新发布

本记录机制建立时增加的[2026-10-08 版本与恢复基线](server-baseline-20261008.md)为历史只读观察。以下登记后续实际发布，并同步 [CURRENT](../CURRENT.md)。

| 发布编号 | 关联任务 | 环境与范围 | 实际终态 | 现场核对时间 | 记录 |
|---|---|---|---|---|---|
| agents-template-release-20261010-r1 | agents-template-reinitialize-20261010／management-workspace-layout-20261010 | 主API新增4条agents模板路由／主前端重新初始化面板与紧凑布局 | 成功；promote/公网/终态/归档通过，1023无关容器代际保持，backup 20 | 2026-10-10 17:15–17:16 | [实际记录](agents-template-release-20261010-r1.md) |
| personal-proxy-concurrency-20261009-r2 | personal-proxy-concurrency-20261009 | 个人代理三源短事务/有界队列；同一current unit与writer补充清单 | r1实际恢复、r2成功；34项实际镜像/HTTP+PG及生产只读权限通过，归档独立复核完成 | 2026-10-09 12:17 | [r2实际记录](personal-proxy-concurrency-20261009-r2.md)／[r1失败恢复](personal-proxy-concurrency-20261009-r1.md) |
| full-system-acceptance-fixes-20261008-r1 | full-system-acceptance-20261008 | 主API资料共享volume/MCP摘要过滤及旧资料读取 | r1实际恢复、r2和第二MCP发布成功；业务22/资料18复验通过，全系统未闭环 | 2026-10-09 09:31/09:36 | [实际记录](full-system-acceptance-fixes-20261008-r1.md) |
| conversation-summary-stats-20261008-r1 | conversation-summary-stats-20261008 | API/MCP/主前端/新项目默认v4；本机0.2.1 | r1恢复、r2成功，公网/MCP/浏览器验收及归档复核通过 | 2026-10-08 20:13 | [实际记录](conversation-summary-stats-20261008-r1.md) |
| company-memory-updater-20261008-r1 | company-memory-updater-20261008 | 主前端更新入口/精确PS1路由；本机插件升级 | 公网资源/部署浏览器及本机版本验收通过，归档完成 | 2026-10-08 18:21 | [实际记录](company-memory-updater-20261008-r1.md) |
| project-memory-no-adapter-20261008-r1 | project-memory-no-adapter-20261008 | 生产API/MCP/主前端/插件包/迁移/备份修复 | 发布与公网/浏览器验收通过，备份success | 2026-10-08 13:00 | [实际记录](project-memory-no-adapter-20261008-r1.md) |

## 已有历史资料

| 记录日期 | 范围 | 资料 | 当前适用性 |
|---|---|---|---|
| 2026-09-20 | 个人单 Key 发布及回退 | [原发布记录](../ops/personal-one-api-key-release-20260920.md) | 历史记录，回退前重新核对目标及兼容性 |
| 2026-09-22 13:45 | 多组件版本与待发布补丁 | [原状态快照](../ops/current-version-status-20260922.md) | 历史快照，不替代新发布清单 |

- 2026-10-08 17:02：[AI工作台正文与滚动实际发布](ai-workspace-records-scroll-20261008-r1.md)；r1实际回退、r2成功，权限/资源/浏览器通过。
