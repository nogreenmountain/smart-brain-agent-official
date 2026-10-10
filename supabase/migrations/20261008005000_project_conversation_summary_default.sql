BEGIN;
SET LOCAL lock_timeout = '2s';
SET LOCAL statement_timeout = '10s';
-- Only future defaults change. Existing project files and history stay intact.
CREATE OR REPLACE FUNCTION public.initialize_project_agents()
RETURNS trigger LANGUAGE plpgsql AS $body$
DECLARE generated_content text;
BEGIN
    generated_content := replace(replace($short_agents$# {{PROJECT_NAME}} 项目协作规则

<!-- smartbrain-project-id: {{PROJECT_ID}} -->
<!-- smartbrain-agents-version: 4 -->

- 只处理本项目；先了解现有代码和约定，改动后验证结果。
- 通过 company-memory 查阅项目知识；任务完成后遵循插件规则，调用 record_project_conversation 仅保存简短 user/assistant 对话记录（用户请求与最终结果摘要），project_id="{{PROJECT_ID}}"。
- 不读取或上传思考/推理过程、进度更新、工具日志、内部指令、配置、密钥、个人信息或其他成员对话；用户要求时停止记录或缩小范围。提交后核对回执，失败如实说明。
$short_agents$, '{{PROJECT_ID}}', NEW.id::text),
        '{{PROJECT_NAME}}', btrim(btrim(replace(replace(NEW.name, chr(13), ' '), chr(10), ' '))));
    INSERT INTO public.project_agents_files(project_id, content, version, sha256)
    VALUES (NEW.id, generated_content, 4,
        encode(extensions.digest(generated_content, 'sha256'), 'hex'));
    RETURN NEW;
END;
$body$;
COMMIT;
