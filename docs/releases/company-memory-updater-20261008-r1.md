# Company Memory 独立更新入口与安装验收

## 发布身份

- 发布编号：company-memory-updater-20261008-r1；关联[任务](../tasks/2026-10-08-company-memory-updater.md)，负责人Codex。
- 用户本对话明确要求持续修复、部署、验收；无额外期限。2026-10-08 18:21已验收；完整现场核对18:18，归档及入口独立复核18:21。
- 影响：主前端Wiki更新入口和精确PS1下载路由；已有Token、后端、数据库、模型入口保持。
- 权威源码：C:/Users/test/.codex/worktrees/deb4/智慧大脑agent - 服务器端；codex/project-memory-no-adapter/431022b加实际source manifest，不整体提交共享脏树。

## 版本与兼容性

| 组件 | 原身份 | 候选身份 | 实际结果 |
|---|---|---|---|
| 主前端 | 3a82c90e5583，image a78a41ab4a39 | smartbrain-company-memory-frontend:2026.10.08-r1，image 5721eff53b7d | 18:13生效7366d9d631ac，原172.18.0.16与HostConfig保持；18:21再次核对 |
| Edge | f72614f0f738，宿主/活动f68aec199bb2 | 只增加精确PS1下载位置；nginx test/reload | 18:13宿主/活动统一c22e68d972ae，原ro挂载和代际保持 |
| 本机Company Memory | 0.1.0+codex.20260810081637 | 0.2.0+codex.20261008 | 17:42实际升级，原Token保持，MCP200/31工具 |

无数据库迁移、生产Token签发/撤销、真实模型请求或备份重跑。更新器固定校验PS1 SHA5110b12dc59e3b178d22e28bffd570b45d03057d3932913fb76c20e319213c31和ZIP SHA37389ef2c0c6a46a62a489e96707be7a087f7ecf3e45af7a7d4308c046b2dbdd；安装失败恢复旧源与版本，旧源保留。新技能需新建Codex聊天/会话加载。

## 发布步骤与回退

1. 专项17项、tsc、真实CLI隔离升级/校验拒绝/失败恢复/桌面CLI回退及候选浏览器通过。完整源码tar/manifest与镜像已固定；保留原缺失静态资源。
2. 构建后容量不足，已先归档本任务临时依赖镜像再移除其成功编译容器；源码bind目录保留。只针对经审计可回收且未共享的缓存及其后继处理，所有容器和镜像身份逐项核对；容量仍须真实达到40/20/250/250GiB和2GiB内存门槛。
3. prepare_release_remote.py核对原主前端、edge宿主与活动inode、20备份登记服务、生命周期引用和候选源码。promote_remote.py先dry-run，再在backup→maintenance双锁下只替换主前端，复用原IP/别名/HostConfig；旧容器停止/no、脱网改名保留。
4. 受控write_active_mount.py更新edge活动ro绑定文件，再原inode同步宿主，nginx test/reload；公网TLS页面、匿名权限、下载SHA验收。失败自动恢复旧edge双视图与原前端网络、名称和restart policy。
5. 发布后浏览器用部署前端+只读合成API验证更新按钮，公网资源逐字节匹配容器，候选和loopback代理收尾；全量未涉及容器配置/代际、backup/timer和容量再次核对。

生产实际回退尚未执行；dry-run和保留旧版本不冒称实际回退演练。镜像/私有证据归档不包含生产数据库，不是冻结备份/恢复合格点。

## 实际验收与收尾

| 验收标准 | 核对时间与结果 | 证据 |
|---|---|---|
| 无需新Token的网页更新 | 18:15部署前端+只读合成API，0 Token时更新启用、初装禁用；下载CMD无Token参数、固定SHA、无JS错误；合成截图不冒称生产登录验收 | browser-deployed.json/png、browser-deployed-download.json |
| 本机升级和MCP可用 | 17:42真实升级、用户/进程Token保持，认证MCP200、服务1.4.0/31工具；record_project_conversation可发现；18:21启用版本0.2.0再次读回 | local-plugin-upgraded.json、local-plugin-final.json |
| 发布身份与公网一致 | 18:14严格TLS Wiki脚本与容器逐字节相同，PS1/ZIP SHA固定，28旧静态资源仍可读 | public-verified.json、promoted.json |
| 原权限/退休入口 | 18:13页面/ready200，匿名Key/records401；18:18四个退休适配器下载410 | promoted.json、final-observation.json |
| 生命周期和其他服务保持 | 18:18共923容器/39运行，920其他既有容器Config/HostConfig/Image/运行/StartedAt/RestartCount保持；主前端原IP和HostConfig保持，无直接systemd引用；候选停止/no、旧前端停止/no且脱网保留；QA代理/SSH与三监听归零 | final-observation.json、frontend-systemd-references.json、qa-closed.json |
| 运维门槛 | 18:18 backup inactive/PID0/Job空/success、timer enabled、登记20服务；全部磁盘和内存门槛通过。18:21Docker43001249792字节，仍≥40GiB | final-observation.json、post-archive-verified.json |

构建r1依赖缓存模式变化导致DNS失败、WinPS模块路径及隔离shim编码失败均保留；后继成功验证分开记录。前三次精确缓存尝试未释放数据，原选择遗漏后继引用；r4补完整13项可回收未共享后继，回收840.1MB缓存逻辑大小但磁盘仍略不足；r5回收两项可重建source.local后实际容量通过。所有922容器和193镜像核对保持，没有整批prune。

归档第一次误把Docker29 OCI index ID与config摘要比较，实际成功导出保留；第二次OCI验证通过后发现服务器缺压缩源包，未完整证据包改名保留。补上传已核对源包后完成，15个OCI descriptor内容hash/size和amd64平台一致，三归档18:21独立SHA核对通过。

归档目录/srv/smartbrain-backups/backups/company-memory-updater-20261008-r1（0600）：frontend-runtime.tar，72312320字节/SHA8e9d6d87c4b99ad9724c00a12ce567235d33bb97cd4c473971ab2ca9be2c1ddc；evidence.private.tar.gz，1575511字节/SHA9efb6bfef89fcf732613b03276e9133aa05e1445639d81056af9e6c3dc42f2b6。原compile-dependencies.tar保留，439334400字节/SHA33043dcc9c1c2b6cdb3493b8dbc0ee5237bcc5627c20026f225ad9405d2b4934。

本次没有生产实际回退，dry-run通过；原容器/镜像和回退脚本保留。全部本任务runner终态，无待接管运行任务。不重放升级、构建、缓存清理、发布、收尾及归档。已有聊天仍加载旧技能快照，用户新建聊天是客户端加载步骤，无需关闭正在工作的桌面端。

## 证据

本地.artifacts/company-memory-updater-20261008；远端/srv/smartbrain/releases/company-memory-updater-20261008-r1/evidence。私有配置/Token/完整inspect不进入公开文档。

关联[CURRENT](../CURRENT.md)。本任务验收已完成；旧运维、主机恢复和历史17项不因本次发布完成。没有Git提交/推送，共享脏树保留；仅本任务文档同步E盘，未覆盖E盘源码。
