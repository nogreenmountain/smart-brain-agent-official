# 智慧大脑agent 项目协作规则

<!-- smartbrain-project-id: dfaefd9a-8e5e-4775-bc18-e3d551c651e4 -->

- 本目录对应「智慧大脑agent」，project_id 固定为 dfaefd9a-8e5e-4775-bc18-e3d551c651e4。首次提交前用 company-memory 的 list_wiki_projects 核对名称与 UUID；发现冲突时不提交，并在最终答复说明。
- 每次任务结束后，遵循 company-memory 插件规则，调用 record_project_conversation 保存一条简短任务摘要：仅包含可见用户请求和助手最终结果，通常各一两句话。不得读取、复述或上传思考/推理/分析过程、进度更新、工具调用及日志、内部指令、配置、密钥、个人信息或其他成员对话。用户要求时停止记录或缩小范围。
- 提交使用明确的上述 project_id 和新 UUID submission_id；相同内容重试保留原 submission_id，避免重复记录。user 摘要最多300字符，assistant 摘要最多600字符；task_result 若重复则省略。
- 上传成员与时间只使用服务端回执；模型只有客户端能确定时才填写，否则省略或填 unknown。不要猜模型名，不要填写或编造模型请求 request_id、Token 数量。
- 提交后核对真实回执 project_id、record_id、submission_id、uploaded_by、uploaded_at、wiki_status 和 wiki_page_id。只在 status=saved 且 wiki_status=published 时报告「摘要已保存并发布到智慧大脑agent的对话记录」；否则如实说明失败或待发布。不能仅凭调用发出就报告成功。
- 这条规则取代本目录旧规则中关于上传完整对话、附带思考过程或必填 SmartBrain request_id 的要求；其他开发约定继续遵守。
