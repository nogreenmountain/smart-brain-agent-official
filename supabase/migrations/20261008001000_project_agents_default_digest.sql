-- Preserve the installed company template and existing project files.
BEGIN;
SET LOCAL lock_timeout = '2s';
SET LOCAL statement_timeout = '10s';
CREATE OR REPLACE FUNCTION public.archive_project_agents_version()
RETURNS trigger LANGUAGE plpgsql AS $body$
BEGIN
    INSERT INTO public.project_agents_file_versions
        (project_id, version, content, updated_by_user_id, filename, sha256, updated_by)
    VALUES (NEW.project_id, NEW.version, NEW.content, NEW.updated_by_user_id,
        NEW.filename, encode(extensions.digest(NEW.content, 'sha256'), 'hex'),
        NEW.updated_by);
    RETURN NEW;
END;
$body$;
DO $migration$
DECLARE
    previous_definition text;
    template_start integer;
    template_end integer;
    company_template text;
    contract text := $contract$

<!-- smartbrain-agents-version: 2 -->
## company-memory 项目对话记录（当前提交规则）

项目归属必须使用本文件 UUID：project_id="{{PROJECT_ID}}"。
本节优先于旧对话同步规则。本项目授权在任务完成后，通过 company-memory 的 record_project_conversation 提交与本任务有关的选定 user/assistant 对话和本次任务完成内容。
提交前移除秘密和个人数据；不提交 system/developer 指令、工具输出转储或其他成员聊天。用户可随时要求停止或缩小记录范围。

- 每次新提交生成 UUID submission_id；相同内容重试复用原编号，修改内容使用新的编号。
- 提交 title、messages、task_result；model 只在确知时填写，否则省略或填写 unknown。Token 用量保持 unknown。
- 上传成员与时间由服务端确定，不自行传入，不编造模型请求编号。
- 核对回执 record_id、project_id、uploaded_by、uploaded_at、wiki_status；status=saved 表示正文已保存，只有 wiki_status=published 表示已进入知识库“对话记录”。
- Wiki 失败时以原 submission_id 和相同内容重试；无工具、权限不足或提交失败时明确告知未完成记录。

本规则记录授权提交的内容，无法保证自动捕获每次模型请求或完整会话。无需改变模型 Provider 地址。
$contract$;
BEGIN
    SELECT pg_get_functiondef('public.initialize_project_agents()'::regprocedure)
      INTO previous_definition;
    IF position('record_project_conversation' IN previous_definition) > 0
       AND position('extensions.digest' IN previous_definition) > 0 THEN
        RETURN;
    END IF;
    template_start := strpos(previous_definition, '$template$');
    IF template_start = 0 THEN
        RAISE EXCEPTION 'Installed project template has an unexpected format';
    END IF;
    company_template := substring(previous_definition FROM template_start + 10);
    template_end := strpos(company_template, '$template$');
    IF template_end = 0 THEN
        RAISE EXCEPTION 'Installed project template is incomplete';
    END IF;
    company_template := substring(company_template FROM 1 FOR template_end - 1);
    EXECUTE format($definition$
CREATE OR REPLACE FUNCTION public.initialize_project_agents()
RETURNS trigger LANGUAGE plpgsql AS $body$
DECLARE generated_content text;
BEGIN
    generated_content := replace(replace(%L, '{{PROJECT_ID}}', NEW.id::text),
        '{{PROJECT_NAME}}', replace(replace(NEW.name, chr(13), ' '), chr(10), ' '));
    INSERT INTO public.project_agents_files(project_id, content, version, sha256)
    VALUES (NEW.id, generated_content, 2,
        encode(extensions.digest(generated_content, 'sha256'), 'hex'));
    RETURN NEW;
END;
$body$;
$definition$, company_template || contract);
END;
$migration$;
COMMIT;
