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
<!-- smartbrain-agents-version: 3 -->

- 只处理本项目；先了解现有代码和约定，改动后验证结果。
- 通过 company-memory 查阅项目知识；任务完成后遵循插件规则，调用 record_project_conversation 保存本项目授权选定的 user/assistant 对话记录和任务结果，project_id="{{PROJECT_ID}}"。
- 不上传密钥、个人信息或其他成员对话；用户要求时停止记录或缩小范围。提交后核对回执，失败如实说明。
$short_agents$, '{{PROJECT_ID}}', NEW.id::text),
        '{{PROJECT_NAME}}', btrim(btrim(replace(replace(NEW.name, chr(13), ' '), chr(10), ' '))));
    INSERT INTO public.project_agents_files(project_id, content, version, sha256)
    VALUES (NEW.id, generated_content, 3,
        encode(extensions.digest(generated_content, 'sha256'), 'hex'));
    RETURN NEW;
END;
$body$;
COMMIT;
