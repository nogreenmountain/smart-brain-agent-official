# 智慧大脑agent自定义AGENTS元数据和记录入口更新

## 身份与范围

关联[任务](../tasks/2026-10-09-agents-reinitialize-project-mismatch.md)，负责人Codex。用户明确报告自定义规则更换/网页初始化后，知识库和调用都归其他项目；沿用限定修复授权。10:43规则更新、10:44真实MCP写入与读回通过。仅更新智慧大脑agent项目现有规则数据和一条本任务短摘要；没有代码镜像部署、DDL、服务重启、Key/Token变更、其他项目规则更新或旧记录迁移。

## 前后版本与数据保留

- project_id dfaefd9a-8e5e-4775-bc18-e3d551c651e4，v1 SHA4f9ea209d576d1a1f2ccafcfdc45d0231c13ea03f3823eb3c0aca15a3e061925，updated_at沿用2026-09-11；和用户附件规范LF后完全一致，没有机器识别注释。
- v2 SHA dcc0fd43fc49239ae3ade7b0c2ec5fa65b1b3f2e1d38c56390ed141d29390ea8，共20116字节；服务端updated_at=2026-10-09T02:43:39.884095Z（北京时间10:43:39），updated_by为实际用户7900a3dc…。
- 原规则全部保留：删除新增前部元数据/两条流程说明后，正文与原附件规范字节完全一致。新增唯一smartbrain-project-id、所有支持project_id的工具显式传UUID/冲突停止，以及短record_project_conversation入口；原propose_memory九部分交接继续保留。
- 原v1原字节备份：/srv/smartbrain-backups/backups/agents-reinitialize-project-mismatch-20261009-r1/AGENTS-before-v1.md，目录0700、文件0600；不是生产数据库冻结备份或完整恢复点。

## 实际执行与验收

使用现有认证HTTP/v4/projects/{id}/agents/upload，前置核对原v1/hash、成员权限、实际MCP项目列表、双锁、backup终态和四盘门槛。300秒临时认证会话finally关闭，没有修改账号或角色。

10:43上传200，返回v2和实际用户；download字节与本地候选一致。随后再次调用initialize返回同v2/hash/正文，证明初始化是保留已有文件而非重置。科研规则53c6edbf…/v1保持；主API e6a1a794…和个人代理b3caf14b…StartedAt保持。

真实Codex CLI0.144.5在隔离CODEX_HOME、合成认证和loopback HTTP400端点启动完整20KiB规则。首请求被当前部署helper SHA4149519f…识别为智慧脑；原附件同样封装则返回None。CLI exit1为模拟400主动结束的预期终态，没有真实模型。没有安装生产依赖。

Company Memory实际短摘要：submission2250b51d-465f-44f9-a9da-07f6a4202b45；recorda0e1c281-9503-45c8-bc44-54b37e27dd80；Wiki8b457085-6b0a-4409-920c-994a4c6e8acc《AGENTS项目归属核查与修复》v1，2026-10-09T02:44:35.347064+00:00发布。status=saved/wiki_status=published/project_id正确，上传者唐伟翔，模型和Token unknown。get_page核对两段短正文一致，get_recent_updates也返回该页，未上传推理、进度、日志、规则或其他成员对话。

## 边界与恢复

10:47用户明确确认10:26在原CLI会话里继续，旧会话沿用启动时的科研规则这一链路已确认；网页初始化或修改文件不替换已加载上下文。另一台实际规则链/override/请求头尚未直接取证，新启动实际任务仍待复验，不能称客户端已自动更新。

旧10:26科研record97737674…/Wiki1e4cfc1d…及三个调用均保持，没有静默移动、重发或删账单。旧七条调用修正与本次新短摘要分开。网页更新不能使历史记录或未连接的电脑自动迁移。

如需恢复v1，先核对当时当前版本/hash和用户授权，通过认证upload上传上述保存原字节，生成新的版本而不强行倒退version；保留v2和新增短摘要，不还原数据库。该恢复未实际执行。全部本轮runner终态、0真实模型；完整平台原有恢复验收缺口仍保留。

证据：远端/srv/smartbrain/acceptance/agents-reinitialize-project-mismatch-20261009-r1/evidence中的initial-diagnosis.json、actual-initialize-function.py、rules-recognition.json、web-update-intent.json、web-updated.json；本地同任务artifacts的rules-manifest.json、cli-full-rules-result.json、conversation-receipt-verified.json。

10:49:50只读收尾通过：智慧脑v2/hash及内容重算一致，科研v1/hash保持；原v1备份SHA/0600/目录0700通过；同一短摘要record/project/user/submission/Wiki和published保持。证据closeout-readonly.json已保存两端。未重跑upload、initialize、MCP写入或真实模型。交付文件及本轮文档镜像到E盘并核对hash，不覆盖E盘源码。
