# AI 工作台记录与管理工作台滚动修复

- 任务：ai-workspace-records-scroll-20261008；负责人：当前 Codex。
- 接续对话：01a11921-7ab3-7c41-a11b-3ea741e99c46。授权为用户原修复部署请求及明确接续，范围限记录滚动、个人正文展示、负责人管理页成员与审批滚动。
- 更新：2026-10-08 17:16（Asia/Shanghai）；完整发布验收核对17:02，归档及服务/公网入口窄核对17:16。
- 开发阶段：已验证；部署范围：生产。
- 权威源码：C:/Users/test/.codex/worktrees/deb4/智慧大脑agent - 服务器端；codex/project-memory-no-adapter / 431022b。E 盘旧源码不覆盖该目录。
- 本任务和先前 company-memory/AGENTS/备份任务共享脏工作树，未提交、未推送；不整体提交。文件身份见 .artifacts/ai-workspace-records-scroll-20261008/source-manifest-final.json。
- [实际发布与回退记录](../releases/ai-workspace-records-scroll-20261008-r1.md)。

## 完成结果

| 验收标准 | 17:02 实际结果 | 证据 |
|---|---|---|
| 工作记录滚轮 | tabpanel 为唯一页面纵向滚动根，嵌入式 main overflow-visible；普通滚动 617→1337 | production-browser-acceptance.json、production-records-cleaned.png |
| 正文只显示对话 | 12 条合成会话、24 条 user/assistant 消息清理；环境块、speaker 包装与 system/tool 不展示；原库正文不清洗 | read-backend-red.log、read-backend-green.log、release-acceptance-r2.json |
| 负责人/普通成员 | 负责人成员内部滚动 0、审批原限高容器 0；普通成员只读；JS error 0 | browser-acceptance.json、production-browser-acceptance.json |
| 实际入口生效 | /workday 新精确位置指向修复后的主前端；/admin 原地址保持；20 次公网 script 字节与新容器相同；7 个旧文件 SHA 匹配 | release-acceptance-r2.json |
| 权限、绑定 | 登记成员 options/records 200；匿名记录/Key 401；未登记合成成员 records 403；26 人白名单保持；read unit 新 CID、备份登记 20 项 | release-acceptance-r2.json、final-observation-r2.json |

独立项目列表和 AGENTS 文本预览仍保留有意的限高滚动。本次移除成员/审批区域的嵌套滚动。浏览器经 loopback SSH 连接部署容器及合成数据；公网 HTML/script 字节、登记成员 cookie HTTP 另行严格 TLS 核对，没有为合成成员扩大公网权限。

## 源码和验证

主 API ai_usage.py、对应后端测试；AIWorkspacePage.tsx、workday/legacy-page.tsx、admin/page.tsx、ProjectMembersPanel.tsx 及测试。实际 read 服务源码不同，以当时镜像为底仅替换 _attach_messages 并加入清理 helper，独立 AST 核对其余节点保持；runtime SHA 4e4971d232108d1671eeea5bffdecb0e80206c6a977e02683ee8312c4db2c138。

| 时间 | 检查 | 结果 |
|---|---|---|
| 16:28 | Windows Vitest 四个相关文件 | 41 项通过；不是完整目录 |
| 16:31 | 主 API 生产依赖候选 | 8 项通过；runner 首次 future-import、第二次 discovery 错误保留，r3 正常执行 |
| 16:33–16:37 | 实际 read 旧版/候选 | 新清理测试旧版失败；候选 8 项通过、/health 200 |
| 16:54 | 发布异步启动等待 | 2 项红→绿；未运行必须超时拒绝 |
| 16:59–17:00 | 公网及浏览器 | 资源、权限、滚轮、正文、负责人和普通成员通过 |
| 17:02 | 最终现场 | 921 容器/39 运行；911 个其余既有容器配置/代际保持；4 个候选停止/no；Docker 约40.49 GiB 可用 |

Python 编译、git diff --check 通过。没有生产 DDL、Key 变更、真实模型调用、备份重跑，不称完整平台回归、整机恢复或原17项完成。

## 失败、恢复与终态

- 原对话 15:13 首次前端构建缺 Dockerfile，15:19 已补建成功；本次没有重新编译成功前端。
- 实际 read 第一次 build 将 Image ID 当作 FROM 名称，触发 metadata 查询；仅终止确切失败 build，以本地固定 tag 的 r2 成功，旧日志保留。
- 16:49 发布操作 r1 的 readiness 在 systemd 异步启动完成前误判退出，触发实际回退。原三 CID/配置/网络/unit/可用性均恢复；read 初次恢复检查也提前报错，16:54 独立确认真正恢复成功。保留 promote-rollback-resumed.json 的 read error 与 promote-rollback-confirmed-r1.json，不改写历史。
- 16:55 独立操作 r2 成功；旧镜像/容器与 r1 失败现场保留，r2 未实际回退。
- 验证脚本曾遗漏管理员 employee_id 得到422；另一次从 internal read 容器请求公网失败，修正为主机严格TLS核对。没有改变权限、网络或产品规则。
- 17:02 两个合成账号停用、两个项目结项、12条合成记录标记并保留，临时 session、Windows代理/SSH关闭；4候选停止。无本任务运行中的 runner，归档结果另见发布记录。
- 17:09:56镜像及私有证据归档完成；17:16重新计算两文件SHA、tar目录及三个OCI镜像身份通过。目录/srv/smartbrain-backups/backups/ai-workspace-records-scroll-20261008-r1，大小/SHA见发布记录；清单archive-manifest.json和独立证据archive-closeout-verification.json已保存本地。不含生产数据库快照，没有恢复验证，不是冻结备份合格点。
- 17:16窄只读核对三个CID/Image/Running、read unit、edge双视图和backup终态保持；严格TLS ready/login/workday/admin 200、匿名records 401。首次归档检查脚本使用错误Image ID口径的失败及诊断保留，修正为OCI身份链后通过，未修改归档。

证据在本地 .artifacts/ai-workspace-records-scroll-20261008/ 和远端 /srv/smartbrain/releases/ai-workspace-records-scroll-20261008-r1/evidence。完整配置、cookie、员工正文不提交或公开。

## 下一步与不可重跑

用户刷新网页使用。接续先读实际终态，不重放 build、promote、fixture 创建/关闭或历史模型批次。若回退，核对 r2 当前 CID、unit、edge 双视图后恢复本次保存的旧版本；不使用旧任务发布器。其他运维及原17项需独立授权与核对。
