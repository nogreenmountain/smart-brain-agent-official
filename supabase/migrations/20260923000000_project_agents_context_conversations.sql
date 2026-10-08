BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.project_agents_files (
    project_id uuid PRIMARY KEY REFERENCES public.projects(id) ON DELETE CASCADE,
    filename text NOT NULL DEFAULT 'AGENTS.md' CHECK (filename = 'AGENTS.md'),
    content text NOT NULL,
    version integer NOT NULL DEFAULT 1 CHECK (version > 0),
    sha256 text NOT NULL CHECK (sha256 ~ '^[a-f0-9]{64}$'),
    updated_by uuid REFERENCES public.users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.project_agents_file_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    filename text NOT NULL CHECK (filename = 'AGENTS.md'),
    content text NOT NULL,
    version integer NOT NULL CHECK (version > 0),
    sha256 text NOT NULL CHECK (sha256 ~ '^[a-f0-9]{64}$'),
    updated_by uuid REFERENCES public.users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (project_id, version)
);

CREATE INDEX IF NOT EXISTS idx_project_agents_versions_project
    ON public.project_agents_file_versions(project_id, version DESC);

-- A previous production candidate created these two AGENTS tables with a
-- smaller shape.  Extend that shape in place before the seed below; never
-- drop the old columns or overwrite existing content.
ALTER TABLE public.project_agents_files
    ADD COLUMN IF NOT EXISTS filename text,
    ADD COLUMN IF NOT EXISTS sha256 text,
    ADD COLUMN IF NOT EXISTS updated_by uuid;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgrelid = 'public.project_agents_files'::regclass
          AND tgname = 'archive_project_agents_version'
          AND NOT tgisinternal
    ) THEN
        ALTER TABLE public.project_agents_files DISABLE TRIGGER archive_project_agents_version;
    END IF;
END $$;

UPDATE public.project_agents_files
SET filename = COALESCE(filename, 'AGENTS.md'),
    sha256 = COALESCE(sha256, encode(digest(convert_to(content, 'UTF8'), 'sha256'), 'hex'));
ALTER TABLE public.project_agents_files
    ALTER COLUMN filename SET DEFAULT 'AGENTS.md',
    ALTER COLUMN filename SET NOT NULL,
    ALTER COLUMN sha256 SET NOT NULL;
ALTER TABLE public.project_agents_files
    DROP CONSTRAINT IF EXISTS project_agents_files_content_size_check;
ALTER TABLE public.project_agents_files
    ADD CONSTRAINT project_agents_files_content_size_check
    CHECK (octet_length(content) BETWEEN 1 AND 65536);

ALTER TABLE public.project_agents_file_versions
    ADD COLUMN IF NOT EXISTS id uuid DEFAULT gen_random_uuid(),
    ADD COLUMN IF NOT EXISTS filename text,
    ADD COLUMN IF NOT EXISTS sha256 text,
    ADD COLUMN IF NOT EXISTS updated_by uuid;
UPDATE public.project_agents_file_versions
SET filename = COALESCE(filename, 'AGENTS.md'),
    sha256 = COALESCE(sha256, encode(digest(convert_to(content, 'UTF8'), 'sha256'), 'hex'));
ALTER TABLE public.project_agents_file_versions
    ALTER COLUMN filename SET DEFAULT 'AGENTS.md',
    ALTER COLUMN filename SET NOT NULL,
    ALTER COLUMN sha256 SET NOT NULL;
ALTER TABLE public.project_agents_file_versions
    DROP CONSTRAINT IF EXISTS project_agents_file_versions_content_size_check;
ALTER TABLE public.project_agents_file_versions
    ADD CONSTRAINT project_agents_file_versions_content_size_check
    CHECK (octet_length(content) BETWEEN 1 AND 65536);

-- Idempotently seed existing projects.  Custom AGENTS.md content is never
-- overwritten; projects created after this migration are initialized by the
-- project creation transaction.
WITH defaults AS (
    SELECT p.id AS project_id,
           format(
               '# %1$s 项目协作规则%2$s%2$s<!-- smartbrain-project-id: %3$s -->%2$s<!-- smartbrain-agents-version: 1 -->%2$s<!-- smartbrain-agents-sha256: generated-on-save -->%2$s%2$s让 AI 理解项目规则，与智慧大脑高效协作。%2$s%2$s每条对话完成后，请使用 company memory 插件，将以下对话直接记录到「%4$s」项目的知识库“对话记录”中，并明确标注：%2$s%2$s- 上传成员名称%2$s- 上传时间%2$s- 使用模型%2$s- SmartBrain request_id%2$s- 本次任务完成内容%2$s',
               replace(replace(p.name, E'\r', ' '), E'\n', ' '), E'\n', p.id,
               replace(replace(p.name, E'\r', ' '), E'\n', ' ')
           ) AS content
    FROM public.projects p
)
INSERT INTO public.project_agents_files
    (project_id, filename, content, version, sha256)
SELECT project_id, 'AGENTS.md', content, 1, encode(digest(convert_to(content, 'UTF8'), 'sha256'), 'hex')
FROM defaults
ON CONFLICT (project_id) DO NOTHING;

INSERT INTO public.project_agents_file_versions
    (project_id, filename, content, version, sha256)
SELECT f.project_id, f.filename, f.content, f.version, f.sha256
FROM public.project_agents_files f
LEFT JOIN public.project_agents_file_versions v
  ON v.project_id = f.project_id AND v.version = f.version
WHERE v.project_id IS NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgrelid = 'public.project_agents_files'::regclass
          AND tgname = 'archive_project_agents_version'
          AND NOT tgisinternal
    ) THEN
        ALTER TABLE public.project_agents_files ENABLE TRIGGER archive_project_agents_version;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.project_context_tokens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    key_id uuid REFERENCES public.ai_gateway_keys(id) ON DELETE CASCADE,
    project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    agents_version integer NOT NULL CHECK (agents_version > 0),
    agents_sha256 text NOT NULL CHECK (agents_sha256 ~ '^[a-f0-9]{64}$'),
    token_hash text NOT NULL UNIQUE CHECK (token_hash ~ '^[a-f0-9]{64}$'),
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_project_context_tokens_lookup
    ON public.project_context_tokens(user_id, key_id, expires_at DESC)
    WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS public.project_conversation_records (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id text NOT NULL,
    project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    employee_id text NOT NULL,
    employee_name text NOT NULL,
    model text NOT NULL DEFAULT 'unknown',
    started_at timestamptz,
    completed_at timestamptz,
    input_tokens integer NOT NULL DEFAULT 0 CHECK (input_tokens >= 0),
    output_tokens integer NOT NULL DEFAULT 0 CHECK (output_tokens >= 0),
    total_tokens integer NOT NULL DEFAULT 0 CHECK (total_tokens >= 0),
    token_status text NOT NULL DEFAULT 'unknown'
        CHECK (token_status IN ('gateway_reported', 'unknown', 'invalid')),
    messages jsonb NOT NULL DEFAULT '[]'::jsonb,
    wiki_status text NOT NULL DEFAULT 'pending'
        CHECK (wiki_status IN ('pending', 'published', 'failed')),
    wiki_page_id uuid REFERENCES public.project_wiki_pages(id) ON DELETE SET NULL,
    wiki_error text,
    attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (project_id, request_id)
);

CREATE INDEX IF NOT EXISTS idx_project_conversation_records_project_created
    ON public.project_conversation_records(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_project_conversation_records_user_created
    ON public.project_conversation_records(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_project_conversation_records_wiki_status
    ON public.project_conversation_records(project_id, wiki_status, created_at DESC);

CREATE TABLE IF NOT EXISTS public.project_conversation_record_attempts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id uuid NOT NULL REFERENCES public.project_conversation_records(id) ON DELETE CASCADE,
    status text NOT NULL CHECK (status IN ('pending', 'published', 'failed')),
    error_message text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.ai_gateway_key_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    requested_total integer NOT NULL CHECK (requested_total >= 2),
    reason text NOT NULL CHECK (char_length(trim(reason)) BETWEEN 1 AND 2000),
    status text NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled')),
    reviewed_by uuid REFERENCES public.users(id) ON DELETE SET NULL,
    review_comment text,
    created_at timestamptz NOT NULL DEFAULT now(),
    reviewed_at timestamptz
);

-- Another earlier candidate used requested_limit/reviewer_id.  Keep those
-- columns for rollback/read compatibility while exposing the current API
-- names used by the gateway routes.
ALTER TABLE public.ai_gateway_key_requests
    ADD COLUMN IF NOT EXISTS requested_limit integer,
    ADD COLUMN IF NOT EXISTS requested_total integer,
    ADD COLUMN IF NOT EXISTS reviewer_id uuid,
    ADD COLUMN IF NOT EXISTS reviewed_by_user_id uuid,
    ADD COLUMN IF NOT EXISTS reviewed_by uuid;
UPDATE public.ai_gateway_key_requests
SET requested_total = COALESCE(requested_total, requested_limit),
    reviewed_by = COALESCE(reviewed_by, reviewer_id, reviewed_by_user_id);
ALTER TABLE public.ai_gateway_key_requests
    ALTER COLUMN requested_limit DROP NOT NULL,
    ALTER COLUMN reviewer_id DROP NOT NULL,
    ALTER COLUMN requested_total SET NOT NULL;
ALTER TABLE public.ai_gateway_key_requests
    DROP CONSTRAINT IF EXISTS ai_gateway_key_requests_requested_total_check,
    DROP CONSTRAINT IF EXISTS ai_gateway_key_requests_status_check;
ALTER TABLE public.ai_gateway_key_requests
    ADD CONSTRAINT ai_gateway_key_requests_requested_total_check CHECK (requested_total >= 2),
    ADD CONSTRAINT ai_gateway_key_requests_status_check CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled'));

CREATE INDEX IF NOT EXISTS idx_ai_gateway_key_requests_status
    ON public.ai_gateway_key_requests(status, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS uq_ai_gateway_key_requests_pending_user
    ON public.ai_gateway_key_requests(user_id)
    WHERE status = 'pending';

ALTER TABLE public.project_wiki_pages
    DROP CONSTRAINT IF EXISTS project_wiki_pages_memory_kind_check;
ALTER TABLE public.project_wiki_pages
    ADD CONSTRAINT project_wiki_pages_memory_kind_check CHECK (
        memory_kind IN (
            'workflow_template', 'failure_case', 'success_case', 'strategy',
            'retrospective', 'decision_record', 'checklist', 'background',
            'timeline_event', 'reference', 'conversation_record'
        )
    );

ALTER TABLE public.ai_daily_work_logs
    ADD COLUMN IF NOT EXISTS conversation_count integer NOT NULL DEFAULT 0 CHECK (conversation_count >= 0),
    ADD COLUMN IF NOT EXISTS wiki_upload_count integer NOT NULL DEFAULT 0 CHECK (wiki_upload_count >= 0),
    ADD COLUMN IF NOT EXISTS pending_wiki_count integer NOT NULL DEFAULT 0 CHECK (pending_wiki_count >= 0),
    ADD COLUMN IF NOT EXISTS failed_wiki_count integer NOT NULL DEFAULT 0 CHECK (failed_wiki_count >= 0),
    ADD COLUMN IF NOT EXISTS project_breakdown jsonb NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE public.project_agents_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_agents_file_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_context_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_conversation_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_conversation_record_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_gateway_key_requests ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.project_agents_files,
    public.project_agents_file_versions,
    public.project_context_tokens,
    public.project_conversation_records,
    public.project_conversation_record_attempts,
    public.ai_gateway_key_requests FROM PUBLIC;

COMMIT;
