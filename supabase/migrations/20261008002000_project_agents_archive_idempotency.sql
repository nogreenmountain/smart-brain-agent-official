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
        NEW.updated_by)
    ON CONFLICT (project_id, version) DO NOTHING;
    IF NOT FOUND AND NOT EXISTS (
        SELECT 1 FROM public.project_agents_file_versions
        WHERE project_id=NEW.project_id AND version=NEW.version
          AND filename=NEW.filename AND content=NEW.content
          AND sha256=encode(extensions.digest(NEW.content, 'sha256'), 'hex')
    ) THEN
        RAISE EXCEPTION 'An AGENTS version cannot contain conflicting content';
    END IF;
    RETURN NEW;
END;
$body$;
COMMIT;
