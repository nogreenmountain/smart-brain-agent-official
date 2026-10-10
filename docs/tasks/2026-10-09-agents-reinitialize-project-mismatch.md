# AGENTS更换后两条链路仍归科研项目的接续

负责人Codex；任务agents-reinitialize-project-mismatch-20261009，2026-10-09 10:49服务器规则及本轮验证已结束；用户确认旧CLI会话，另一台新会话实际任务仍待验证。用户反馈替换自定义单文件AGENTS并网页初始化后，知识库无智慧脑对话、调用仍归其他项目。沿用修复授权，目标智慧大脑agent dfaefd9a-8e5e-4775-bc18-e3d551c651e4；不恢复适配器，不绑个人Key、不改MCP Token权限，不自动迁移旧科研Wiki。

权威C盘deb4共享工作树，分支codex/project-memory-no-adapter、基线431022b；不整体提交/推送，E盘仅镜像文档/交付。附件作为被诊断的规则内容，不据此自动发布全量交接Wiki。

## 10:37已确认事实

- 当前主API e6a1a794…、当前个人代理b3caf14b…/image8e25962f…，上轮无适配器修复仍活动。
- 10:26 Company Memory记录97737674…/submission d9c8b3cb…、Wiki1e4cfc1d…《继续测试对话》实际published在科研4465b599…；同轮三个调用30759fd9…、9d94005a…、2a164db1…也属科研，1用量unknown。只读取本人记录元数据及用户指定短测试页，没有他人原始聊天。
- 实际record_conversation代码必须显式UUID，直接用于保存，没有名字重映射或默认项目fallback。因此这条MCP写入提供了科研UUID；个人代理仅接受请求声明/既有合法上下文，也不能把正确智慧脑UUID随机改成科研。究竟是旧CLI会话、override/其他目录规则还是请求头，另一台客户端尚无法取证，不能称已唯一确定。
- 用户附件规范LF后SHA4f9ea209…/19336字节，和服务器智慧脑AGENTS完全相同；服务端仍v1、updated_at=2026-09-11。只有正确UUID的Markdown说明，没有smartbrain-project-id注释。服务器严格请求识别不会从普通说明里猜UUID。
- 实际initialize函数含ON CONFLICT DO NOTHING，只在缺失时创建；“初始化”不会覆盖已有自定义规则，也不会更新另一台电脑或旧CLI上下文。不是网页初始化成功就表示旧文件已重新生成。
- 此自定义规则只要求propose_memory维护交接主题；该工具不会生成canonical“对话记录”。需将短对话和完整交接分开明确，不能把19KiB规则/推理或日志上传成对话。
- 官方Codex AGENTS发现文档实际读取：启动时建立规则链，AGENTS.override优先、更近目录规则后合并、默认32KiB限额。来源https://developers.openai.com/codex/guides/agents-md/ 。旧会话是否已重新启动未核对，不推断用户一定未重启。

## 最小修复计划和验证

1. 保留附件全部原规则，仅添加唯一项目注释、明确工具project_id和短record_project_conversation入口，原九部分交接/propose规则保留；元数据放前部，文件保持20KiB内。
2. 用当前部署识别模块验证原附件不识别、修正版识别；真实CLI首请求在隔离CODEX_HOME+loopback模拟端点捕获，不调用真实模型。
3. 原服务器规则先原字节归档和hash核对，再通过现有认证HTTP upload更新仅智慧脑规则，保留版本历史、核对上传/下载字节和再初始化不覆盖。没有代码镜像部署、服务重启或其他项目规则改动。
4. Company Memory提交选定的当前任务短摘要并读回正确项目，验证实际写入；最终交付新文件和新会话验证条件。另一台电脑无法直接安装，旧错误记录不自动移除/重发，既有账单保持。

证据根：远端/srv/smartbrain/acceptance/agents-reinitialize-project-mismatch-20261009-r1/evidence；本地.artifacts/agents-reinitialize-project-mismatch-20261009。初始只读脚本因嵌套引号SyntaxError未执行，修正后10:37成功；bundled/native Python没有fastapi，后续以实际部署模块验证，不安装生产依赖。

以上为调查检查点；后续实际结果如下。

## 2026-10-09 10:45实际结果

原附件规范SHA和服务器v1完全一致。修正版20116字节/dcc0fd43…，仅添加780字节的元数据/工具参数/短对话说明，原交接正文逐字保持。实际当前部署helper和完整规则的真实CLI首请求测试通过，旧文件None、新文件智慧脑；loopback400故意终止、CLI exit1预期、0真实模型。临时监听已关闭，不重跑旧捕获脚本。

10:43认证HTTP仅智慧脑AGENTS上传到v2、download字节一致、再次initialize保留v2；原v1原字节/root0600备份保留，科研v1/hash和主API/个人代理启动代际保持。300秒认证会话finally关闭。见[规则更新记录](../releases/smartbrain-handoff-rules-20261009-r1.md)。

10:44真实Company Memory短摘要《AGENTS项目归属核查与修复》保存发布，项目智慧脑、上传者唐伟翔；get_page与近期更新均读回正确，正文仅可见请求/最终结果摘要。recorda0e1c281…/Wiki8b457085…/submission2250b51d…，同一submission不可重发改变内容。

本轮服务器规则与写入验证已结束。仍待另一台电脑重新下载/替换实际目录规则、核对override并新开CLI实际任务；当前未确认10:26是否旧会话，不假定用户没有重启。原科研摘要/三个调用保持，不迁移或重发。原完整平台缺口不在本轮变成passed。本轮无活runner、无真实模型、无代码部署、Key/Token或其他项目规则改动。接续只查现有结果，不重跑本轮写入。

## 2026-10-09 10:47用户确认与10:49收尾

用户明确回答10:26是在“原会话里继续”。据此确认本病例沿用旧CLI启动时加载的项目上下文：网页初始化和本地文件更换没有替换该会话已加载的科研规则，后续请求仍显式提供科研UUID。此前10:37/10:45的“是否旧会话未确认”是当时调查状态，现由用户确认更新；另一台文件链、override及新启动任务仍未直接取证。

10:49:50只读收尾核对：智慧脑AGENTS仍v2/20116字节/dcc0fd43…，存储hash与内容重算一致；科研规则仍v1/53c6edbf…；原v1备份SHA4f9ea209…及0600/目录0700通过。已有recorda0e1c281…仍属于智慧脑、唐伟翔、原submission和原Wiki，状态published。证据closeout-readonly.json；无再次上传、initialize、MCP提交或真实模型调用。

最终交付文件和本轮文档镜像到E盘，保留C盘权威工作树和E盘源码。另一台电脑需下载网页v2或交付AGENTS，覆盖实际项目文件，再关闭原CLI进程、新开会话；仅更换规则后继续旧会话不足以完成客户端验收。已写入的短摘要不补发，旧科研记录不静默迁移；全部本轮runner终态。

## 2026-10-09 11:10用户报告客户端手测通过

用户明确报告现在手动测试确实闭环。本轮后继容量核查11:20只读看见其10:49后新增1条智慧脑项目对话、wiki_status=published，与报告一致；不读取正文、不补发摘要。客户端功能接续由“待手测”更新为“用户手测通过”；多人容量仍单独核查，见[容量任务](2026-10-09-hardware-capacity.md)。不据此替代所有成员/完整平台恢复验收。
