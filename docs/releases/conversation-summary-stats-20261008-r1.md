# 对话上传统计与简短提交实际发布

关联[任务](../tasks/2026-10-08-conversation-summary-stats.md)和[计划](../plans/2026-10-08-conversation-summary-stats.md)。用户授权持续修复、发布与验收。20:06:53 r2切换成功，20:10完整现场、20:13归档及公网复核通过（2026-10-08 Asia/Shanghai）。权威源码在C盘deb4工作树，未整体提交共享脏树。

## 行为与数据

PROJECT PROFILE改“对话上传统计”，计全部已保存项目对话，Wiki失败不漏计，幂等重试一条；新conversation-upload-stats路由，旧路径兼容。提交最多两条有序user/assistant摘要，300/600字符，标题120、task_result300、payload6000 UTF-8字节；超限与已识别内部封装拒绝，不截断。插件只从可见请求与FINAL结果选取几句话，禁止思考/进度/工具/环境等内容。服务端不能靠正则可靠判定任意未标记内部文字，不冒称任意内容分类完备。

MCP1.4.1、Company Memory0.2.1+codex.20261008。只替换initialize_project_agents新默认函数为v4，真实PG回滚事务与API模板逐字节一致，生产既有AGENTS指纹不变；不改表/RLS，不改写历史正文。只读认证工具发现通过，没有本轮员工对话提交、模型调用或Token轮换。

## 实际版本

| 服务 | 新容器 | 新镜像 |
|---|---|---|
| API | 1d84686b2d1807bee1a690cf4ad784acff8ecfcc43532a3f438aebdb09419bff | sha256:8eac15848ae9e29080d9deba458d588e572d8b0b1188f8f10dc60040ec41d402 |
| MCP | 49ef5f84ecc1323bbd34f3808e609c23b2917f1cceda7b251a2f452e6162a26a | sha256:31d781ab868bcf8c52203e9598145f8eec7d6104f675b83742e1709cd5ca4554 |
| 主前端 | 4d2d06eca852aa4d94ec298eafdcfb62b1d850ccfe0711388af66326c70409ac | sha256:295d3a7244d555ca1c531beee7eb5729423da5d12f7ea6c509d0f48db598bdaa |

原API878ec68ec20e、MCP3292f4518fc0、前端5721eff53b7d镜像及容器停止保留。原IP172.18.0.10/.15/.16、网络、HostConfig、环境与账号保持。edge未修改，宿主/活动SHA c22e68d972aeb997dbf5328dd00ca1de968fabe7455e4b8eb23037d28ed78626。

ZIP5098字节/SHA b7542ddc8d1e34a78a9836081f75520a5340ad9885eeb3d39c7fdf13138d7182；PS17977字节/SHA a29dbf9f42c2d87f4fe7e4f5457d02997a9433ab3aa2b1191d81ad166219a2f7。公网逐字节与运行前端相同，本机升级并核对缓存技能、启用版本及原Token保持；新聊天加载新版。

## 失败、恢复与验收

- r1切换后backup登记拒绝重复wiki-mcp：保留旧Compose标记容器未追加精确归档条目。三原容器已自动恢复；默认函数回退因pg_get_functiondef末尾无分号失败，20:06独立补分号恢复并逐字节核对。失败证据保留，不掩盖为一次成功。
- r2新操作在backup→maintenance双锁下执行，精确核对恢复后的目标代际；同步backup Compose的MCP镜像、images.lock、真实config-hash/image标签，追加停止旧MCP及r1失败MCP的精确归档登记。原政策条目保留，20登记服务校验通过。r2 rollback路径具备原容器/函数/登记恢复，本轮未实际触发r2回退。
- 63后端（含真实隔离PG14项）、51前端、tsc/py_compile通过，15既有SQLAlchemy hstore注册告警保留；构建已有Stripe配置/hook lint告警保留。实际MCP库和隔离合成身份保存/幂等/scope/extra字段/think拒绝通过，生产认证发现1.4.1/31工具/schema2通过。
- 公网admin/wiki/login/workday/ready200，匿名新统计/Key/records401，退休下载410。11管理页脚本、新标题/路由与部署直接入口一致；Wiki资源、PS1/ZIP、35旧静态资源通过。已部署前端加合成只读API浏览器验证统计3、比例66.7/33.3和短摘要指引，无JS错误；不称真实员工生产登录/上传闭环。
- 20:10现场933容器/39运行，920原无关容器Config/HostConfig/Image/Running/StartedAt/RestartCount保持。三候选和编译容器停止/no，四临时监听归零。backup inactive/PID0/Job空/success，timer enabled，登记20服务；原40/20/250/250GiB与2GiB内存门槛通过。无备份重跑，原17项未重新放行。

## 归档与接续

20:11归档完成，20:13四文件SHA/0600、三运行服务、edge、登记及公网独立复核。目录/srv/smartbrain-backups/backups/conversation-summary-stats-20261008-r1，OCI index身份及API28/MCP18/前端15 descriptor内容SHA/size/Linux amd64通过。

| 文件 | 字节 | SHA256 |
|---|---|---|
| api-runtime.tar | 192720384 | 658906b085ff27295dc27f03c70fd9bcd10028e56383be2c73f9ac9a0b794ffe |
| mcp-runtime.tar | 192393216 | a21e20ec45a95b42d11a383146407b3ce538829965effb99b2ac9851816cbcf1 |
| frontend-runtime.tar | 72350720 | 757a01586eb34770344acefac0b10bec9c4c876a035b1420a4c07ab18d96ea50 |
| evidence.private.tar.gz | 1834730 | 9be8887accca5c5a650c2fb9017b2a637b23581ab0e18c6373b549520aaa7c40 |

这是运行镜像/源码/私有证据归档，不含生产DB，不能称冻结备份或恢复验收。源码包121文件SHA b49244bb90c2677ad903e53029edcf5e2d886fba0ba5b4d1c42399441a05addb；20:13本地逐文件身份相同。证据在.artifacts/conversation-summary-stats-20261008及远端同名release/evidence，完整配置/SQL保密。

所有runner终态，不重放发布/升级/归档。未来回退须重新核对当前三容器、edge和登记及授权，不能直接执行历史脚本。已有AGENTS和旧对话不自动改写。
