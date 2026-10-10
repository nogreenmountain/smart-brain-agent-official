# 个人 API 使用记录增量化任务接续记录

## 任务身份与范围

- 任务编号：personal-api-incremental-records-20261010
- 负责人／集成负责人：Codex（用户 2026-10-10 晚授权全流程自主完成，中途不停下提问）
- 创建／更新时间：2026-10-10 19:30 +08:00（红绿验证完成后 19:25 更新；20:10 发布后收尾更新）
- 开发阶段：已完成（19:45:48 promote 生产、20:01:43 终验、20:03:49 归档、20:07:05 复核通过）
- 部署范围：smartbrain-prod personal-key-api 服务单文件叠加发布
- 目标及可观察的验收标准：个人 API 每条使用记录只含本轮提示与本轮回答（增量尾部），不再打包整段聊天历史；知识库/对话记录存储流程不变；后端测试全绿；生产发布后经公网真实请求验证
- 本轮授权范围、来源、期限：用户 2026-10-10 指令"复现→方案→开工→测试→提交→推送→部署生产，不要让我回答问题"
- 前置依赖／相关任务：agents-template-release-20261010-r1（同日已发布，流程复用）；request-project-attribution-20261009（个人代理现状来源）
- 方案文档：docs/plans/2026-10-10-personal-api-incremental-records.md

## 代码与版本

- 权威源码目录：C:\Users\test\.codex\worktrees\deb4\智慧大脑agent - 服务器端
- 工作目录／分支／基线提交：同上，codex/project-memory-no-adapter，基线 603ce51
- 本任务变更文件：agentops_local/api/personal_gateway_proxy.py、agentops_local/tests/test_personal_gateway_proxy.py、deploy/personal-api-incremental-records/Dockerfile.personal-api（新增）
- 本任务未提交修改及保存方式：实施完成后提交推送 official；artifacts 在 .artifacts/personal-api-incremental-records-20261010/
- 既有其他任务修改：无（工作树干净，git status 2026-10-10 19:05 核对为空）
- Git 提交、审查与推送状态：807cedb（修复+7新用例+文档+Dockerfile）、6c38321（叠加镜像属主 10001:10001）已推 official/codex/project-memory-no-adapter（远端 20:08 核对一致）
- 关联发布记录／最近生产核对时间：docs/releases/personal-api-incremental-records-20261010-r1.md；2026-10-10 20:07:05 收尾复核

## 已完成与未完成

| 项目 | 状态 | 证据或说明 |
|---|---|---|
| 生产只读复现（前缀递增、重复率、最大单条） | 完成 | .artifacts/personal-api-incremental-records-20261010/repro-output2.json、repro-output3.txt |
| 根因定位（event_for_response 打包全历史） | 完成 | personal_gateway_proxy.py:283 |
| 方案文档 | 完成 | docs/plans/2026-10-10-personal-api-incremental-records.md |
| 红测试→实现→绿 | 完成 | 红：6 failed（仅新用例）/32 passed/6 skipped；绿：38 passed/6 skipped；tests-red/green.log |
| 提交推送 | 完成 | 807cedb+6c38321 已推 official |
| 生产部署与公网验收 | 完成 | 19:45:48 promote；公网 4×200+4×401；release-verified.json |
| 容器内合成端到端（三路径增量） | 完成 | deployed-checks.json：chat/Responses/SSE、首轮全保留、兜底、角色过滤、authorization 不外发、零写入 |
| 发布后有机流量形状验收 | 完成 | promote 后 51 会话 assistant 交错为零，仅合法重试头部重叠；release-verified.json |
| 归档与独立复核 | 完成 | archive-manifest.json、closeout-verified.json（20:07:05） |

## 验证记录

| 时间 | 代码版本或 hash | 环境与命令 | 退出码和结果 | 证据位置 | 验证范围与限制 |
|---|---|---|---|---|---|
| 2026-10-10 19:10–19:25 | 生产运行镜像 6c9a5779643b（活动代理副本 9f7ed873） | smartbrain-prod 只读 SQL（条数/字节/md5，无正文导出） | 0，复现成立 | .artifacts/personal-api-incremental-records-20261010/repro-output*.json/txt | 只读统计，不改任何数据 |
| 2026-10-10 19:22 | 镜像自带源（=git HEAD CRLF 9f7ed873）+ 新测试 | 生产镜像内 pytest，network=none/read-only，容器 smartbrain-incremental-red-20261010-r1 | exit 1：6 failed 全部为新增量用例、32 passed、6 skipped（PG 依赖无 DSN 跳过） | .artifacts/personal-api-incremental-records-20261010/tests-red.log | 红：证明旧源打包全历史 |
| 2026-10-10 19:23 | 候选 personal_gateway_proxy.py（3f196fe9）挂载覆盖 | 同上，容器 smartbrain-incremental-green-20261010-r1 | exit 0：38 passed、6 skipped | .artifacts/personal-api-incremental-records-20261010/tests-green.log | 绿：增量裁剪+流式+并发+错误路径回归 |
| 2026-10-10 19:23 | 工作树 | py_compile 两改动文件 | 0 | 本机 | 语法检查 |
| 2026-10-10 19:40 | 叠加镜像 sha256:532a68da…（基底 6c9a5779643b） | docker build + AST 函数级比对 | 0：仅 event_for_response 变更+新增 _incremental_request_tail，其余函数 AST 不变 | 远端 release evidence build-verified.json、build.log | 构建产物无源码挂载复测 38 passed（tests-image.log） |
| 2026-10-10 19:45:48 | 新容器 7e700797f7cc… | promote 受控切换（双锁、候选 ready、旧容器改名保留、unit 重绑） | 0：status passed，原 Env/HostConfig/IP 不变 | promoted.json、promotion-baseline.private.json | 发布自身零写入；无 DDL/迁移/Key 变更 |
| 2026-10-10 20:01:43 | 同上 | verify_release.py 终验 | 0：1032 无关容器代际保持、公网 8 项、health 26 成员/限额、edge 双视图、容器内合成端到端 passed、有机流量 51 会话形状全符合增量 | release-verified.json、deployed-checks.json | 有机流量核验仅 role/md5，不取正文；合成端到端用替身不称真实模型验收 |
| 2026-10-10 20:03:49 | 归档 | archive_remote.py | 0：images.oci.tar.gz 193027711B SHA bca17141…；evidence.private.tar.gz 1304959B SHA 7c11d3e8…；0600 | archive-manifest.json；/srv/smartbrain-backups/backups/personal-api-incremental-records-20261010-r1 | 无数据库 dump，非全冻结备份/恢复合格点 |
| 2026-10-10 20:07:05 | 收尾 | closeout_remote.py 独立复核 | 0：归档 SHA 重算一致、OCI 配置/层与实镜像匹配、终态/公网/四盘/backup 全通过 | closeout-verified.json | full_system_closed=false |

## 运行中的任务

状态：2026-10-10 19:05 核对本机无本任务相关 runner。

| 任务身份／目标 | PID、Invocation 或 Job ID | 最近观察时间与状态 | 只读观察方式 | 终态及中断处理 |
|---|---|---|---|---|
| 无 | — | — | — | — |

## 不可重跑的动作

| 动作与操作编号 | 已知结果／不确定状态 | 查询或恢复原任务的方法 |
|---|---|---|
| 生产只读 SQL 统计 | 已保存输出 | 重跑脚本即可，幂等只读 |

## 下一步

1. ~~写增量裁剪红测试~~（完成，红 6 failed/绿 38 passed）。
2. ~~实现 `_incremental_request_tail` 并接入 event_for_response~~（完成）。
3. ~~提交推送 → 生产发布门禁流程~~（完成：叠加镜像→构建复测→promote→公网/容器内端到端/有机流量形状验收→归档→复核→记录）。

任务完成，无剩余下一步。

## 决策与变更日志

| 时间 | 决策或状态变化 | 原因与来源 |
|---|---|---|
| 2026-10-10 19:30 | 方案定稿：写侧单点增量裁剪，知识库存储流程不变，存量不回改 | 用户指令"知识库里面存储的对话记录还是保持不变"；project_conversation_records/Wiki 本就不处理 personal_api |
| 2026-10-10 19:30 | request_message_count/context_source 维持不设置 | 个人代理现状；增量语义下空响应会触发既有校验器拒绝 |
| 2026-10-10 19:23 | 权威红/绿在生产镜像内执行（network=none、read-only、testdeps 只读挂载），本机 import 链不全不作权威 | 沿用 personal-proxy-concurrency-20261009 已验证模式 |
| 2026-10-10 19:45 | promote 沿用原名/IP/Env/HostConfig，旧容器改名 -rollback-incremental-20261010 停止保留 | 最小爆炸半径；回退路径明确 |
| 2026-10-10 20:01 | 有机流量验收改用 assistant 交错判别（non_final_assistant），放弃前缀超集启发式 | 前缀超集把合法重试（首发空响应存 1 条 user、重试存 [user,assistant]；同提示整段重发）误报为打包；交错判别对照发布前旧记录确认有效 |
| 2026-10-10 20:07 | 存量历史不回改不删除；主 API 未使用同名副本不改 | 用户要求知识库存储保持不变；路由不到主 API 副本，事件实例唯一 gateway-local |