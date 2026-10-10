# AGENTS.md + company-memory 生产发布记录

关联任务：project-memory-no-adapter-20261008。用户已授权修复并部署。2026-10-08 12:46–12:49 切换完成，13:00 收尾核对通过（Asia/Shanghai）。

网页桌面适配器模块、端口/检测、启动器及下载入口已撤下。项目记录改用 AGENTS.md + company-memory；真实公网与浏览器验收通过。备份失败已修复，唯一新 online 批次成功完成。

## 实际生效版本

| 组件 | 生产容器 ID 前缀 | 镜像 ID 前缀 | 生效内容 |
|---|---|---|---|
| 主 API | 54d26ce78322 | 3d2c644644ce | 默认 AGENTS 模板 v3（精简版，约 639 UTF-8 字节/8 行）；继承原确切 API 镜像，其余模块保持 |
| MCP | 7a0f4bc5bf52 | 3292f4518fc0 | 服务 1.4.0，原 30 工具保留，新增 record_project_conversation |
| 主前端 | cf85e07c0b98 | a0b5f09c955a | 模块/检测/旧下载退出，AGENTS 初始化、上传、下载保留 |
| 插件安装包 | 下载已更新 | SHA 37389ef2c0c6… | 0.2.0+codex.20261008；用户客户端尚未代为升级 |
| 数据库 | 原主 PostgreSQL | 不重建容器 | 三个加法/触发器修复迁移；后续精简模板迁移 20261008003000，既有 141 个 AGENTS 文件逐行摘要保持 |
| Edge | f72614f0f738 | 原镜像保持 | 四个精确退休地址 410/no-store，插件包路由更新；nginx test/reload 通过 |

镜像标签依次为 smartbrain-memory-api、smartbrain-memory-mcp、smartbrain-memory-frontend:2026.10.08-r1。工作树 codex/project-memory-no-adapter，基线 431022b；本轮未提交或推送。MCP 以实际运行源码为权威合并，避免旧本地源码覆盖既有资料接口；活动五个 Python 文件 SHA 已逐一核对。

旧 workday 前端、个人模型入口、数据库、Redis、隧道及其 systemd 绑定保持。三个目标旧容器停止、restart=no、断开网络后保留，三个 readiness 验证容器也停止保留。新容器复用原准确 IP/aliases 和生命周期策略，没有套用旧发布器或绑定其他 legacy unit。

## 备份与数据修复

原备份失败点为 ai-worklog-worker 配置漂移：备份 Compose 漏掉 9/24 热补丁。11:32 纳入准确 environment/volumes 和三个外部脚本的可恢复来源，保留漂移校验；本次新批次 20261008T033252Z 已成功，36 个 SHA256SUMS 文件全部通过，外部源码归档独立重验通过。

备份路径：`/srv/smartbrain-backups/backups/20261008T033252Z`；Invocation 0326a849cecd433e8d35567e31545b07。收尾服务 inactive/Result=success/MainPID=0/ControlPID=0/Job 空，timer enabled。没有重跑既有失败批次。

新增 MCP 切换后同步备份 Compose/image lock；旧 MCP 仅在确切 ID、已停止、restart=no、配置身份保持且唯一替代活动容器匹配时才能归档排除。规则 7 项测试及真实登记 20 服务 hash/镜像校验通过，未绕过 guard。

迁移前两张对话表各 0 行，独立 dump 已在隔离 PG 恢复并验证候选迁移；依赖外键表使用 stub，范围仅这两张空表。生产迁移：

- 20261008000000：company-memory 来源、提交幂等及兼容字段。
- 20261008001000：新项目默认规则保留原公司模板并附当前提交协议；补初始化与版本归档缺失的 SHA。
- 20261008002000：版本归档与 API 已插入版本幂等协作，同版本不同正文明确拒绝。

后两项来自真实验收发现的生产遗留故障：新账号默认项目创建违反 SHA 非空约束、上传文件与归档触发器重复插入同一版本。真实 PG rollback-only 红/绿验证包含创建、上传去重与冲突拒绝；安装只修改两个触发器函数，未覆盖旧文件或版本历史。

## 验收证据

- 后端 70 项，其中隔离真实 PG 12；前端 40 文件/177 项、tsc、Linux Node 20.19.4 / Next 15.5.23 build 通过。
- 严格 TLS：login/profile/workday/ready 200，匿名个人 Key/模型 401；四个旧下载 GET/HEAD 共 8 项 410/no-store；公网插件 ZIP SHA/版本匹配。
- 非管理员合成成员使用真实会话及 MCP bearer：31 工具发现、选定对话保存、同编号重试仅一条、身份/时间由服务端给出、unknown Token、额外字段/内容冲突/非成员/只读 scope 拒绝、ledger 与 Wiki 统计一致。
- 实际 Edge 浏览器登录：页面无适配器模块，无 localhost/127.0.0.1/检测请求；AGENTS 上传后正文与版本读回、下载按钮正常，无 JavaScript 错误。
- 测试结束撤销两个令牌、失效会话、停用合成账号并完成两个合成项目；再次公网访问均 401。合成记录/Wiki 证据保留，真实模型请求 0。
- 最终 908 容器/38 运行，899 个非本次切换容器完整配置/镜像/启动代际保持；原 141 个 AGENTS 文件摘要与版本保持。Docker 约 40.98 GiB 可用。
- Edge 宿主与实际挂载 SHA 同为 bca45b5caae5a7c53a95bc4e835b1e156a9a4baa1283e96b94e67ff2f5b65599。两个 inode 不同，分别更新/核对；原实际 mount 为 rw，收尾按 Docker 声明恢复 ro，无容器重启。

私有证据目录：`/srv/smartbrain/releases/project-memory-no-adapter-20261008-r1/evidence`。包括 promoted、edge-applied、new-backup-verified、public-acceptance、browser-acceptance、两次触发器修复、final-observation、rollback-dry-run 和 release-archive 报告；本地 `.artifacts/project-memory-no-adapter-20261008/` 保留失败及成功日志。凭据、完整配置、公司模板和原始正文不进入 Git。

## 回退与归档

本次准确旧容器/镜像/配置保留；回退 dry-run 已通过。没有实际回退。应用回退保留新数据库列、对话/Wiki/版本数据，旧下载继续关闭，不做 down migration 或整库恢复。修复函数安装前定义保存在私有证据中。

发布归档：`/srv/smartbrain-backups/backups/project-memory-release-20261008-r1`。本次 v3 精简模板的增量镜像/源码/证据归档：`/srv/smartbrain-backups/backups/project-agents-short-20261008-r1`。，目录 0700/文件 0600。

| 文件 | 字节 | SHA256 |
|---|---:|---|
| application-images.tar.gz | 435732561 | 9fe2c065cb041994abce4d5335b6a73402a0f173d526c0b6e18d2d63aec756b6 |
| evidence.private.tar.gz | 1222528 | d73c655e00d5de0a49c4b7994a2e60c64994809cbff9bdeebd13cbc9d867af15 |
| release-source.tar.gz | 56150155 | 833179ad64233073a2da3a427188c017c6bd2affa858acaa0a524db417594e38 |

这些是在线备份、有限表恢复验证与发布归档，不是整机冻结备份/完整恢复资格点；原 17 项完整维护门禁未因此完成。

成员需升级/重新连接 company-memory 后核对新工具。已有项目 AGENTS.md 不自动覆盖，负责人须确认并分发当前项目 UUID 与提交协议。记录范围是授权选择的对话；模型名称为客户端声明，用量未知，不保证自动捕获全部聊天。详见[使用说明](../project-conversation-company-memory.md)。
