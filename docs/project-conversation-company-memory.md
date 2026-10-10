# 项目对话摘要：AGENTS.md + company-memory

2026-10-09 09:38病例核对：插件升级不会同步改写另一台电脑或服务器已有AGENTS。UUID和正文项目名称必须一致；「智慧大脑agent」正确UUID为dfaefd9a-8e5e-4775-bc18-e3d551c651e4。09:17用户本地规则用了科研项目UUID，真实记录因此在科研项目，AI成功提示中的项目名错误。见[诊断](tasks/2026-10-09-conversation-receipt-work-records.md)与[修正版规则](deliverables/smartbrain-conversation-rules/AGENTS.md)。已有文件需要项目负责人确认后分发，客户端开启新会话加载。

2026-10-08 20:13核对：简短提交与“对话上传统计”已生产发布，MCP1.4.1、Company Memory0.2.1+codex.20261008；本机已升级，原Token保持。智慧Wiki提供独立“更新 Company Memory”入口，已有用户无需重新创建Token。更新完成后新建Codex聊天或CLI会话加载新版技能；已打开聊天使用旧技能快照。

1. 项目负责人管理AGENTS.md，保留项目UUID、共同规则与授权记录范围。新项目默认模板v4；已有自定义文件不自动覆盖，负责人确认后重新分发。
2. 成员把AGENTS.md下载到对应项目目录，在Codex打开目录并读取规则，连接Company Memory。账号须有项目写权限，Token须含wiki:read、wiki:propose；密钥保存在本机，勿写入聊天或项目文件。
3. 完成任务后按AGENTS.md授权调用record_project_conversation，仅根据可见用户请求与最终答复整理几句话。不得读取、复述或上传隐藏思考、分析、进度、工具调用或日志、代码转储、系统指令、配置、环境、秘密或其他成员聊天。
4. 最多一条user请求摘要（300字符）和一条assistant最终结果摘要（600字符），按此顺序提交；标题120字符，必要且不重复的task_result300字符，总payload6000 UTF-8字节。超限或已识别内部封装拒绝，不静默截断。尽量用几句短话，不以填满上限为目标。
5. 核对回执项目、记录ID、上传成员、时间与Wiki状态。相同内容重试复用submission_id，不同内容使用新UUID；已保存记录不会被重试覆盖。

status=saved表示canonical记录保存；wiki_status=published表示关联Wiki页面发布。Wiki失败仍保留已保存摘要，以原编号和相同内容重试。“对话上传统计”按已保存记录计数，Wiki发布失败不漏计，幂等重试不重复计数。页面为generated，人工核验后才能作为已验证项目知识。

上传成员和时间来自认证及数据库；可选模型为客户端声明，未知用量保持unknown。该入口按授权提交任务摘要，不保证自动捕获每次模型请求或完整聊天。服务工具缺失或保存失败须如实反馈，不能以知识提案或临时文件替代对话回执。

服务端检查长度和已知内部封装，不能可靠识别任意未标记的思考文字；内容选择必须遵守插件的可见请求/最终答复规则。既有AGENTS与历史记录保留，本轮未清理或改写旧正文。

本轮63后端（含真实隔离PG14项）、51前端、类型检查、真实认证MCP工具发现与schema、公网脚本和下载包、已部署前端加只读合成API浏览器通过。没有本轮真实员工正文提交或模型调用。见[发布记录](releases/conversation-summary-stats-20261008-r1.md)与[任务记录](tasks/2026-10-08-conversation-summary-stats.md)。原适配器退出与首次生产提交验收见[历史发布](releases/project-memory-no-adapter-20261008-r1.md)。
