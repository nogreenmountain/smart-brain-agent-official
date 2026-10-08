BEGIN;

-- Personal API calls are authenticated gateway traffic, not client self-reports.
-- Keep the existing source values and add the two server-materialized gateway
-- sources so the work-record projection can display them without pretending
-- they belong to CC Switch.
ALTER TABLE public.ai_chat_sessions
    DROP CONSTRAINT IF EXISTS ai_chat_sessions_source_check;

ALTER TABLE public.ai_chat_sessions
    ADD CONSTRAINT ai_chat_sessions_source_check CHECK (
        source IN (
            'cc_switch',
            'chatgpt_web',
            'chatgpt_desktop',
            'openai_compliance',
            'smartbrain',
            'ai_gateway',
            'personal_api'
        )
    );

COMMIT;
