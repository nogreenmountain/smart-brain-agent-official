\set ON_ERROR_STOP on
-- Read-only structural gates. Run after restoration, before starting writers.
BEGIN READ ONLY;
DO $$
DECLARE name text;
BEGIN
  FOREACH name IN ARRAY ARRAY['auth.users', 'public.users', 'public.projects',
    'public.project_members', 'public.project_agents_files', 'public.project_conversation_records',
    'public.ai_gateway_keys', 'public.ai_gateway_events'] LOOP
    IF to_regclass(name) IS NULL THEN
      RAISE EXCEPTION 'required table missing: %', name;
    END IF;
  END LOOP;
  IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector') THEN
    RAISE EXCEPTION 'pgvector extension missing';
  END IF;
END $$;
SELECT 'schema gate passed' AS result;
ROLLBACK;
