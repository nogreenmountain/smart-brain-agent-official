# Company Memory MCP

Company Memory按需检索项目Wiki、成员经验和会议摘要。propose_memory发布稳定项目知识；record_project_conversation保存授权选定的简短项目对话摘要。上传身份来自认证Token用户，generated页面须人工核验。

## 连接与更新

2026-10-08 20:13核对：生产MCP1.4.1，共31工具，原30工具保留；网页包与本机插件0.2.1+codex.20261008。公网地址https://39.105.79.0/mcp，使用本机SMARTBRAIN_WIKI_MCP_TOKEN环境变量，密钥不写入AGENTS.md、仓库或聊天。

已有用户在智慧Wiki点击“更新 Company Memory”，运行更新器保留原Token升级。完成后新建Codex聊天或CLI会话，核对record_project_conversation发现；旧聊天的技能快照不会热更新。首次安装由本人创建Token并使用安装入口。

- 项目检索：list_wiki_projects、search_wiki、get_page、get_related_nodes、get_recent_updates、get_decision_records、get_examples。
- 成员：list_member_wikis、search_member_experience、get_member_experience、get_member_recent_experience，遵守成员隐私与管理权限。
- 会议：list_meeting_summaries、search_meeting_summaries、get_meeting_summary。
- 知识写入：propose_memory，要求wiki:propose，不能替代canonical项目对话记录。
- 项目对话：record_project_conversation，要求wiki:propose、可用实名账户和developer/admin/owner写权限，系统管理员沿用既有管理权限。

## 简短提交

只从授权的可见用户请求与assistant最终答复生成几句话。禁止隐藏思考、分析/进度、工具调用或日志、代码转储、系统/开发指令、环境/配置、秘密、个人数据及其他成员聊天。不得读取思考过程后再概括上传。

| 字段 | 规则 |
|---|---|
| project_id | 当前项目AGENTS.md中的显式UUID，不按名称或默认项目回落 |
| submission_id | 新提交生成UUID，相同内容重试复用，不同内容复用会冲突 |
| title | 1–120字符 |
| messages | 1–2条摘要，每条仅role/content；两条须user请求后assistant最终结果，分别最多300/600字符 |
| task_result | 可选且不重复的结果，最多300字符 |
| model | 可选客户端声明，不确定时省略或unknown |

规范化JSON总计最多6000 UTF-8字节，超限明确拒绝，不截断。服务端拒绝已识别think/analysis/reasoning封装、分析/进度/工具channel、内部章节及代码日志fence；未声明身份、时间、Token等字段也被拒绝。任意未标记内部文字不能仅靠正则可靠判定，插件必须坚持可见请求与最终答复的来源边界。

回执含status=saved、record_id、project_id、submission_id、duplicate、uploaded_by、uploaded_at、record_source、model_source、token_status=unknown、total_tokens=null和wiki_status/wiki_page_id/wiki_error。成员来自认证，时间来自数据库，不冒充模型完成时间或可信用量。

保存与Wiki发布使用事务及savepoint。Wiki失败保留已保存摘要和通用失败码；并发重试只保留一条记录与一个页面。知识库“对话记录”查看已发布页面；PROJECT PROFILE“对话上传统计”读取全部已保存project_conversation_records，Wiki失败不漏计。新/v4/projects/{project_id}/conversation-upload-stats，旧/wiki-upload-stats保留为兼容别名且不展示于schema。

## 发布与历史

本轮只替换新项目默认initialize_project_agents函数为v4，不改表/RLS，不覆盖既有AGENTS或历史对话。首次canonical字段迁移已在2026-10-08 13:00阶段发布，详见[历史记录](releases/project-memory-no-adapter-20261008-r1.md)；本轮PG验证使用独立测试库，生产认证检查只做initialize/tools/list，没有提交员工正文。

流程见[项目记录说明](project-conversation-company-memory.md)，实际版本/失败恢复/部署与归档见[本轮发布](releases/conversation-summary-stats-20261008-r1.md)。旧下载继续410，Monitor不恢复；PROJECT_WIKI_INCLUDE_AI_CHAT_SOURCES自动编译开关属于另一入口，本轮不改。
