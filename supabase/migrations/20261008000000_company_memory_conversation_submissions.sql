BEGIN;
SET LOCAL lock_timeout = '2s';
SET LOCAL statement_timeout = '10s';

-- Additive provenance only. Preserve gateway rows, AGENTS files and history.
ALTER TABLE public.project_conversation_records
    ADD COLUMN IF NOT EXISTS record_source text NOT NULL DEFAULT 'gateway',
    ADD COLUMN IF NOT EXISTS submission_id uuid,
    ADD COLUMN IF NOT EXISTS content_sha256 text,
    ADD COLUMN IF NOT EXISTS title text NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS task_result text NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS model_source text NOT NULL DEFAULT 'gateway_reported';

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.project_conversation_records'::regclass AND conname='project_conversation_submission_check') THEN
        ALTER TABLE public.project_conversation_records ADD CONSTRAINT project_conversation_submission_check CHECK (
            record_source IN ('gateway', 'company_memory') AND
            model_source IN ('gateway_reported', 'client_declared', 'unknown') AND
            (record_source <> 'company_memory' OR (
                submission_id IS NOT NULL AND content_sha256 IS NOT NULL AND
                content_sha256 ~ '^[a-f0-9]{64}$' AND char_length(trim(title)) BETWEEN 1 AND 200 AND
                model_source IN ('client_declared', 'unknown') AND
                token_status='unknown' AND input_tokens=0 AND output_tokens=0 AND total_tokens=0
            ))
        );
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_project_conversation_submission
    ON public.project_conversation_records(project_id,user_id,submission_id)
    WHERE record_source='company_memory';

ALTER TABLE public.project_conversation_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_conversation_record_attempts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.project_conversation_records, public.project_conversation_record_attempts FROM PUBLIC;
COMMIT;
