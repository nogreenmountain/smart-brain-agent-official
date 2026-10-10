# 全面验收发现的业务缺陷修复发布

## 发布身份

- 发布编号：full-system-acceptance-fixes-20261008-r1；关联任务full-system-acceptance-20261008。
- 负责人/验证人：本任务Codex。授权来自用户要求全面验收及本对话持续排查修复，不扩展为整机/全生产恢复。
- 范围：主API资料共享volume、MCP摘要过滤与旧资料分块读取；状态：业务修复已发布、范围内已验收，全系统未闭环。
- 记录更新时间2026-10-09 09:43；第一发布完成2026-10-08 22:09，第二发布22:32；最新完整现场核对2026-10-09 09:31（Asia/Shanghai）。

## 发布前后版本

| 组件 | 旧身份 | 实际生效身份 | 行为及证据 |
|---|---|---|---|
| 主API | CID1d84686b2d1807bee1a690cf4ad784acff8ecfcc43532a3f438aebdb09419bff | CIDe6a1a794f8334ffda576f853b34eb6e9c99b70a89c9f785a51b68996fcb7cecb，镜像保持sha256:8eac15848ae9e29080d9deba458d588e572d8b0b1188f8f10dc60040ec41d402 | 新共享资料volume，非API源码镜像升级 |
| MCP第一发布 | CID49ef5f84ecc1323bbd34f3808e609c23b2917f1cceda7b251a2f452e6162a26a，镜像31d781ab… | 中间CID1089374f6f6ff85c6bc253c7bb16bb08bdeff7855dd97001c695d2033c9494a4，镜像sha256:34b95963dc80723ea344e3b5a83377ed79a4e7d264f753d9cf12f3775ed95081 | 内部摘要标记拒绝；后由第二发布替换 |
| MCP第二发布 | 上述中间版本 | CIDa2db22b03758ff0ee5d2a96c21298bef71812285854f18a758acceb9cbdf199b，镜像sha256:74415450172deb1873760fbbc4e824cdcb58eb37783c9a6e6541ff92159fd7fa，tag smartbrain-mcp-material-reader:2026.10.08-r1 | 资料v2优先/legacy兼容，MCP版本1.4.1/插件0.2.1保持 |
| 前端 | 本轮保持 | CID4d2d06eca852aa4d94ec298eafdcfb62b1d850ccfe0711388af66326c70409ac，镜像295d3a7244d5… | 实际网页验收，无新前端发布 |
| 实际read | 本轮保持 | CID5c07fd2651605a93ad8c2e6d63675c485e5d3b73b7687c113d30c261b6a16083，镜像985176d5cbf5… | 个人records读取保持 |

权威源码C盘deb4工作树，分支codex/project-memory-no-adapter、基线431022b，实际未提交源码hash另留本地manifest。此次产品文件`agentops_local/project_memory/conversations.py`、`agentops_local/wiki_mcp/operations.py`，新增真实PG测试`test_material_chunks_compat_pg.py`。共享脏树其他修改不归入本次发布，不整体提交或推送。

## 数据与兼容性

无生产DDL或数据恢复。v2/legacy分块按project+document关联，保留权限/审批/当前版本，避免跨项目回退；未覆盖或移动真实员工对话。API原容器层114字节测试资料在复制到共享volume前逐字节/hash核对；新挂载让两个既有worker读取相同文件，原审批重试完成。

唯一online备份批次`20261008T033252Z`36 SHA通过；Redis隔离恢复通过，PG仅7关键表行数通过，完整PG恢复未通过。不能把证据/镜像留存称为全生产冻结恢复点。

## 实际步骤和结果

| 步骤 | 时间与实际结果 | 证据/失败处理 |
|---|---|---|
| 捕获摘要漏拦截与文件目录不共享 | 10-08 21:40–21:51 | 原业务失败、四Red、主API无共享mount和worker读不到文件证据保留 |
| 第一发布r1 | 10-08晚，实际失败并恢复 | tmp挂载冲突；`fixes-rollback.json`保留，不改写成成功 |
| 第一发布r2 | 10-08 22:08–22:09通过 | 只新增资料volume，保留文件；`fixes-promoted.json`，945其他当时容器保持，edge保持 |
| 第一修复生产复验 | 10-08 22:10，22项/0失败 | `postfix-business-results.json`；旧审批原job完成，会议正文/越权通过 |
| 资料旧分块兼容修复 | 10-08 22:20–22:32，版本diff补验22:37 | 初始5Red→5Green；最新MCP镜像54回归、实际模块import通过，发布后另补实际版本diff SQL，6PG通过 |
| 第二发布 | 10-08 22:32通过 | `material-mcp-promoted.json`；仅MCP切换，957其他当时容器保持、edge保持 |
| 第二生产复验 | 10-08 22:33，18项/0失败 | `material-postfix-results.json`；3块全文、检索/引用、只读与跨项目拒绝、原文件hash |
| 全量收尾 | 10-09 09:29/09:31/09:36 | fixture清理、931基线无关容器保持、真实匿名models401/退休410补验 |

发布脚本及逐次intent/result保存在`.artifacts/full-system-acceptance-20261008`和远端同任务根；本文件记录结果，不能直接作为重放脚本。

## 回退与恢复记录

第一发布r1已实际恢复旧目标；证据`fixes-rollback.json`。r2及第二发布成功后未实际回退。旧镜像/容器与前置配置受控保留；新写入与复制的文件需保留，禁止用数据库回灌或删除共享volume进行应用回退。

后续如需退出，先核对当前CID/image、API volume、compose/backup登记、edge双视图和写入状态，再从受控原配置建立新的退出计划。旧MCP能否继续完整读取新增业务数据、旧API去掉mount后worker行为须重新验证；旧容器存在不等于回退可用。未证明整机重启或全系统恢复。

## 收尾和剩余问题

09:29临时身份清理完成，09:31所有本轮测试/恢复容器停止/no，无需接管运行runner。ClickHouse持续Code241、Docker容量低于40GiB、完整PG恢复、旧tunnel unit生命周期、全writer闭包及实际四模型验收仍待；新发布须先重新满足容量门槛。

完整矩阵见[验收报告](../ops/full-system-acceptance-20261008.md)，任务见[接续记录](../tasks/2026-10-08-full-system-acceptance.md)，状态入口见[CURRENT](../CURRENT.md)。私有原始配置/Key/正文不复制到文档或Git。
