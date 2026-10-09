--
-- PostgreSQL database dump
--

-- Dumped from database version 15.8
-- Dumped by pg_dump version 15.8

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: _realtime; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA _realtime;


--
-- Name: auth; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA auth;


--
-- Name: deploy; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA deploy;


--
-- Name: extensions; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA extensions;


--
-- Name: graphql; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA graphql;


--
-- Name: graphql_public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA graphql_public;


--
-- Name: pg_net; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_net WITH SCHEMA extensions;


--
-- Name: EXTENSION pg_net; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_net IS 'Async HTTP';


--
-- Name: pgbouncer; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA pgbouncer;


--
-- Name: realtime; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA realtime;


--
-- Name: storage; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA storage;


--
-- Name: supabase_functions; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA supabase_functions;


--
-- Name: supabase_migrations; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA supabase_migrations;


--
-- Name: vault; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA vault;


--
-- Name: pg_graphql; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_graphql WITH SCHEMA graphql;


--
-- Name: EXTENSION pg_graphql; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_graphql IS 'pg_graphql: GraphQL support';


--
-- Name: pg_jsonschema; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_jsonschema WITH SCHEMA extensions;


--
-- Name: EXTENSION pg_jsonschema; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_jsonschema IS 'pg_jsonschema';


--
-- Name: pg_stat_statements; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_stat_statements WITH SCHEMA extensions;


--
-- Name: EXTENSION pg_stat_statements; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_stat_statements IS 'track planning and execution statistics of all SQL statements executed';


--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: pgjwt; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgjwt WITH SCHEMA extensions;


--
-- Name: EXTENSION pgjwt; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgjwt IS 'JSON Web Token API for Postgresql';


--
-- Name: supabase_vault; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS supabase_vault WITH SCHEMA vault;


--
-- Name: EXTENSION supabase_vault; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION supabase_vault IS 'Supabase Vault Extension';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA extensions;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: aal_level; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.aal_level AS ENUM (
    'aal1',
    'aal2',
    'aal3'
);


--
-- Name: code_challenge_method; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.code_challenge_method AS ENUM (
    's256',
    'plain'
);


--
-- Name: factor_status; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.factor_status AS ENUM (
    'unverified',
    'verified'
);


--
-- Name: factor_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.factor_type AS ENUM (
    'totp',
    'webauthn',
    'phone'
);


--
-- Name: oauth_authorization_status; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_authorization_status AS ENUM (
    'pending',
    'approved',
    'denied',
    'expired'
);


--
-- Name: oauth_client_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_client_type AS ENUM (
    'public',
    'confidential'
);


--
-- Name: oauth_registration_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_registration_type AS ENUM (
    'dynamic',
    'manual'
);


--
-- Name: oauth_response_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.oauth_response_type AS ENUM (
    'code'
);


--
-- Name: one_time_token_type; Type: TYPE; Schema: auth; Owner: -
--

CREATE TYPE auth.one_time_token_type AS ENUM (
    'confirmation_token',
    'reauthentication_token',
    'recovery_token',
    'email_change_token_new',
    'email_change_token_current',
    'phone_change_token'
);


--
-- Name: end_state; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.end_state AS ENUM (
    'Success',
    'Fail',
    'Indeterminate'
);


--
-- Name: environment; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.environment AS ENUM (
    'production',
    'staging',
    'development',
    'community'
);


--
-- Name: org_roles; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.org_roles AS ENUM (
    'owner',
    'admin',
    'developer',
    'business_user'
);


--
-- Name: prem_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.prem_status AS ENUM (
    'free',
    'pro',
    'enterprise'
);


--
-- Name: pricing_plan_interval; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.pricing_plan_interval AS ENUM (
    'day',
    'week',
    'month',
    'year'
);


--
-- Name: pricing_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.pricing_type AS ENUM (
    'one_time',
    'recurring'
);


--
-- Name: subscription_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.subscription_status AS ENUM (
    'trialing',
    'active',
    'canceled',
    'incomplete',
    'incomplete_expired',
    'past_due',
    'unpaid',
    'paused'
);


--
-- Name: trigger_event_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.trigger_event_type AS ENUM (
    'actions',
    'llms',
    'tools'
);


--
-- Name: action; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.action AS ENUM (
    'INSERT',
    'UPDATE',
    'DELETE',
    'TRUNCATE',
    'ERROR'
);


--
-- Name: equality_op; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.equality_op AS ENUM (
    'eq',
    'neq',
    'lt',
    'lte',
    'gt',
    'gte',
    'in',
    'like',
    'ilike',
    'is',
    'match',
    'imatch',
    'isdistinct'
);


--
-- Name: user_defined_filter; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.user_defined_filter AS (
	column_name text,
	op realtime.equality_op,
	value text,
	negate boolean
);


--
-- Name: wal_column; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.wal_column AS (
	name text,
	type_name text,
	type_oid oid,
	value jsonb,
	is_pkey boolean,
	is_selectable boolean
);


--
-- Name: wal_rls; Type: TYPE; Schema: realtime; Owner: -
--

CREATE TYPE realtime.wal_rls AS (
	wal jsonb,
	is_rls_enabled boolean,
	subscription_ids uuid[],
	errors text[]
);


--
-- Name: buckettype; Type: TYPE; Schema: storage; Owner: -
--

CREATE TYPE storage.buckettype AS ENUM (
    'STANDARD',
    'ANALYTICS',
    'VECTOR'
);


--
-- Name: email(); Type: FUNCTION; Schema: auth; Owner: -
--

CREATE FUNCTION auth.email() RETURNS text
    LANGUAGE sql STABLE
    AS $$
  select
  coalesce(
    nullif(current_setting('request.jwt.claim.email', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'email')
  )::text
$$;


--
-- Name: FUNCTION email(); Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON FUNCTION auth.email() IS 'Deprecated. Use auth.jwt() -> ''email'' instead.';


--
-- Name: jwt(); Type: FUNCTION; Schema: auth; Owner: -
--

CREATE FUNCTION auth.jwt() RETURNS jsonb
    LANGUAGE sql STABLE
    AS $$
  select
    coalesce(
        nullif(current_setting('request.jwt.claim', true), ''),
        nullif(current_setting('request.jwt.claims', true), '')
    )::jsonb
$$;


--
-- Name: role(); Type: FUNCTION; Schema: auth; Owner: -
--

CREATE FUNCTION auth.role() RETURNS text
    LANGUAGE sql STABLE
    AS $$
  select
  coalesce(
    nullif(current_setting('request.jwt.claim.role', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role')
  )::text
$$;


--
-- Name: FUNCTION role(); Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON FUNCTION auth.role() IS 'Deprecated. Use auth.jwt() -> ''role'' instead.';


--
-- Name: uid(); Type: FUNCTION; Schema: auth; Owner: -
--

CREATE FUNCTION auth.uid() RETURNS uuid
    LANGUAGE sql STABLE
    AS $$
  select
  coalesce(
    nullif(current_setting('request.jwt.claim.sub', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
  )::uuid
$$;


--
-- Name: FUNCTION uid(); Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON FUNCTION auth.uid() IS 'Deprecated. Use auth.jwt() -> ''sub'' instead.';


--
-- Name: grant_pg_cron_access(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.grant_pg_cron_access() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF EXISTS (
    SELECT
    FROM pg_event_trigger_ddl_commands() AS ev
    JOIN pg_extension AS ext
    ON ev.objid = ext.oid
    WHERE ext.extname = 'pg_cron'
  )
  THEN
    grant usage on schema cron to postgres with grant option;

    alter default privileges in schema cron grant all on tables to postgres with grant option;
    alter default privileges in schema cron grant all on functions to postgres with grant option;
    alter default privileges in schema cron grant all on sequences to postgres with grant option;

    alter default privileges for user supabase_admin in schema cron grant all
        on sequences to postgres with grant option;
    alter default privileges for user supabase_admin in schema cron grant all
        on tables to postgres with grant option;
    alter default privileges for user supabase_admin in schema cron grant all
        on functions to postgres with grant option;

    grant all privileges on all tables in schema cron to postgres with grant option;
    revoke all on table cron.job from postgres;
    grant select on table cron.job to postgres with grant option;
  END IF;
END;
$$;


--
-- Name: FUNCTION grant_pg_cron_access(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.grant_pg_cron_access() IS 'Grants access to pg_cron';


--
-- Name: grant_pg_graphql_access(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.grant_pg_graphql_access() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $_$
DECLARE
    func_is_graphql_resolve bool;
BEGIN
    func_is_graphql_resolve = (
        SELECT n.proname = 'resolve'
        FROM pg_event_trigger_ddl_commands() AS ev
        LEFT JOIN pg_catalog.pg_proc AS n
        ON ev.objid = n.oid
    );

    IF func_is_graphql_resolve
    THEN
        -- Update public wrapper to pass all arguments through to the pg_graphql resolve func
        DROP FUNCTION IF EXISTS graphql_public.graphql;
        create or replace function graphql_public.graphql(
            "operationName" text default null,
            query text default null,
            variables jsonb default null,
            extensions jsonb default null
        )
            returns jsonb
            language sql
        as $$
            select graphql.resolve(
                query := query,
                variables := coalesce(variables, '{}'),
                "operationName" := "operationName",
                extensions := extensions
            );
        $$;

        -- This hook executes when `graphql.resolve` is created. That is not necessarily the last
        -- function in the extension so we need to grant permissions on existing entities AND
        -- update default permissions to any others that are created after `graphql.resolve`
        grant usage on schema graphql to postgres, anon, authenticated, service_role;
        grant select on all tables in schema graphql to postgres, anon, authenticated, service_role;
        grant execute on all functions in schema graphql to postgres, anon, authenticated, service_role;
        grant all on all sequences in schema graphql to postgres, anon, authenticated, service_role;
        alter default privileges in schema graphql grant all on tables to postgres, anon, authenticated, service_role;
        alter default privileges in schema graphql grant all on functions to postgres, anon, authenticated, service_role;
        alter default privileges in schema graphql grant all on sequences to postgres, anon, authenticated, service_role;

        -- Allow postgres role to allow granting usage on graphql and graphql_public schemas to custom roles
        grant usage on schema graphql_public to postgres with grant option;
        grant usage on schema graphql to postgres with grant option;
    END IF;

END;
$_$;


--
-- Name: FUNCTION grant_pg_graphql_access(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.grant_pg_graphql_access() IS 'Grants access to pg_graphql';


--
-- Name: grant_pg_net_access(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.grant_pg_net_access() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM pg_event_trigger_ddl_commands() AS ev
    JOIN pg_extension AS ext
    ON ev.objid = ext.oid
    WHERE ext.extname = 'pg_net'
  )
  THEN
    GRANT USAGE ON SCHEMA net TO supabase_functions_admin, postgres, anon, authenticated, service_role;

    ALTER function net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) SECURITY DEFINER;
    ALTER function net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) SECURITY DEFINER;

    ALTER function net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) SET search_path = net;
    ALTER function net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) SET search_path = net;

    REVOKE ALL ON FUNCTION net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) FROM PUBLIC;
    REVOKE ALL ON FUNCTION net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) FROM PUBLIC;

    GRANT EXECUTE ON FUNCTION net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) TO supabase_functions_admin, postgres, anon, authenticated, service_role;
    GRANT EXECUTE ON FUNCTION net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) TO supabase_functions_admin, postgres, anon, authenticated, service_role;
  END IF;
END;
$$;


--
-- Name: FUNCTION grant_pg_net_access(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.grant_pg_net_access() IS 'Grants access to pg_net';


--
-- Name: pgrst_ddl_watch(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.pgrst_ddl_watch() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  cmd record;
BEGIN
  FOR cmd IN SELECT * FROM pg_event_trigger_ddl_commands()
  LOOP
    IF cmd.command_tag IN (
      'CREATE SCHEMA', 'ALTER SCHEMA'
    , 'CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO', 'ALTER TABLE'
    , 'CREATE FOREIGN TABLE', 'ALTER FOREIGN TABLE'
    , 'CREATE VIEW', 'ALTER VIEW'
    , 'CREATE MATERIALIZED VIEW', 'ALTER MATERIALIZED VIEW'
    , 'CREATE FUNCTION', 'ALTER FUNCTION'
    , 'CREATE TRIGGER'
    , 'CREATE TYPE', 'ALTER TYPE'
    , 'CREATE RULE'
    , 'COMMENT'
    )
    -- don't notify in case of CREATE TEMP table or other objects created on pg_temp
    AND cmd.schema_name is distinct from 'pg_temp'
    THEN
      NOTIFY pgrst, 'reload schema';
    END IF;
  END LOOP;
END; $$;


--
-- Name: pgrst_drop_watch(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.pgrst_drop_watch() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  obj record;
BEGIN
  FOR obj IN SELECT * FROM pg_event_trigger_dropped_objects()
  LOOP
    IF obj.object_type IN (
      'schema'
    , 'table'
    , 'foreign table'
    , 'view'
    , 'materialized view'
    , 'function'
    , 'trigger'
    , 'type'
    , 'rule'
    )
    AND obj.is_temporary IS false -- no pg_temp objects
    THEN
      NOTIFY pgrst, 'reload schema';
    END IF;
  END LOOP;
END; $$;


--
-- Name: set_graphql_placeholder(); Type: FUNCTION; Schema: extensions; Owner: -
--

CREATE FUNCTION extensions.set_graphql_placeholder() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $_$
    DECLARE
    graphql_is_dropped bool;
    BEGIN
    graphql_is_dropped = (
        SELECT ev.schema_name = 'graphql_public'
        FROM pg_event_trigger_dropped_objects() AS ev
        WHERE ev.schema_name = 'graphql_public'
    );

    IF graphql_is_dropped
    THEN
        create or replace function graphql_public.graphql(
            "operationName" text default null,
            query text default null,
            variables jsonb default null,
            extensions jsonb default null
        )
            returns jsonb
            language plpgsql
        as $$
            DECLARE
                server_version float;
            BEGIN
                server_version = (SELECT (SPLIT_PART((select version()), ' ', 2))::float);

                IF server_version >= 14 THEN
                    RETURN jsonb_build_object(
                        'errors', jsonb_build_array(
                            jsonb_build_object(
                                'message', 'pg_graphql extension is not enabled.'
                            )
                        )
                    );
                ELSE
                    RETURN jsonb_build_object(
                        'errors', jsonb_build_array(
                            jsonb_build_object(
                                'message', 'pg_graphql is only available on projects running Postgres 14 onwards.'
                            )
                        )
                    );
                END IF;
            END;
        $$;
    END IF;

    END;
$_$;


--
-- Name: FUNCTION set_graphql_placeholder(); Type: COMMENT; Schema: extensions; Owner: -
--

COMMENT ON FUNCTION extensions.set_graphql_placeholder() IS 'Reintroduces placeholder function for graphql_public.graphql';


--
-- Name: graphql(text, text, jsonb, jsonb); Type: FUNCTION; Schema: graphql_public; Owner: -
--

CREATE FUNCTION graphql_public.graphql("operationName" text DEFAULT NULL::text, query text DEFAULT NULL::text, variables jsonb DEFAULT NULL::jsonb, extensions jsonb DEFAULT NULL::jsonb) RETURNS jsonb
    LANGUAGE sql
    AS $$
  SELECT graphql.resolve(
    query := query,
    variables := coalesce(variables, '{}'),
    "operationName" := "operationName",
    extensions := extensions
  );
$$;


--
-- Name: get_auth(text); Type: FUNCTION; Schema: pgbouncer; Owner: -
--

CREATE FUNCTION pgbouncer.get_auth(p_usename text) RETURNS TABLE(username text, password text)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $_$
begin
    raise debug 'PgBouncer auth request: %', p_usename;

    return query
    select
        rolname::text,
        case when rolvaliduntil < now()
            then null
            else rolpassword::text
        end
    from pg_authid
    where rolname=$1 and rolcanlogin;
end;
$_$;


--
-- Name: add_default_agent_if_null(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.add_default_agent_if_null() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
   agent_row agents%ROWTYPE;
BEGIN
   -- If agent_id is NULL
   IF NEW.agent_id IS NULL THEN
      -- Retrieve the default_agent for the given session
      SELECT * INTO agent_row
      FROM agents
      WHERE session_id = NEW.session_id AND name = 'Default Agent';

      -- Check for existence
      IF NOT FOUND THEN
         -- Create new agent and get inserted row
         INSERT INTO agents(id, session_id, name)
         VALUES (gen_random_uuid(), NEW.session_id, 'Default Agent')
         RETURNING * INTO agent_row;
      END IF;

      -- Assign the ID of the found or created agent to the new event
      NEW.agent_id := agent_row.id;
   END IF;

   RETURN NEW;
END;
$$;


--
-- Name: add_to_shared_org(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.add_to_shared_org() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
    -- Add user to shared org as developer
    INSERT INTO public.user_orgs (user_id, org_id, role, user_email)
    VALUES (NEW.id, 'c0000000-0000-0000-0000-000000000000', 'business_user', NEW.email);
    RETURN NEW;
END;
$$;


--
-- Name: archive_project_agents_version(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.archive_project_agents_version() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
$$;


--
-- Name: create_new_org(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.create_new_org(org_name text) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    new_org_id UUID;
BEGIN
  BEGIN
    -- Create new org
    INSERT INTO public.orgs (name)
    VALUES (org_name)
    RETURNING id INTO new_org_id;

    -- Add user and org into user_orgs
    INSERT INTO public.user_orgs (user_id, org_id, user_email)
    VALUES ((SELECT auth.uid()), new_org_id, (SELECT auth.email()));

    -- Create a project for the new org
    INSERT INTO public.projects (org_id, name)
    VALUES (new_org_id, 'Default Project');

    RETURN new_org_id;
  EXCEPTION
    WHEN others THEN
      RAISE EXCEPTION 'Error creating new org';
  END;
END;
$$;


--
-- Name: ensure_root_direct_department(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.ensure_root_direct_department() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.parent_id IS NULL THEN
        INSERT INTO public.departments (
            id, name, sort_order, parent_id, allows_projects, is_direct
        )
        VALUES (
            'direct-' || substr(md5(NEW.id), 1, 32),
            '直属分级',
            COALESCE((
                SELECT max(sibling.sort_order) + 1
                FROM public.departments sibling
                WHERE sibling.parent_id = NEW.id
            ), 1),
            NEW.id,
            true,
            true
        )
        ON CONFLICT (id) DO UPDATE
        SET name = EXCLUDED.name,
            parent_id = EXCLUDED.parent_id,
            allows_projects = true,
            is_direct = true;
    END IF;
    RETURN NEW;
END;
$$;


--
-- Name: guard_gateway_key_project_binding(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.guard_gateway_key_project_binding() RETURNS trigger
    LANGUAGE plpgsql
    SET search_path TO 'pg_catalog', 'public'
    AS $$
BEGIN
    IF TG_OP <> 'INSERT' THEN
        RAISE EXCEPTION 'Gateway key project attribution is immutable';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM public.ai_gateway_keys k
        WHERE k.id=NEW.key_id AND k.user_id=NEW.user_id
    ) THEN
        RAISE EXCEPTION 'Gateway key owner does not match project binding';
    END IF;
    IF EXISTS (SELECT 1 FROM public.ai_gateway_events e WHERE e.key_id=NEW.key_id) THEN
        RAISE EXCEPTION 'A key with billed history cannot acquire a project binding';
    END IF;
    RETURN NEW;
END;
$$;


--
-- Name: initialize_project_agents(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.initialize_project_agents() RETURNS trigger
    LANGUAGE plpgsql
    AS $_$
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
$_$;


--
-- Name: protect_direct_department(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.protect_direct_department() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF OLD.is_direct AND (
        NEW.name IS DISTINCT FROM OLD.name
        OR NEW.parent_id IS DISTINCT FROM OLD.parent_id
        OR NEW.allows_projects IS DISTINCT FROM OLD.allows_projects
        OR NEW.is_direct IS DISTINCT FROM OLD.is_direct
    ) THEN
        RAISE EXCEPTION 'generated direct categories cannot be renamed, moved, or disabled';
    END IF;
    RETURN NEW;
END;
$$;


--
-- Name: protect_direct_department_delete(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.protect_direct_department_delete() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF OLD.is_direct AND pg_trigger_depth() = 1 THEN
        RAISE EXCEPTION 'generated direct categories cannot be deleted directly';
    END IF;
    RETURN OLD;
END;
$$;


--
-- Name: refresh_ai_gateway_leaderboard_daily(date[]); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.refresh_ai_gateway_leaderboard_daily(target_dates date[]) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    DELETE FROM public.ai_usage_leaderboard_daily WHERE usage_date = ANY(target_dates) AND source = 'ai_gateway';
    INSERT INTO public.ai_usage_leaderboard_daily (
      usage_date,user_id,employee_id,employee_name,origin,source,app,model,
      request_count,total_tokens,input_tokens,output_tokens,cache_read_tokens,
      cache_creation_tokens,error_count,total_cost_usd,refreshed_at)
    SELECT usage_date,user_id,employee_id,max(employee_name),'session','ai_gateway',
      lower(max(app_type)),coalesce(nullif(resolved_model,''),nullif(model,''),'unknown'),count(*)::bigint,
      sum(total_tokens),sum(input_tokens),sum(output_tokens),sum(cache_read_tokens),
      sum(cache_creation_tokens),count(*) FILTER (WHERE status_code < 200 OR status_code >= 400),
      sum(total_cost_usd),now()
    FROM public.ai_gateway_events
    WHERE usage_date = ANY(target_dates)
    GROUP BY usage_date,user_id,employee_id,coalesce(nullif(resolved_model,''),nullif(model,''),'unknown')
    ON CONFLICT (usage_date, user_id, origin, source, app, model) DO UPDATE SET
      employee_id=EXCLUDED.employee_id, employee_name=EXCLUDED.employee_name,
      request_count=EXCLUDED.request_count, total_tokens=EXCLUDED.total_tokens,
      input_tokens=EXCLUDED.input_tokens, output_tokens=EXCLUDED.output_tokens,
      cache_read_tokens=EXCLUDED.cache_read_tokens, cache_creation_tokens=EXCLUDED.cache_creation_tokens,
      error_count=EXCLUDED.error_count, total_cost_usd=EXCLUDED.total_cost_usd, refreshed_at=now();
END;
$$;


--
-- Name: refresh_ai_usage_leaderboard_daily(date[]); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.refresh_ai_usage_leaderboard_daily(target_dates date[]) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    locked_date date;
BEGIN
    IF target_dates IS NULL OR cardinality(target_dates) = 0 THEN
        RETURN;
    END IF;

    FOR locked_date IN
        SELECT DISTINCT target_date
        FROM unnest(target_dates) AS dates(target_date)
        WHERE target_date IS NOT NULL
        ORDER BY target_date
    LOOP
        PERFORM pg_advisory_xact_lock(
            hashtextextended(
                'smartbrain:ai-usage-leaderboard:' || locked_date::text,
                0
            )
        );
    END LOOP;

    DELETE FROM public.ai_usage_leaderboard_daily
    WHERE usage_date = ANY(target_dates);

    INSERT INTO public.ai_usage_leaderboard_daily (
        usage_date, user_id, employee_id, employee_name, origin,
        source, app, model, request_count, total_tokens,
        input_tokens, output_tokens, cache_read_tokens,
        cache_creation_tokens, error_count, total_cost_usd, refreshed_at
    )
    SELECT usage_date, user_id, employee_id, employee_name, origin,
           source, app, model, request_count, total_tokens,
           input_tokens, output_tokens, cache_read_tokens,
           cache_creation_tokens, error_count, total_cost_usd, now()
    FROM (
        SELECT d.usage_date,
               d.user_id,
               d.employee_id,
               max(d.employee_name) AS employee_name,
               'official'::text AS origin,
               'cc_switch'::text AS source,
               lower(COALESCE(NULLIF(d.app_type, ''), 'unknown')) AS app,
               COALESCE(NULLIF(d.model, ''), 'unknown') AS model,
               sum(d.request_count)::bigint AS request_count,
               sum(
                   CASE
                       WHEN d.input_token_semantics = 2 THEN d.input_tokens
                       WHEN lower(d.app_type) IN ('codex', 'gemini')
                            AND d.input_token_semantics = 1
                            AND d.input_tokens >= d.cache_read_tokens + d.cache_creation_tokens
                       THEN d.input_tokens - d.cache_read_tokens - d.cache_creation_tokens
                       WHEN lower(d.app_type) IN ('codex', 'gemini')
                            AND d.input_token_semantics = 0
                            AND d.input_tokens >= d.cache_read_tokens
                       THEN d.input_tokens - d.cache_read_tokens
                       ELSE d.input_tokens
                   END
                   + d.output_tokens + d.cache_read_tokens + d.cache_creation_tokens
               )::bigint AS total_tokens,
               sum(
                   CASE
                       WHEN d.input_token_semantics = 2 THEN d.input_tokens
                       WHEN lower(d.app_type) IN ('codex', 'gemini')
                            AND d.input_token_semantics = 1
                            AND d.input_tokens >= d.cache_read_tokens + d.cache_creation_tokens
                       THEN d.input_tokens - d.cache_read_tokens - d.cache_creation_tokens
                       WHEN lower(d.app_type) IN ('codex', 'gemini')
                            AND d.input_token_semantics = 0
                            AND d.input_tokens >= d.cache_read_tokens
                       THEN d.input_tokens - d.cache_read_tokens
                       ELSE d.input_tokens
                   END
               )::bigint AS input_tokens,
               sum(d.output_tokens)::bigint AS output_tokens,
               sum(d.cache_read_tokens)::bigint AS cache_read_tokens,
               sum(d.cache_creation_tokens)::bigint AS cache_creation_tokens,
               sum(GREATEST(d.request_count - d.success_count, 0))::bigint AS error_count,
               sum(d.total_cost_usd)::numeric AS total_cost_usd
        FROM public.cc_switch_usage_daily d
        WHERE d.usage_date = ANY(target_dates)
        GROUP BY d.usage_date, d.user_id, d.employee_id, d.app_type, d.model

        UNION ALL

        SELECT r.usage_date,
               r.target_user_id,
               r.target_employee_id,
               max(r.target_employee_name),
               'shared'::text,
               'cc_switch'::text,
               lower(COALESCE(NULLIF(r.app_type, ''), 'unknown')),
               COALESCE(NULLIF(r.model, ''), 'unknown'),
               count(*)::bigint,
               sum(r.total_tokens)::bigint,
               sum(r.input_tokens)::bigint,
               sum(r.output_tokens)::bigint,
               sum(r.cache_read_tokens)::bigint,
               sum(r.cache_creation_tokens)::bigint,
               count(*) FILTER (WHERE r.status_code < 200 OR r.status_code >= 400)::bigint,
               sum(r.total_cost_usd)::numeric
        FROM public.cc_switch_attributed_requests r
        WHERE r.usage_date = ANY(target_dates)
        GROUP BY r.usage_date, r.target_user_id, r.target_employee_id, r.app_type, r.model

        UNION ALL

        SELECT (s.started_at AT TIME ZONE 'Asia/Shanghai')::date,
               s.user_id,
               s.employee_id,
               max(s.employee_name),
               'session'::text,
               s.source,
               CASE WHEN s.source = 'cc_switch' THEN 'cc_switch_fallback' ELSE s.source END,
               COALESCE(NULLIF(s.model, ''), 'unknown'),
               count(*)::bigint,
               sum(s.total_tokens)::bigint,
               sum(s.prompt_tokens)::bigint,
               sum(s.completion_tokens)::bigint,
               0::bigint,
               0::bigint,
               sum(s.error_count)::bigint,
               sum(s.cost)::numeric
        FROM public.ai_chat_sessions s
        WHERE (s.started_at AT TIME ZONE 'Asia/Shanghai')::date = ANY(target_dates)
        GROUP BY (s.started_at AT TIME ZONE 'Asia/Shanghai')::date,
                 s.user_id, s.employee_id, s.source, s.model
    ) AS combined;
END;
$$;


--
-- Name: rename_org(uuid, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.rename_org(org_id uuid, org_name text) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  IF user_is_org_admin(org_id)
  AND EXISTS (
    SELECT 1
    FROM public.orgs
    WHERE orgs.id = org_id
  ) THEN
    UPDATE public.orgs
    SET name = org_name
    WHERE id = org_id;
  ELSE
    RAISE EXCEPTION 'Error renaming org';
  END IF;
END;
$$;


--
-- Name: rotate_project_api_key(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.rotate_project_api_key(project_id uuid) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
  new_api_key uuid;
BEGIN
  new_api_key := gen_random_uuid();

  UPDATE projects
  SET api_key = new_api_key
  WHERE id = project_id;

  RETURN new_api_key;
END;
$$;


--
-- Name: setup_new_users(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.setup_new_users() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  user_name TEXT;
  new_org_id UUID;
BEGIN
  user_name := NEW.raw_user_meta_data->>'full_name';

  -- Add entry into users table (NOW INCLUDING EMAIL!)
  INSERT INTO public.users (id, full_name, avatar_url, email)
  VALUES (NEW.id, user_name, NEW.raw_user_meta_data->>'avatar_url', NEW.email);

  -- ALWAYS create a personal default organization for every user
  IF user_name IS NOT NULL THEN
    INSERT INTO public.orgs (name)
    VALUES (user_name || '''s org')
    RETURNING id INTO new_org_id;
  ELSE
    INSERT INTO public.orgs (name)
    VALUES ('Default Organization')
    RETURNING id INTO new_org_id;
  END IF;

  -- Add user to their default org as owner
  INSERT INTO public.user_orgs (user_id, org_id, role, user_email)
  VALUES (NEW.id, new_org_id, 'owner', NEW.email);

  -- Create a project for the new org
  INSERT INTO public.projects (org_id, name)
  VALUES (new_org_id, 'Default Project');

  RETURN NEW;
END;
$$;


--
-- Name: FUNCTION setup_new_users(); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.setup_new_users() IS 'Creates user record, default org, and project for new signups. Fixed to include email field in users table.';


--
-- Name: touch_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.touch_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;


--
-- Name: transfer_org_ownership(uuid, uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.transfer_org_ownership(org_id uuid, new_owner_id uuid) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  IF user_is_org_owner(org_id)
  AND EXISTS (
    SELECT 1
    FROM public.user_orgs
    WHERE user_orgs.user_id = new_owner_id
  ) AND EXISTS (
    SELECT 1
    FROM public.orgs
    WHERE prem_status IN ('pro', 'enterprise')
  )
  THEN
    BEGIN
      UPDATE public.user_orgs
      SET role = 'admin'
      WHERE user_id = (SELECT auth.uid())
      AND user_orgs.org_id = transfer_org_ownership.org_id;

      UPDATE public.user_orgs
      SET role = 'owner'
      WHERE user_id = new_owner_id
      AND user_orgs.org_id = transfer_org_ownership.org_id;

    EXCEPTION WHEN OTHERS THEN
      RAISE EXCEPTION 'Error transferring ownership';
    END;
  ELSE
    RAISE EXCEPTION 'Error: either the user is not the current owner or the new owner is not a member of the organization';
  END IF;
END;
$$;


--
-- Name: user_aal(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.user_aal() RETURNS text[]
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    user_factors int;
BEGIN
    SELECT count(*)
    INTO user_factors
    FROM auth.mfa_factors
    WHERE (SELECT auth.uid()) = user_id AND status = 'verified';

    IF user_factors > 0 THEN
        RETURN ARRAY['aal2'];
    ELSE
        RETURN ARRAY['aal1', 'aal2'];
    END IF;
END;
$$;


--
-- Name: user_belongs_to_org(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.user_belongs_to_org(org_id uuid) RETURNS boolean
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM public.user_orgs uo
    WHERE uo.user_id = (SELECT auth.uid())
    AND uo.org_id = user_belongs_to_org.org_id
  );
END;
$$;


--
-- Name: user_is_org_admin(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.user_is_org_admin(org_id uuid) RETURNS boolean
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM public.user_orgs uo
    WHERE uo.user_id = (SELECT auth.uid())
    AND uo.org_id = user_is_org_admin.org_id
    AND uo.role in ('owner', 'admin')
  );
END;
$$;


--
-- Name: user_is_org_owner(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.user_is_org_owner(org_id uuid) RETURNS boolean
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM public.user_orgs uo
    WHERE uo.user_id = (SELECT auth.uid())
    AND uo.org_id = user_is_org_owner.org_id
    AND uo.role = 'owner'
  );
END;
$$;


--
-- Name: user_projects(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.user_projects() RETURNS SETOF uuid
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  RETURN QUERY
  SELECT id
  FROM public.projects
  WHERE projects.org_id in (
    SELECT org_id
    FROM user_orgs
    WHERE user_id = (SELECT auth.uid())
    );
END;
$$;


--
-- Name: apply_rls(jsonb, integer); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.apply_rls(wal jsonb, max_record_bytes integer DEFAULT (1024 * 1024)) RETURNS SETOF realtime.wal_rls
    LANGUAGE plpgsql
    AS $$
declare
    -- Regclass of the table e.g. public.notes
    entity_ regclass = (quote_ident(wal ->> 'schema') || '.' || quote_ident(wal ->> 'table'))::regclass;

    -- I, U, D, T: insert, update ...
    action realtime.action = (
        case wal ->> 'action'
            when 'I' then 'INSERT'
            when 'U' then 'UPDATE'
            when 'D' then 'DELETE'
            else 'ERROR'
        end
    );

    -- Is row level security enabled for the table
    is_rls_enabled bool = relrowsecurity from pg_class where oid = entity_;

    subscriptions realtime.subscription[] = array_agg(subs)
        from
            realtime.subscription subs
        where
            subs.entity = entity_
            -- Filter by action early - only get subscriptions interested in this action
            -- action_filter column can be: '*' (all), 'INSERT', 'UPDATE', or 'DELETE'
            and (subs.action_filter = '*' or subs.action_filter = action::text);

    -- Subscription vars
    working_role regrole;
    working_selected_columns text[];
    claimed_role regrole;
    claims jsonb;

    subscription_id uuid;
    subscription_has_access bool;
    visible_to_subscription_ids uuid[] = '{}';

    -- structured info for wal's columns
    columns realtime.wal_column[];
    -- previous identity values for update/delete
    old_columns realtime.wal_column[];

    error_record_exceeds_max_size boolean = octet_length(wal::text) > max_record_bytes;

    -- Primary jsonb output for record
    output jsonb;

    -- Loop record for iterating unique roles (outer loop)
    role_record record;
    -- Loop record for iterating unique selected_columns within a role (inner loop)
    cols_record record;
    -- Subscription ids visible at the role level (before fanning out by selected_columns)
    visible_role_sub_ids uuid[] = '{}';

begin
    perform set_config('role', null, true);

    columns =
        array_agg(
            (
                x->>'name',
                x->>'type',
                x->>'typeoid',
                realtime.cast(
                    (x->'value') #>> '{}',
                    coalesce(
                        (x->>'typeoid')::regtype, -- null when wal2json version <= 2.4
                        (x->>'type')::regtype
                    )
                ),
                (pks ->> 'name') is not null,
                true
            )::realtime.wal_column
        )
        from
            jsonb_array_elements(wal -> 'columns') x
            left join jsonb_array_elements(wal -> 'pk') pks
                on (x ->> 'name') = (pks ->> 'name');

    old_columns =
        array_agg(
            (
                x->>'name',
                x->>'type',
                x->>'typeoid',
                realtime.cast(
                    (x->'value') #>> '{}',
                    coalesce(
                        (x->>'typeoid')::regtype, -- null when wal2json version <= 2.4
                        (x->>'type')::regtype
                    )
                ),
                (pks ->> 'name') is not null,
                true
            )::realtime.wal_column
        )
        from
            jsonb_array_elements(wal -> 'identity') x
            left join jsonb_array_elements(wal -> 'pk') pks
                on (x ->> 'name') = (pks ->> 'name');

    for role_record in
        select claims_role
        from (select distinct claims_role from unnest(subscriptions)) t
        order by claims_role::text
    loop
        working_role := role_record.claims_role;

        -- Update `is_selectable` for columns and old_columns (once per role)
        columns =
            array_agg(
                (
                    c.name,
                    c.type_name,
                    c.type_oid,
                    c.value,
                    c.is_pkey,
                    pg_catalog.has_column_privilege(working_role, entity_, c.name, 'SELECT')
                )::realtime.wal_column
            )
            from
                unnest(columns) c;

        old_columns =
                array_agg(
                    (
                        c.name,
                        c.type_name,
                        c.type_oid,
                        c.value,
                        c.is_pkey,
                        pg_catalog.has_column_privilege(working_role, entity_, c.name, 'SELECT')
                    )::realtime.wal_column
                )
                from
                    unnest(old_columns) c;

        if action <> 'DELETE' and count(1) = 0 from unnest(columns) c where c.is_pkey then
            -- Fan out 400 error per distinct selected_columns for this role
            for cols_record in
                select selected_columns
                from (select distinct selected_columns from unnest(subscriptions) s where s.claims_role = working_role) t
                order by coalesce(array_to_string(selected_columns, ','), '')
            loop
                working_selected_columns := cols_record.selected_columns;
                return next (
                    jsonb_build_object(
                        'schema', wal ->> 'schema',
                        'table', wal ->> 'table',
                        'type', action
                    ),
                    is_rls_enabled,
                    (select array_agg(s.subscription_id) from unnest(subscriptions) as s where s.claims_role = working_role and (s.selected_columns is not distinct from working_selected_columns)),
                    array['Error 400: Bad Request, no primary key']
                )::realtime.wal_rls;
            end loop;

        -- The claims role does not have SELECT permission to the primary key of entity
        elsif action <> 'DELETE' and sum(c.is_selectable::int) <> count(1) from unnest(columns) c where c.is_pkey then
            -- Fan out 401 error per distinct selected_columns for this role
            for cols_record in
                select selected_columns
                from (select distinct selected_columns from unnest(subscriptions) s where s.claims_role = working_role) t
                order by coalesce(array_to_string(selected_columns, ','), '')
            loop
                working_selected_columns := cols_record.selected_columns;
                return next (
                    jsonb_build_object(
                        'schema', wal ->> 'schema',
                        'table', wal ->> 'table',
                        'type', action
                    ),
                    is_rls_enabled,
                    (select array_agg(s.subscription_id) from unnest(subscriptions) as s where s.claims_role = working_role and (s.selected_columns is not distinct from working_selected_columns)),
                    array['Error 401: Unauthorized']
                )::realtime.wal_rls;
            end loop;

        else
            -- Create the prepared statement (once per role)
            if is_rls_enabled and action <> 'DELETE' then
                if (select 1 from pg_prepared_statements where name = 'walrus_rls_stmt' limit 1) > 0 then
                    deallocate walrus_rls_stmt;
                end if;
                execute realtime.build_prepared_statement_sql('walrus_rls_stmt', entity_, columns);
            end if;

            -- Collect all visible subscription IDs for this role (filter check + RLS check)
            visible_role_sub_ids = '{}';

            for subscription_id, claims in (
                    select
                        subs.subscription_id,
                        subs.claims
                    from
                        unnest(subscriptions) subs
                    where
                        subs.entity = entity_
                        and subs.claims_role = working_role
                        and (
                            realtime.is_visible_through_filters(columns, subs.filters)
                            or (
                              action = 'DELETE'
                              and realtime.is_visible_through_filters(old_columns, subs.filters)
                            )
                        )
            ) loop

                if not is_rls_enabled or action = 'DELETE' then
                    visible_role_sub_ids = visible_role_sub_ids || subscription_id;
                else
                    -- Check if RLS allows the role to see the record
                    perform
                        -- Trim leading and trailing quotes from working_role because set_config
                        -- doesn't recognize the role as valid if they are included
                        set_config('role', trim(both '"' from working_role::text), true),
                        set_config('request.jwt.claims', claims::text, true);

                    execute 'execute walrus_rls_stmt' into subscription_has_access;

                    if subscription_has_access then
                        visible_role_sub_ids = visible_role_sub_ids || subscription_id;
                    end if;
                end if;
            end loop;

            perform set_config('role', null, true);

            -- Inner loop: per distinct selected_columns for this role
            for cols_record in
                select selected_columns
                from (select distinct selected_columns from unnest(subscriptions) s where s.claims_role = working_role) t
                order by coalesce(array_to_string(selected_columns, ','), '')
            loop
                working_selected_columns := cols_record.selected_columns;

                output = jsonb_build_object(
                    'schema', wal ->> 'schema',
                    'table', wal ->> 'table',
                    'type', action,
                    'commit_timestamp', to_char(
                        ((wal ->> 'timestamp')::timestamptz at time zone 'utc'),
                        'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'
                    ),
                    'columns', (
                        select
                            jsonb_agg(
                                jsonb_build_object(
                                    'name', pa.attname,
                                    'type', pt.typname
                                )
                                order by pa.attnum asc
                            )
                        from
                            pg_attribute pa
                            join pg_type pt
                                on pa.atttypid = pt.oid
                            left join (
                                select unnest(conkey) as pkey_attnum
                                from pg_constraint
                                where conrelid = entity_ and contype = 'p'
                            ) pk on pk.pkey_attnum = pa.attnum
                        where
                            attrelid = entity_
                            and attnum > 0
                            and pg_catalog.has_column_privilege(working_role, entity_, pa.attname, 'SELECT')
                            and (working_selected_columns is null or pa.attname = any(working_selected_columns) or pk.pkey_attnum is not null)
                    )
                )
                -- Add "record" key for insert and update
                || case
                    when action in ('INSERT', 'UPDATE') then
                        jsonb_build_object(
                            'record',
                            (
                                select
                                    jsonb_object_agg(
                                        -- if unchanged toast, get column name and value from old record
                                        coalesce((c).name, (oc).name),
                                        case
                                            when (c).name is null then (oc).value
                                            else (c).value
                                        end
                                    )
                                from
                                    unnest(columns) c
                                    full outer join unnest(old_columns) oc
                                        on (c).name = (oc).name
                                where
                                    coalesce((c).is_selectable, (oc).is_selectable)
                                    and (working_selected_columns is null or coalesce((c).name, (oc).name) = any(working_selected_columns) or coalesce((c).is_pkey, (oc).is_pkey))
                                    and ( not error_record_exceeds_max_size or (octet_length((c).value::text) <= 64))
                            )
                        )
                    else '{}'::jsonb
                end
                -- Add "old_record" key for update and delete
                || case
                    when action = 'UPDATE' then
                        jsonb_build_object(
                                'old_record',
                                (
                                    select jsonb_object_agg((c).name, (c).value)
                                    from unnest(old_columns) c
                                    where
                                        (c).is_selectable
                                        and (working_selected_columns is null or (c).name = any(working_selected_columns) or (c).is_pkey)
                                        and ( not error_record_exceeds_max_size or (octet_length((c).value::text) <= 64))
                                )
                            )
                    when action = 'DELETE' then
                        jsonb_build_object(
                            'old_record',
                            (
                                select jsonb_object_agg((c).name, (c).value)
                                from unnest(old_columns) c
                                where
                                    (c).is_selectable
                                    and (working_selected_columns is null or (c).name = any(working_selected_columns) or (c).is_pkey)
                                    and ( not error_record_exceeds_max_size or (octet_length((c).value::text) <= 64))
                                    and ( not is_rls_enabled or (c).is_pkey ) -- if RLS enabled, we can't secure deletes so filter to pkey
                            )
                        )
                    else '{}'::jsonb
                end;

                -- Filter visible_role_sub_ids to those matching the current selected_columns group
                visible_to_subscription_ids = coalesce(
                    (
                        select array_agg(s.subscription_id)
                        from unnest(subscriptions) s
                        where s.claims_role = working_role
                          and (s.selected_columns is not distinct from working_selected_columns)
                          and s.subscription_id = any(visible_role_sub_ids)
                    ),
                    '{}'::uuid[]
                );

                return next (
                    output,
                    is_rls_enabled,
                    visible_to_subscription_ids,
                    case
                        when error_record_exceeds_max_size then array['Error 413: Payload Too Large']
                        else '{}'
                    end
                )::realtime.wal_rls;
            end loop;

        end if;
    end loop;

    perform set_config('role', null, true);
end;
$$;


--
-- Name: broadcast_changes(text, text, text, text, text, record, record, text); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.broadcast_changes(topic_name text, event_name text, operation text, table_name text, table_schema text, new record, old record, level text DEFAULT 'ROW'::text) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    -- Declare a variable to hold the JSONB representation of the row
    row_data jsonb := '{}'::jsonb;
BEGIN
    IF level = 'STATEMENT' THEN
        RAISE EXCEPTION 'function can only be triggered for each row, not for each statement';
    END IF;
    -- Check the operation type and handle accordingly
    IF operation = 'INSERT' OR operation = 'UPDATE' OR operation = 'DELETE' THEN
        row_data := jsonb_build_object('old_record', OLD, 'record', NEW, 'operation', operation, 'table', table_name, 'schema', table_schema);
        PERFORM realtime.send (row_data, event_name, topic_name);
    ELSE
        RAISE EXCEPTION 'Unexpected operation type: %', operation;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Failed to process the row: %', SQLERRM;
END;

$$;


--
-- Name: build_prepared_statement_sql(text, regclass, realtime.wal_column[]); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.build_prepared_statement_sql(prepared_statement_name text, entity regclass, columns realtime.wal_column[]) RETURNS text
    LANGUAGE sql
    AS $$
      /*
      Builds a sql string that, if executed, creates a prepared statement to
      tests retrive a row from *entity* by its primary key columns.
      Example
          select realtime.build_prepared_statement_sql('public.notes', '{"id"}'::text[], '{"bigint"}'::text[])
      */
          select
      'prepare ' || prepared_statement_name || ' as
          select
              exists(
                  select
                      1
                  from
                      ' || entity || '
                  where
                      ' || string_agg(quote_ident(pkc.name) || '=' || quote_nullable(pkc.value #>> '{}') , ' and ') || '
              )'
          from
              unnest(columns) pkc
          where
              pkc.is_pkey
          group by
              entity
      $$;


--
-- Name: cast(text, regtype); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime."cast"(val text, type_ regtype) RETURNS jsonb
    LANGUAGE plpgsql IMMUTABLE
    AS $$
declare
  res jsonb;
begin
  if type_::text = 'bytea' then
    return to_jsonb(val);
  end if;
  execute format('select to_jsonb(%L::'|| type_::text || ')', val) into res;
  return res;
end
$$;


--
-- Name: check_equality_op(realtime.equality_op, regtype, text, text); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.check_equality_op(op realtime.equality_op, type_ regtype, val_1 text, val_2 text) RETURNS boolean
    LANGUAGE plpgsql IMMUTABLE
    AS $$
/*
Casts *val_1* and *val_2* as type *type_* and check the *op* condition for truthiness
*/
declare
    op_symbol text = (
        case
            when op = 'eq' then '='
            when op = 'neq' then '!='
            when op = 'lt' then '<'
            when op = 'lte' then '<='
            when op = 'gt' then '>'
            when op = 'gte' then '>='
            when op = 'in' then '= any'
            else 'UNKNOWN OP'
        end
    );
    res boolean;
begin
    execute format(
        'select %L::'|| type_::text || ' ' || op_symbol
        || ' ( %L::'
        || (
            case
                when op = 'in' then type_::text || '[]'
                else type_::text end
        )
        || ')', val_1, val_2) into res;
    return res;
end;
$$;


--
-- Name: check_equality_op(realtime.equality_op, regtype, text, text, boolean); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.check_equality_op(op realtime.equality_op, type_ regtype, val_1 text, val_2 text, negate boolean) RETURNS boolean
    LANGUAGE plpgsql STABLE
    AS $$
declare
    op_symbol text;
    res boolean;
begin
    -- IS DISTINCT FROM / IS NOT DISTINCT FROM: infix, both sides typed literals
    if op = 'isdistinct' then
        execute format(
            'select %L::%s %s %L::%s',
            val_1,
            type_::text,
            case when negate then 'IS NOT DISTINCT FROM' else 'IS DISTINCT FROM' end,
            val_2,
            type_::text
        ) into res;
        return res;
    end if;

    -- IS requires a keyword RHS (NULL, TRUE, FALSE, UNKNOWN), not a typed literal
    if op = 'is' then
        if val_2 not in ('null', 'true', 'false', 'unknown') then
            raise exception 'invalid value for is filter: must be null, true, false, or unknown';
        end if;
        execute format(
            'select %L::%s %s %s',
            val_1,
            type_::text,
            case when negate then 'IS NOT' else 'IS' end,
            upper(val_2)
        ) into res;
        return res;
    end if;

    op_symbol = case
        when op = 'eq'    then '='
        when op = 'neq'   then '!='
        when op = 'lt'    then '<'
        when op = 'lte'   then '<='
        when op = 'gt'    then '>'
        when op = 'gte'   then '>='
        when op = 'in'    then '= any'
        when op = 'like'   then 'LIKE'
        when op = 'ilike'  then 'ILIKE'
        when op = 'match'  then '~'
        when op = 'imatch' then '~*'
        else null
    end;

    if op_symbol is null then
        raise exception 'unsupported equality operator: %', op::text;
    end if;

    execute format(
        'select %L::%s %s (%L::%s)',
        val_1,
        type_::text,
        op_symbol,
        val_2,
        case when op = 'in' then type_::text || '[]' else type_::text end
    ) into res;

    return case when negate then not res else res end;
end;
$$;


--
-- Name: is_visible_through_filters(realtime.wal_column[], realtime.user_defined_filter[]); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.is_visible_through_filters(columns realtime.wal_column[], filters realtime.user_defined_filter[]) RETURNS boolean
    LANGUAGE sql STABLE
    AS $$
    select
        filters is null
        or array_length(filters, 1) is null
        or coalesce(
            count(col.name) = count(1)
            and sum(
                realtime.check_equality_op(
                    op:=f.op,
                    type_:=coalesce(col.type_oid::regtype, col.type_name::regtype),
                    val_1:=col.value #>> '{}',
                    val_2:=f.value,
                    negate:=coalesce(f.negate, false)
                )::int
            ) filter (where col.name is not null) = count(col.name),
            false
        )
    from
        unnest(filters) f
        left join unnest(columns) col
            on f.column_name = col.name;
$$;


--
-- Name: list_changes(name, name, integer, integer); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.list_changes(publication name, slot_name name, max_changes integer, max_record_bytes integer) RETURNS TABLE(wal jsonb, is_rls_enabled boolean, subscription_ids uuid[], errors text[], slot_changes_count bigint)
    LANGUAGE sql
    SET log_min_messages TO 'fatal'
    AS $$
  WITH pub AS (
    SELECT
      concat_ws(
        ',',
        CASE WHEN bool_or(pubinsert) THEN 'insert' ELSE NULL END,
        CASE WHEN bool_or(pubupdate) THEN 'update' ELSE NULL END,
        CASE WHEN bool_or(pubdelete) THEN 'delete' ELSE NULL END
      ) AS w2j_actions,
      coalesce(
        string_agg(
          realtime.quote_wal2json(format('%I.%I', schemaname, tablename)::regclass),
          ','
        ) filter (WHERE ppt.tablename IS NOT NULL),
        ''
      ) AS w2j_add_tables
    FROM pg_publication pp
    LEFT JOIN pg_publication_tables ppt ON pp.pubname = ppt.pubname
    WHERE pp.pubname = publication
    GROUP BY pp.pubname
    LIMIT 1
  ),
  -- MATERIALIZED ensures pg_logical_slot_get_changes is called exactly once
  w2j AS MATERIALIZED (
    SELECT x.*, pub.w2j_add_tables
    FROM pub,
         pg_logical_slot_get_changes(
           slot_name, null, max_changes,
           'include-pk', 'true',
           'include-transaction', 'false',
           'include-timestamp', 'true',
           'include-type-oids', 'true',
           'format-version', '2',
           'actions', pub.w2j_actions,
           'add-tables', pub.w2j_add_tables
         ) x
  ),
  slot_count AS (
    SELECT count(*)::bigint AS cnt
    FROM w2j
    WHERE w2j.w2j_add_tables <> ''
  ),
  rls_filtered AS (
    SELECT xyz.wal, xyz.is_rls_enabled, xyz.subscription_ids, xyz.errors
    FROM w2j,
         realtime.apply_rls(
           wal := w2j.data::jsonb,
           max_record_bytes := max_record_bytes
         ) xyz(wal, is_rls_enabled, subscription_ids, errors)
    WHERE w2j.w2j_add_tables <> ''
      AND xyz.subscription_ids[1] IS NOT NULL
  )
  SELECT rf.wal, rf.is_rls_enabled, rf.subscription_ids, rf.errors, sc.cnt
  FROM rls_filtered rf, slot_count sc

  UNION ALL

  SELECT null, null, null, null, sc.cnt
  FROM slot_count sc
  WHERE NOT EXISTS (SELECT 1 FROM rls_filtered)
$$;


--
-- Name: quote_wal2json(regclass); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.quote_wal2json(entity regclass) RETURNS text
    LANGUAGE sql IMMUTABLE STRICT
    AS $$
  SELECT
    realtime.wal2json_escape_identifier(nsp.nspname::text)
    || '.'
    || realtime.wal2json_escape_identifier(pc.relname::text)
  FROM pg_class pc
  JOIN pg_namespace nsp ON pc.relnamespace = nsp.oid
  WHERE pc.oid = entity
$$;


--
-- Name: send(jsonb, text, text, boolean); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.send(payload jsonb, event text, topic text, private boolean DEFAULT true) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
  generated_id uuid;
  final_payload jsonb;
BEGIN
  BEGIN
    generated_id := gen_random_uuid();

    -- Check if payload has an 'id' key, if not, add the generated UUID
    IF payload ? 'id' THEN
      final_payload := payload;
    ELSE
      final_payload := jsonb_set(payload, '{id}', to_jsonb(generated_id));
    END IF;

    -- Set the topic configuration
    EXECUTE format('SET LOCAL realtime.topic TO %L', topic);

    INSERT INTO realtime.messages (id, payload, event, topic, private, extension)
    VALUES (generated_id, final_payload, event, topic, private, 'broadcast');
  EXCEPTION
    WHEN OTHERS THEN
      RAISE WARNING 'WarnSendingBroadcastMessage: %', SQLERRM;
  END;
END;
$$;


--
-- Name: send_binary(bytea, text, text, boolean); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.send_binary(payload bytea, event text, topic text, private boolean DEFAULT true) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
  generated_id uuid;
BEGIN
  BEGIN
    generated_id := gen_random_uuid();

    EXECUTE format('SET LOCAL realtime.topic TO %L', topic);

    INSERT INTO realtime.messages (id, binary_payload, event, topic, private, extension)
    VALUES (generated_id, payload, event, topic, private, 'broadcast');
  EXCEPTION
    WHEN OTHERS THEN
      RAISE WARNING 'WarnSendingBroadcastMessage: %', SQLERRM;
  END;
END;
$$;


--
-- Name: subscription_check_filters(); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.subscription_check_filters() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
declare
    col_names text[] = coalesce(
            array_agg(a.attname order by a.attnum),
            '{}'::text[]
        )
        from
            pg_catalog.pg_attribute a
        where
            a.attrelid = new.entity
            and a.attnum > 0
            and not a.attisdropped
            and pg_catalog.has_column_privilege(
                (new.claims ->> 'role'),
                a.attrelid,
                a.attnum,
                'SELECT'
            );
    filter realtime.user_defined_filter;
    col_type regtype;
    in_val jsonb;
    selected_col text;
begin
    for filter in select * from unnest(new.filters) loop
        if not filter.column_name = any(col_names) then
            raise exception 'invalid column for filter %', filter.column_name;
        end if;

        col_type = (
            select atttypid::regtype
            from pg_catalog.pg_attribute
            where attrelid = new.entity
                  and attname = filter.column_name
        );
        if col_type is null then
            raise exception 'failed to lookup type for column %', filter.column_name;
        end if;

        if filter.op = 'in'::realtime.equality_op then
            in_val = realtime.cast(filter.value, (col_type::text || '[]')::regtype);
            if coalesce(jsonb_array_length(in_val), 0) > 100 then
                raise exception 'too many values for `in` filter. Maximum 100';
            end if;
        elsif filter.op = 'is'::realtime.equality_op then
            -- `is` requires a keyword RHS rather than a typed literal
            if filter.value not in ('null', 'true', 'false', 'unknown') then
                raise exception 'invalid value for is filter: must be null, true, false, or unknown';
            end if;
            -- IS NULL works for any type, but IS TRUE/FALSE/UNKNOWN require a boolean
            -- operand. Reject the non-null keywords on non-boolean columns here so they
            -- don't abort apply_rls at WAL time.
            if filter.value <> 'null' and col_type <> 'boolean'::regtype then
                raise exception 'is % filter requires a boolean column, got %', filter.value, col_type::text;
            end if;
        elsif filter.op in ('like'::realtime.equality_op, 'ilike'::realtime.equality_op) then
            -- like/ilike apply the text pattern operator (~~); reject column types that
            -- have no such operator instead of failing at WAL time
            if not exists (
                select 1 from pg_catalog.pg_operator
                where oprname = '~~' and oprleft = col_type
            ) then
                raise exception 'operator % requires a text-compatible column type, got %', filter.op::text, col_type::text;
            end if;
        elsif filter.op in ('match'::realtime.equality_op, 'imatch'::realtime.equality_op) then
            -- match/imatch apply the regex operators ~ / ~*; reject column types that have
            -- no such operator (e.g. integer) instead of failing at WAL time, mirroring the
            -- like/ilike guard above.
            if not exists (
                select 1 from pg_catalog.pg_operator
                where oprname = case when filter.op = 'imatch'::realtime.equality_op then '~*' else '~' end
                  and oprleft = col_type
                  and oprright = col_type
                  and oprresult = 'boolean'::regtype
            ) then
                raise exception 'operator % requires a text-compatible column type, got %', filter.op::text, col_type::text;
            end if;
            -- validate the regex eagerly so a bad pattern is rejected here, not inside
            -- apply_rls where it would abort the WAL stream for the entity
            begin
                perform '' ~ filter.value;
            exception when others then
                raise exception 'invalid regular expression for % filter: %', filter.op::text, sqlerrm;
            end;
        else
            -- eq/neq/lt/lte/gt/gte: value must be coercable to the type
            perform realtime.cast(filter.value, col_type);
        end if;
    end loop;

    if new.selected_columns is not null then
        for selected_col in select * from unnest(new.selected_columns) loop
            if not selected_col = any(col_names) then
                raise exception 'invalid column for select %', selected_col;
            end if;
        end loop;
    end if;

    -- Apply consistent order to filters so the unique constraint can't be tricked by a
    -- different filter order. negate is part of the sort key.
    new.filters = coalesce(
        array_agg(f order by f.column_name, f.op, f.value, f.negate),
        '{}'
    ) from unnest(new.filters) f;

    new.selected_columns = (
        select array_agg(c order by c)
        from unnest(new.selected_columns) c
    );

    return new;
end;
$$;


--
-- Name: to_regrole(text); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.to_regrole(role_name text) RETURNS regrole
    LANGUAGE sql IMMUTABLE
    AS $$ select role_name::regrole $$;


--
-- Name: topic(); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.topic() RETURNS text
    LANGUAGE sql STABLE
    AS $$
select nullif(current_setting('realtime.topic', true), '')::text;
$$;


--
-- Name: wal2json_escape_identifier(text); Type: FUNCTION; Schema: realtime; Owner: -
--

CREATE FUNCTION realtime.wal2json_escape_identifier(name text) RETURNS text
    LANGUAGE sql IMMUTABLE STRICT
    AS $$
  -- Prefix `\`, `,`, `.`, and any whitespace with `\`
  SELECT regexp_replace(name, '([\\,.[:space:]])', '\\\1', 'g')
$$;


--
-- Name: allow_any_operation(text[]); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.allow_any_operation(expected_operations text[]) RETURNS boolean
    LANGUAGE sql STABLE
    AS $$
  WITH current_operation AS (
    SELECT storage.operation() AS raw_operation
  ),
  normalized AS (
    SELECT CASE
      WHEN raw_operation LIKE 'storage.%' THEN substr(raw_operation, 9)
      ELSE raw_operation
    END AS current_operation
    FROM current_operation
  )
  SELECT EXISTS (
    SELECT 1
    FROM normalized n
    CROSS JOIN LATERAL unnest(expected_operations) AS expected_operation
    WHERE expected_operation IS NOT NULL
      AND expected_operation <> ''
      AND n.current_operation = CASE
        WHEN expected_operation LIKE 'storage.%' THEN substr(expected_operation, 9)
        ELSE expected_operation
      END
  );
$$;


--
-- Name: allow_only_operation(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.allow_only_operation(expected_operation text) RETURNS boolean
    LANGUAGE sql STABLE
    AS $$
  WITH current_operation AS (
    SELECT storage.operation() AS raw_operation
  ),
  normalized AS (
    SELECT
      CASE
        WHEN raw_operation LIKE 'storage.%' THEN substr(raw_operation, 9)
        ELSE raw_operation
      END AS current_operation,
      CASE
        WHEN expected_operation LIKE 'storage.%' THEN substr(expected_operation, 9)
        ELSE expected_operation
      END AS requested_operation
    FROM current_operation
  )
  SELECT CASE
    WHEN requested_operation IS NULL OR requested_operation = '' THEN FALSE
    ELSE COALESCE(current_operation = requested_operation, FALSE)
  END
  FROM normalized;
$$;


--
-- Name: can_insert_object(text, text, uuid, jsonb); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.can_insert_object(bucketid text, name text, owner uuid, metadata jsonb) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  INSERT INTO "storage"."objects" ("bucket_id", "name", "owner", "metadata") VALUES (bucketid, name, owner, metadata);
  -- hack to rollback the successful insert
  RAISE sqlstate 'PT200' using
  message = 'ROLLBACK',
  detail = 'rollback successful insert';
END
$$;


--
-- Name: enforce_bucket_name_length(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.enforce_bucket_name_length() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
    if length(new.name) > 100 then
        raise exception 'bucket name "%" is too long (% characters). Max is 100.', new.name, length(new.name);
    end if;
    return new;
end;
$$;


--
-- Name: extension(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.extension(name text) RETURNS text
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    _parts text[];
    _filename text;
BEGIN
    -- Split on "/" to get path segments
    SELECT string_to_array(name, '/') INTO _parts;
    -- Get the last path segment (the actual filename)
    SELECT _parts[array_length(_parts, 1)] INTO _filename;
    -- Extract extension: reverse, split on '.', then reverse again
    RETURN reverse(split_part(reverse(_filename), '.', 1));
END
$$;


--
-- Name: filename(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.filename(name text) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
_parts text[];
BEGIN
	select string_to_array(name, '/') into _parts;
	return _parts[array_length(_parts,1)];
END
$$;


--
-- Name: foldername(text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.foldername(name text) RETURNS text[]
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    _parts text[];
BEGIN
    -- Split on "/" to get path segments
    SELECT string_to_array(name, '/') INTO _parts;
    -- Return everything except the last segment
    RETURN _parts[1 : array_length(_parts,1) - 1];
END
$$;


--
-- Name: get_common_prefix(text, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.get_common_prefix(p_key text, p_prefix text, p_delimiter text) RETURNS text
    LANGUAGE sql IMMUTABLE
    AS $$
SELECT CASE
    WHEN position(p_delimiter IN substring(p_key FROM length(p_prefix) + 1)) > 0
    THEN left(p_key, length(p_prefix) + position(p_delimiter IN substring(p_key FROM length(p_prefix) + 1)))
    ELSE NULL
END;
$$;


--
-- Name: get_size_by_bucket(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.get_size_by_bucket() RETURNS TABLE(size bigint, bucket_id text)
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    return query
        select sum((metadata->>'size')::bigint)::bigint as size, obj.bucket_id
        from "storage".objects as obj
        group by obj.bucket_id;
END
$$;


--
-- Name: list_multipart_uploads_with_delimiter(text, text, text, integer, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.list_multipart_uploads_with_delimiter(bucket_id text, prefix_param text, delimiter_param text, max_keys integer DEFAULT 100, next_key_token text DEFAULT ''::text, next_upload_token text DEFAULT ''::text) RETURNS TABLE(key text, id text, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $_$
BEGIN
    RETURN QUERY EXECUTE
        'SELECT DISTINCT ON(key COLLATE "C") * from (
            SELECT
                CASE
                    WHEN position($2 IN substring(key from length($1) + 1)) > 0 THEN
                        substring(key from 1 for length($1) + position($2 IN substring(key from length($1) + 1)))
                    ELSE
                        key
                END AS key, id, created_at
            FROM
                storage.s3_multipart_uploads
            WHERE
                bucket_id = $5 AND
                key ILIKE $1 || ''%'' AND
                CASE
                    WHEN $4 != '''' AND $6 = '''' THEN
                        CASE
                            WHEN position($2 IN substring(key from length($1) + 1)) > 0 THEN
                                substring(key from 1 for length($1) + position($2 IN substring(key from length($1) + 1))) COLLATE "C" > $4
                            ELSE
                                key COLLATE "C" > $4
                            END
                    ELSE
                        true
                END AND
                CASE
                    WHEN $6 != '''' THEN
                        id COLLATE "C" > $6
                    ELSE
                        true
                    END
            ORDER BY
                key COLLATE "C" ASC, created_at ASC) as e order by key COLLATE "C" LIMIT $3'
        USING prefix_param, delimiter_param, max_keys, next_key_token, bucket_id, next_upload_token;
END;
$_$;


--
-- Name: list_objects_with_delimiter(text, text, text, integer, text, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.list_objects_with_delimiter(_bucket_id text, prefix_param text, delimiter_param text, max_keys integer DEFAULT 100, start_after text DEFAULT ''::text, next_token text DEFAULT ''::text, sort_order text DEFAULT 'asc'::text) RETURNS TABLE(name text, id uuid, metadata jsonb, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone)
    LANGUAGE plpgsql STABLE
    AS $_$
DECLARE
    v_peek_name TEXT;
    v_current RECORD;
    v_common_prefix TEXT;

    -- Configuration
    v_is_asc BOOLEAN;
    v_prefix TEXT;
    v_start TEXT;
    v_upper_bound TEXT;
    v_file_batch_size INT;

    -- Seek state
    v_next_seek TEXT;
    v_count INT := 0;

    -- Dynamic SQL for batch query only
    v_batch_query TEXT;

BEGIN
    -- ========================================================================
    -- INITIALIZATION
    -- ========================================================================
    v_is_asc := lower(coalesce(sort_order, 'asc')) = 'asc';
    v_prefix := coalesce(prefix_param, '');
    v_start := CASE WHEN coalesce(next_token, '') <> '' THEN next_token ELSE coalesce(start_after, '') END;
    v_file_batch_size := LEAST(GREATEST(max_keys * 2, 100), 1000);

    -- Calculate upper bound for prefix filtering (bytewise, using COLLATE "C")
    IF v_prefix = '' THEN
        v_upper_bound := NULL;
    ELSIF right(v_prefix, 1) = delimiter_param THEN
        v_upper_bound := left(v_prefix, -1) || chr(ascii(delimiter_param) + 1);
    ELSE
        v_upper_bound := left(v_prefix, -1) || chr(ascii(right(v_prefix, 1)) + 1);
    END IF;

    -- Build batch query (dynamic SQL - called infrequently, amortized over many rows)
    IF v_is_asc THEN
        IF v_upper_bound IS NOT NULL THEN
            v_batch_query := 'SELECT o.name, o.id, o.updated_at, o.created_at, o.last_accessed_at, o.metadata ' ||
                'FROM storage.objects o WHERE o.bucket_id = $1 AND o.name COLLATE "C" >= $2 ' ||
                'AND o.name COLLATE "C" < $3 ORDER BY o.name COLLATE "C" ASC LIMIT $4';
        ELSE
            v_batch_query := 'SELECT o.name, o.id, o.updated_at, o.created_at, o.last_accessed_at, o.metadata ' ||
                'FROM storage.objects o WHERE o.bucket_id = $1 AND o.name COLLATE "C" >= $2 ' ||
                'ORDER BY o.name COLLATE "C" ASC LIMIT $4';
        END IF;
    ELSE
        IF v_upper_bound IS NOT NULL THEN
            v_batch_query := 'SELECT o.name, o.id, o.updated_at, o.created_at, o.last_accessed_at, o.metadata ' ||
                'FROM storage.objects o WHERE o.bucket_id = $1 AND o.name COLLATE "C" < $2 ' ||
                'AND o.name COLLATE "C" >= $3 ORDER BY o.name COLLATE "C" DESC LIMIT $4';
        ELSE
            v_batch_query := 'SELECT o.name, o.id, o.updated_at, o.created_at, o.last_accessed_at, o.metadata ' ||
                'FROM storage.objects o WHERE o.bucket_id = $1 AND o.name COLLATE "C" < $2 ' ||
                'ORDER BY o.name COLLATE "C" DESC LIMIT $4';
        END IF;
    END IF;

    -- ========================================================================
    -- SEEK INITIALIZATION: Determine starting position
    -- ========================================================================
    IF v_start = '' THEN
        IF v_is_asc THEN
            v_next_seek := v_prefix;
        ELSE
            -- DESC without cursor: find the last item in range
            IF v_upper_bound IS NOT NULL THEN
                SELECT o.name INTO v_next_seek FROM storage.objects o
                WHERE o.bucket_id = _bucket_id AND o.name COLLATE "C" >= v_prefix AND o.name COLLATE "C" < v_upper_bound
                ORDER BY o.name COLLATE "C" DESC LIMIT 1;
            ELSIF v_prefix <> '' THEN
                SELECT o.name INTO v_next_seek FROM storage.objects o
                WHERE o.bucket_id = _bucket_id AND o.name COLLATE "C" >= v_prefix
                ORDER BY o.name COLLATE "C" DESC LIMIT 1;
            ELSE
                SELECT o.name INTO v_next_seek FROM storage.objects o
                WHERE o.bucket_id = _bucket_id
                ORDER BY o.name COLLATE "C" DESC LIMIT 1;
            END IF;

            IF v_next_seek IS NOT NULL THEN
                v_next_seek := v_next_seek || delimiter_param;
            ELSE
                RETURN;
            END IF;
        END IF;
    ELSE
        -- Cursor provided: determine if it refers to a folder or leaf
        IF EXISTS (
            SELECT 1 FROM storage.objects o
            WHERE o.bucket_id = _bucket_id
              AND o.name COLLATE "C" LIKE v_start || delimiter_param || '%'
            LIMIT 1
        ) THEN
            -- Cursor refers to a folder
            IF v_is_asc THEN
                v_next_seek := v_start || chr(ascii(delimiter_param) + 1);
            ELSE
                v_next_seek := v_start || delimiter_param;
            END IF;
        ELSE
            -- Cursor refers to a leaf object
            IF v_is_asc THEN
                v_next_seek := v_start || delimiter_param;
            ELSE
                v_next_seek := v_start;
            END IF;
        END IF;
    END IF;

    -- ========================================================================
    -- MAIN LOOP: Hybrid peek-then-batch algorithm
    -- Uses STATIC SQL for peek (hot path) and DYNAMIC SQL for batch
    -- ========================================================================
    LOOP
        EXIT WHEN v_count >= max_keys;

        -- STEP 1: PEEK using STATIC SQL (plan cached, very fast)
        IF v_is_asc THEN
            IF v_upper_bound IS NOT NULL THEN
                SELECT o.name INTO v_peek_name FROM storage.objects o
                WHERE o.bucket_id = _bucket_id AND o.name COLLATE "C" >= v_next_seek AND o.name COLLATE "C" < v_upper_bound
                ORDER BY o.name COLLATE "C" ASC LIMIT 1;
            ELSE
                SELECT o.name INTO v_peek_name FROM storage.objects o
                WHERE o.bucket_id = _bucket_id AND o.name COLLATE "C" >= v_next_seek
                ORDER BY o.name COLLATE "C" ASC LIMIT 1;
            END IF;
        ELSE
            IF v_upper_bound IS NOT NULL THEN
                SELECT o.name INTO v_peek_name FROM storage.objects o
                WHERE o.bucket_id = _bucket_id AND o.name COLLATE "C" < v_next_seek AND o.name COLLATE "C" >= v_prefix
                ORDER BY o.name COLLATE "C" DESC LIMIT 1;
            ELSIF v_prefix <> '' THEN
                SELECT o.name INTO v_peek_name FROM storage.objects o
                WHERE o.bucket_id = _bucket_id AND o.name COLLATE "C" < v_next_seek AND o.name COLLATE "C" >= v_prefix
                ORDER BY o.name COLLATE "C" DESC LIMIT 1;
            ELSE
                SELECT o.name INTO v_peek_name FROM storage.objects o
                WHERE o.bucket_id = _bucket_id AND o.name COLLATE "C" < v_next_seek
                ORDER BY o.name COLLATE "C" DESC LIMIT 1;
            END IF;
        END IF;

        EXIT WHEN v_peek_name IS NULL;

        -- STEP 2: Check if this is a FOLDER or FILE
        v_common_prefix := storage.get_common_prefix(v_peek_name, v_prefix, delimiter_param);

        IF v_common_prefix IS NOT NULL THEN
            -- FOLDER: Emit and skip to next folder (no heap access needed)
            name := rtrim(v_common_prefix, delimiter_param);
            id := NULL;
            updated_at := NULL;
            created_at := NULL;
            last_accessed_at := NULL;
            metadata := NULL;
            RETURN NEXT;
            v_count := v_count + 1;

            -- Advance seek past the folder range
            IF v_is_asc THEN
                v_next_seek := left(v_common_prefix, -1) || chr(ascii(delimiter_param) + 1);
            ELSE
                v_next_seek := v_common_prefix;
            END IF;
        ELSE
            -- FILE: Batch fetch using DYNAMIC SQL (overhead amortized over many rows)
            -- For ASC: upper_bound is the exclusive upper limit (< condition)
            -- For DESC: prefix is the inclusive lower limit (>= condition)
            FOR v_current IN EXECUTE v_batch_query USING _bucket_id, v_next_seek,
                CASE WHEN v_is_asc THEN COALESCE(v_upper_bound, v_prefix) ELSE v_prefix END, v_file_batch_size
            LOOP
                v_common_prefix := storage.get_common_prefix(v_current.name, v_prefix, delimiter_param);

                IF v_common_prefix IS NOT NULL THEN
                    -- Hit a folder: exit batch, let peek handle it
                    v_next_seek := v_current.name;
                    EXIT;
                END IF;

                -- Emit file
                name := v_current.name;
                id := v_current.id;
                updated_at := v_current.updated_at;
                created_at := v_current.created_at;
                last_accessed_at := v_current.last_accessed_at;
                metadata := v_current.metadata;
                RETURN NEXT;
                v_count := v_count + 1;

                -- Advance seek past this file
                IF v_is_asc THEN
                    v_next_seek := v_current.name || delimiter_param;
                ELSE
                    v_next_seek := v_current.name;
                END IF;

                EXIT WHEN v_count >= max_keys;
            END LOOP;
        END IF;
    END LOOP;
END;
$_$;


--
-- Name: operation(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.operation() RETURNS text
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    RETURN current_setting('storage.operation', true);
END;
$$;


--
-- Name: protect_delete(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.protect_delete() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Check if storage.allow_delete_query is set to 'true'
    IF COALESCE(current_setting('storage.allow_delete_query', true), 'false') != 'true' THEN
        RAISE EXCEPTION 'Direct deletion from storage tables is not allowed. Use the Storage API instead.'
            USING HINT = 'This prevents accidental data loss from orphaned objects.',
                  ERRCODE = '42501';
    END IF;
    RETURN NULL;
END;
$$;


--
-- Name: search(text, text, integer, integer, integer, text, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.search(prefix text, bucketname text, limits integer DEFAULT 100, levels integer DEFAULT 1, offsets integer DEFAULT 0, search text DEFAULT ''::text, sortcolumn text DEFAULT 'name'::text, sortorder text DEFAULT 'asc'::text) RETURNS TABLE(name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone, metadata jsonb)
    LANGUAGE plpgsql STABLE
    AS $_$
DECLARE
    v_peek_name TEXT;
    v_current RECORD;
    v_common_prefix TEXT;
    v_delimiter CONSTANT TEXT := '/';

    -- Configuration
    v_limit INT;
    v_prefix TEXT;
    v_prefix_lower TEXT;
    v_is_asc BOOLEAN;
    v_order_by TEXT;
    v_sort_order TEXT;
    v_upper_bound TEXT;
    v_file_batch_size INT;

    -- Dynamic SQL for batch query only
    v_batch_query TEXT;

    -- Seek state
    v_next_seek TEXT;
    v_count INT := 0;
    v_skipped INT := 0;
BEGIN
    -- ========================================================================
    -- INITIALIZATION
    -- ========================================================================
    v_limit := LEAST(coalesce(limits, 100), 1500);
    v_prefix := coalesce(prefix, '') || coalesce(search, '');
    v_prefix_lower := lower(v_prefix);
    v_is_asc := lower(coalesce(sortorder, 'asc')) = 'asc';
    v_file_batch_size := LEAST(GREATEST(v_limit * 2, 100), 1000);

    -- Validate sort column
    CASE lower(coalesce(sortcolumn, 'name'))
        WHEN 'name' THEN v_order_by := 'name';
        WHEN 'updated_at' THEN v_order_by := 'updated_at';
        WHEN 'created_at' THEN v_order_by := 'created_at';
        WHEN 'last_accessed_at' THEN v_order_by := 'last_accessed_at';
        ELSE v_order_by := 'name';
    END CASE;

    v_sort_order := CASE WHEN v_is_asc THEN 'asc' ELSE 'desc' END;

    -- ========================================================================
    -- NON-NAME SORTING: Use path_tokens approach (unchanged)
    -- ========================================================================
    IF v_order_by != 'name' THEN
        RETURN QUERY EXECUTE format(
            $sql$
            WITH folders AS (
                SELECT path_tokens[$1] AS folder
                FROM storage.objects
                WHERE objects.name ILIKE $2 || '%%'
                  AND bucket_id = $3
                  AND array_length(objects.path_tokens, 1) <> $1
                GROUP BY folder
                ORDER BY folder %s
            )
            (SELECT folder AS "name",
                   NULL::uuid AS id,
                   NULL::timestamptz AS updated_at,
                   NULL::timestamptz AS created_at,
                   NULL::timestamptz AS last_accessed_at,
                   NULL::jsonb AS metadata FROM folders)
            UNION ALL
            (SELECT path_tokens[$1] AS "name",
                   id, updated_at, created_at, last_accessed_at, metadata
             FROM storage.objects
             WHERE objects.name ILIKE $2 || '%%'
               AND bucket_id = $3
               AND array_length(objects.path_tokens, 1) = $1
             ORDER BY %I %s)
            LIMIT $4 OFFSET $5
            $sql$, v_sort_order, v_order_by, v_sort_order
        ) USING levels, v_prefix, bucketname, v_limit, offsets;
        RETURN;
    END IF;

    -- ========================================================================
    -- NAME SORTING: Hybrid skip-scan with batch optimization
    -- ========================================================================

    -- Calculate upper bound for prefix filtering
    IF v_prefix_lower = '' THEN
        v_upper_bound := NULL;
    ELSIF right(v_prefix_lower, 1) = v_delimiter THEN
        v_upper_bound := left(v_prefix_lower, -1) || chr(ascii(v_delimiter) + 1);
    ELSE
        v_upper_bound := left(v_prefix_lower, -1) || chr(ascii(right(v_prefix_lower, 1)) + 1);
    END IF;

    -- Build batch query (dynamic SQL - called infrequently, amortized over many rows)
    IF v_is_asc THEN
        IF v_upper_bound IS NOT NULL THEN
            v_batch_query := 'SELECT o.name, o.id, o.updated_at, o.created_at, o.last_accessed_at, o.metadata ' ||
                'FROM storage.objects o WHERE o.bucket_id = $1 AND lower(o.name) COLLATE "C" >= $2 ' ||
                'AND lower(o.name) COLLATE "C" < $3 ORDER BY lower(o.name) COLLATE "C" ASC LIMIT $4';
        ELSE
            v_batch_query := 'SELECT o.name, o.id, o.updated_at, o.created_at, o.last_accessed_at, o.metadata ' ||
                'FROM storage.objects o WHERE o.bucket_id = $1 AND lower(o.name) COLLATE "C" >= $2 ' ||
                'ORDER BY lower(o.name) COLLATE "C" ASC LIMIT $4';
        END IF;
    ELSE
        IF v_upper_bound IS NOT NULL THEN
            v_batch_query := 'SELECT o.name, o.id, o.updated_at, o.created_at, o.last_accessed_at, o.metadata ' ||
                'FROM storage.objects o WHERE o.bucket_id = $1 AND lower(o.name) COLLATE "C" < $2 ' ||
                'AND lower(o.name) COLLATE "C" >= $3 ORDER BY lower(o.name) COLLATE "C" DESC LIMIT $4';
        ELSE
            v_batch_query := 'SELECT o.name, o.id, o.updated_at, o.created_at, o.last_accessed_at, o.metadata ' ||
                'FROM storage.objects o WHERE o.bucket_id = $1 AND lower(o.name) COLLATE "C" < $2 ' ||
                'ORDER BY lower(o.name) COLLATE "C" DESC LIMIT $4';
        END IF;
    END IF;

    -- Initialize seek position
    IF v_is_asc THEN
        v_next_seek := v_prefix_lower;
    ELSE
        -- DESC: find the last item in range first (static SQL)
        IF v_upper_bound IS NOT NULL THEN
            SELECT o.name INTO v_peek_name FROM storage.objects o
            WHERE o.bucket_id = bucketname AND lower(o.name) COLLATE "C" >= v_prefix_lower AND lower(o.name) COLLATE "C" < v_upper_bound
            ORDER BY lower(o.name) COLLATE "C" DESC LIMIT 1;
        ELSIF v_prefix_lower <> '' THEN
            SELECT o.name INTO v_peek_name FROM storage.objects o
            WHERE o.bucket_id = bucketname AND lower(o.name) COLLATE "C" >= v_prefix_lower
            ORDER BY lower(o.name) COLLATE "C" DESC LIMIT 1;
        ELSE
            SELECT o.name INTO v_peek_name FROM storage.objects o
            WHERE o.bucket_id = bucketname
            ORDER BY lower(o.name) COLLATE "C" DESC LIMIT 1;
        END IF;

        IF v_peek_name IS NOT NULL THEN
            v_next_seek := lower(v_peek_name) || v_delimiter;
        ELSE
            RETURN;
        END IF;
    END IF;

    -- ========================================================================
    -- MAIN LOOP: Hybrid peek-then-batch algorithm
    -- Uses STATIC SQL for peek (hot path) and DYNAMIC SQL for batch
    -- ========================================================================
    LOOP
        EXIT WHEN v_count >= v_limit;

        -- STEP 1: PEEK using STATIC SQL (plan cached, very fast)
        IF v_is_asc THEN
            IF v_upper_bound IS NOT NULL THEN
                SELECT o.name INTO v_peek_name FROM storage.objects o
                WHERE o.bucket_id = bucketname AND lower(o.name) COLLATE "C" >= v_next_seek AND lower(o.name) COLLATE "C" < v_upper_bound
                ORDER BY lower(o.name) COLLATE "C" ASC LIMIT 1;
            ELSE
                SELECT o.name INTO v_peek_name FROM storage.objects o
                WHERE o.bucket_id = bucketname AND lower(o.name) COLLATE "C" >= v_next_seek
                ORDER BY lower(o.name) COLLATE "C" ASC LIMIT 1;
            END IF;
        ELSE
            IF v_upper_bound IS NOT NULL THEN
                SELECT o.name INTO v_peek_name FROM storage.objects o
                WHERE o.bucket_id = bucketname AND lower(o.name) COLLATE "C" < v_next_seek AND lower(o.name) COLLATE "C" >= v_prefix_lower
                ORDER BY lower(o.name) COLLATE "C" DESC LIMIT 1;
            ELSIF v_prefix_lower <> '' THEN
                SELECT o.name INTO v_peek_name FROM storage.objects o
                WHERE o.bucket_id = bucketname AND lower(o.name) COLLATE "C" < v_next_seek AND lower(o.name) COLLATE "C" >= v_prefix_lower
                ORDER BY lower(o.name) COLLATE "C" DESC LIMIT 1;
            ELSE
                SELECT o.name INTO v_peek_name FROM storage.objects o
                WHERE o.bucket_id = bucketname AND lower(o.name) COLLATE "C" < v_next_seek
                ORDER BY lower(o.name) COLLATE "C" DESC LIMIT 1;
            END IF;
        END IF;

        EXIT WHEN v_peek_name IS NULL;

        -- STEP 2: Check if this is a FOLDER or FILE
        v_common_prefix := storage.get_common_prefix(lower(v_peek_name), v_prefix_lower, v_delimiter);

        IF v_common_prefix IS NOT NULL THEN
            -- FOLDER: Handle offset, emit if needed, skip to next folder
            IF v_skipped < offsets THEN
                v_skipped := v_skipped + 1;
            ELSE
                name := split_part(rtrim(storage.get_common_prefix(v_peek_name, v_prefix, v_delimiter), v_delimiter), v_delimiter, levels);
                id := NULL;
                updated_at := NULL;
                created_at := NULL;
                last_accessed_at := NULL;
                metadata := NULL;
                RETURN NEXT;
                v_count := v_count + 1;
            END IF;

            -- Advance seek past the folder range
            IF v_is_asc THEN
                v_next_seek := lower(left(v_common_prefix, -1)) || chr(ascii(v_delimiter) + 1);
            ELSE
                v_next_seek := lower(v_common_prefix);
            END IF;
        ELSE
            -- FILE: Batch fetch using DYNAMIC SQL (overhead amortized over many rows)
            -- For ASC: upper_bound is the exclusive upper limit (< condition)
            -- For DESC: prefix_lower is the inclusive lower limit (>= condition)
            FOR v_current IN EXECUTE v_batch_query
                USING bucketname, v_next_seek,
                    CASE WHEN v_is_asc THEN COALESCE(v_upper_bound, v_prefix_lower) ELSE v_prefix_lower END, v_file_batch_size
            LOOP
                v_common_prefix := storage.get_common_prefix(lower(v_current.name), v_prefix_lower, v_delimiter);

                IF v_common_prefix IS NOT NULL THEN
                    -- Hit a folder: exit batch, let peek handle it
                    v_next_seek := lower(v_current.name);
                    EXIT;
                END IF;

                -- Handle offset skipping
                IF v_skipped < offsets THEN
                    v_skipped := v_skipped + 1;
                ELSE
                    -- Emit file
                    name := split_part(v_current.name, v_delimiter, levels);
                    id := v_current.id;
                    updated_at := v_current.updated_at;
                    created_at := v_current.created_at;
                    last_accessed_at := v_current.last_accessed_at;
                    metadata := v_current.metadata;
                    RETURN NEXT;
                    v_count := v_count + 1;
                END IF;

                -- Advance seek past this file
                IF v_is_asc THEN
                    v_next_seek := lower(v_current.name) || v_delimiter;
                ELSE
                    v_next_seek := lower(v_current.name);
                END IF;

                EXIT WHEN v_count >= v_limit;
            END LOOP;
        END IF;
    END LOOP;
END;
$_$;


--
-- Name: search_by_timestamp(text, text, integer, integer, text, text, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.search_by_timestamp(p_prefix text, p_bucket_id text, p_limit integer, p_level integer, p_start_after text, p_sort_order text, p_sort_column text, p_sort_column_after text) RETURNS TABLE(key text, name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone, metadata jsonb)
    LANGUAGE plpgsql STABLE
    AS $_$
DECLARE
    v_cursor_op text;
    v_query text;
    v_prefix text;
BEGIN
    v_prefix := coalesce(p_prefix, '');

    IF p_sort_order = 'asc' THEN
        v_cursor_op := '>';
    ELSE
        v_cursor_op := '<';
    END IF;

    v_query := format($sql$
        WITH raw_objects AS (
            SELECT
                o.name AS obj_name,
                o.id AS obj_id,
                o.updated_at AS obj_updated_at,
                o.created_at AS obj_created_at,
                o.last_accessed_at AS obj_last_accessed_at,
                o.metadata AS obj_metadata,
                storage.get_common_prefix(o.name, $1, '/') AS common_prefix
            FROM storage.objects o
            WHERE o.bucket_id = $2
              AND o.name COLLATE "C" LIKE $1 || '%%'
        ),
        -- Aggregate common prefixes (folders)
        -- Both created_at and updated_at use MIN(obj_created_at) to match the old prefixes table behavior
        aggregated_prefixes AS (
            SELECT
                rtrim(common_prefix, '/') AS name,
                NULL::uuid AS id,
                MIN(obj_created_at) AS updated_at,
                MIN(obj_created_at) AS created_at,
                NULL::timestamptz AS last_accessed_at,
                NULL::jsonb AS metadata,
                TRUE AS is_prefix
            FROM raw_objects
            WHERE common_prefix IS NOT NULL
            GROUP BY common_prefix
        ),
        leaf_objects AS (
            SELECT
                obj_name AS name,
                obj_id AS id,
                obj_updated_at AS updated_at,
                obj_created_at AS created_at,
                obj_last_accessed_at AS last_accessed_at,
                obj_metadata AS metadata,
                FALSE AS is_prefix
            FROM raw_objects
            WHERE common_prefix IS NULL
        ),
        combined AS (
            SELECT * FROM aggregated_prefixes
            UNION ALL
            SELECT * FROM leaf_objects
        ),
        filtered AS (
            SELECT *
            FROM combined
            WHERE (
                $5 = ''
                OR ROW(
                    date_trunc('milliseconds', %I),
                    name COLLATE "C"
                ) %s ROW(
                    COALESCE(NULLIF($6, '')::timestamptz, 'epoch'::timestamptz),
                    $5
                )
            )
        )
        SELECT
            split_part(name, '/', $3) AS key,
            name,
            id,
            updated_at,
            created_at,
            last_accessed_at,
            metadata
        FROM filtered
        ORDER BY
            COALESCE(date_trunc('milliseconds', %I), 'epoch'::timestamptz) %s,
            name COLLATE "C" %s
        LIMIT $4
    $sql$,
        p_sort_column,
        v_cursor_op,
        p_sort_column,
        p_sort_order,
        p_sort_order
    );

    RETURN QUERY EXECUTE v_query
    USING v_prefix, p_bucket_id, p_level, p_limit, p_start_after, p_sort_column_after;
END;
$_$;


--
-- Name: search_v2(text, text, integer, integer, text, text, text, text); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.search_v2(prefix text, bucket_name text, limits integer DEFAULT 100, levels integer DEFAULT 1, start_after text DEFAULT ''::text, sort_order text DEFAULT 'asc'::text, sort_column text DEFAULT 'name'::text, sort_column_after text DEFAULT ''::text) RETURNS TABLE(key text, name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone, metadata jsonb)
    LANGUAGE plpgsql STABLE
    AS $$
DECLARE
    v_sort_col text;
    v_sort_ord text;
    v_limit int;
BEGIN
    -- Cap limit to maximum of 1500 records
    v_limit := LEAST(coalesce(limits, 100), 1500);

    -- Validate and normalize sort_order
    v_sort_ord := lower(coalesce(sort_order, 'asc'));
    IF v_sort_ord NOT IN ('asc', 'desc') THEN
        v_sort_ord := 'asc';
    END IF;

    -- Validate and normalize sort_column
    v_sort_col := lower(coalesce(sort_column, 'name'));
    IF v_sort_col NOT IN ('name', 'updated_at', 'created_at') THEN
        v_sort_col := 'name';
    END IF;

    -- Route to appropriate implementation
    IF v_sort_col = 'name' THEN
        -- Use list_objects_with_delimiter for name sorting (most efficient: O(k * log n))
        RETURN QUERY
        SELECT
            split_part(l.name, '/', levels) AS key,
            l.name AS name,
            l.id,
            l.updated_at,
            l.created_at,
            l.last_accessed_at,
            l.metadata
        FROM storage.list_objects_with_delimiter(
            bucket_name,
            coalesce(prefix, ''),
            '/',
            v_limit,
            start_after,
            '',
            v_sort_ord
        ) l;
    ELSE
        -- Use aggregation approach for timestamp sorting
        -- Not efficient for large datasets but supports correct pagination
        RETURN QUERY SELECT * FROM storage.search_by_timestamp(
            prefix, bucket_name, v_limit, levels, start_after,
            v_sort_ord, v_sort_col, sort_column_after
        );
    END IF;
END;
$$;


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: storage; Owner: -
--

CREATE FUNCTION storage.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;


--
-- Name: http_request(); Type: FUNCTION; Schema: supabase_functions; Owner: -
--

CREATE FUNCTION supabase_functions.http_request() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'supabase_functions'
    AS $$
  DECLARE
    request_id bigint;
    payload jsonb;
    url text := TG_ARGV[0]::text;
    method text := TG_ARGV[1]::text;
    headers jsonb DEFAULT '{}'::jsonb;
    params jsonb DEFAULT '{}'::jsonb;
    timeout_ms integer DEFAULT 1000;
  BEGIN
    IF url IS NULL OR url = 'null' THEN
      RAISE EXCEPTION 'url argument is missing';
    END IF;

    IF method IS NULL OR method = 'null' THEN
      RAISE EXCEPTION 'method argument is missing';
    END IF;

    IF TG_ARGV[2] IS NULL OR TG_ARGV[2] = 'null' THEN
      headers = '{"Content-Type": "application/json"}'::jsonb;
    ELSE
      headers = TG_ARGV[2]::jsonb;
    END IF;

    IF TG_ARGV[3] IS NULL OR TG_ARGV[3] = 'null' THEN
      params = '{}'::jsonb;
    ELSE
      params = TG_ARGV[3]::jsonb;
    END IF;

    IF TG_ARGV[4] IS NULL OR TG_ARGV[4] = 'null' THEN
      timeout_ms = 1000;
    ELSE
      timeout_ms = TG_ARGV[4]::integer;
    END IF;

    CASE
      WHEN method = 'GET' THEN
        SELECT http_get INTO request_id FROM net.http_get(
          url,
          params,
          headers,
          timeout_ms
        );
      WHEN method = 'POST' THEN
        payload = jsonb_build_object(
          'old_record', OLD,
          'record', NEW,
          'type', TG_OP,
          'table', TG_TABLE_NAME,
          'schema', TG_TABLE_SCHEMA
        );

        SELECT http_post INTO request_id FROM net.http_post(
          url,
          payload,
          params,
          headers,
          timeout_ms
        );
      ELSE
        RAISE EXCEPTION 'method argument % is invalid', method;
    END CASE;

    INSERT INTO supabase_functions.hooks
      (hook_table_id, hook_name, request_id)
    VALUES
      (TG_RELID, TG_NAME, request_id);

    RETURN NEW;
  END
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: extensions; Type: TABLE; Schema: _realtime; Owner: -
--

CREATE TABLE _realtime.extensions (
    id uuid NOT NULL,
    type text,
    settings jsonb,
    tenant_external_id text,
    inserted_at timestamp(0) without time zone NOT NULL,
    updated_at timestamp(0) without time zone NOT NULL
);


--
-- Name: feature_flags; Type: TABLE; Schema: _realtime; Owner: -
--

CREATE TABLE _realtime.feature_flags (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    enabled boolean DEFAULT false NOT NULL,
    inserted_at timestamp(0) without time zone NOT NULL,
    updated_at timestamp(0) without time zone NOT NULL
);


--
-- Name: schema_migrations; Type: TABLE; Schema: _realtime; Owner: -
--

CREATE TABLE _realtime.schema_migrations (
    version bigint NOT NULL,
    inserted_at timestamp(0) without time zone
);


--
-- Name: tenants; Type: TABLE; Schema: _realtime; Owner: -
--

CREATE TABLE _realtime.tenants (
    id uuid NOT NULL,
    name text,
    external_id text,
    jwt_secret text,
    max_concurrent_users integer DEFAULT 200 NOT NULL,
    inserted_at timestamp(0) without time zone NOT NULL,
    updated_at timestamp(0) without time zone NOT NULL,
    max_events_per_second integer DEFAULT 100 NOT NULL,
    postgres_cdc_default text DEFAULT 'postgres_cdc_rls'::text,
    max_bytes_per_second integer DEFAULT 100000 NOT NULL,
    max_channels_per_client integer DEFAULT 100 NOT NULL,
    max_joins_per_second integer DEFAULT 500 NOT NULL,
    suspend boolean DEFAULT false,
    jwt_jwks jsonb,
    notify_private_alpha boolean DEFAULT false,
    private_only boolean DEFAULT false NOT NULL,
    migrations_ran integer DEFAULT 0,
    broadcast_adapter character varying(255) DEFAULT 'gen_rpc'::character varying,
    max_presence_events_per_second integer DEFAULT 1000,
    max_payload_size_in_kb integer DEFAULT 3000,
    max_client_presence_events_per_window integer,
    client_presence_window_ms integer,
    presence_enabled boolean DEFAULT false NOT NULL,
    feature_flags jsonb DEFAULT '{}'::jsonb NOT NULL,
    CONSTRAINT jwt_secret_or_jwt_jwks_required CHECK (((jwt_secret IS NOT NULL) OR (jwt_jwks IS NOT NULL)))
);


--
-- Name: audit_log_entries; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.audit_log_entries (
    instance_id uuid,
    id uuid NOT NULL,
    payload json,
    created_at timestamp with time zone,
    ip_address character varying(64) DEFAULT ''::character varying NOT NULL
);


--
-- Name: TABLE audit_log_entries; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.audit_log_entries IS 'Auth: Audit trail for user actions.';


--
-- Name: custom_oauth_providers; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.custom_oauth_providers (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    provider_type text NOT NULL,
    identifier text NOT NULL,
    name text NOT NULL,
    client_id text NOT NULL,
    client_secret text NOT NULL,
    acceptable_client_ids text[] DEFAULT '{}'::text[] NOT NULL,
    scopes text[] DEFAULT '{}'::text[] NOT NULL,
    pkce_enabled boolean DEFAULT true NOT NULL,
    attribute_mapping jsonb DEFAULT '{}'::jsonb NOT NULL,
    authorization_params jsonb DEFAULT '{}'::jsonb NOT NULL,
    enabled boolean DEFAULT true NOT NULL,
    email_optional boolean DEFAULT false NOT NULL,
    issuer text,
    discovery_url text,
    skip_nonce_check boolean DEFAULT false NOT NULL,
    cached_discovery jsonb,
    discovery_cached_at timestamp with time zone,
    authorization_url text,
    token_url text,
    userinfo_url text,
    jwks_uri text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    custom_claims_allowlist text[] DEFAULT '{}'::text[] NOT NULL,
    CONSTRAINT custom_oauth_providers_authorization_url_https CHECK (((authorization_url IS NULL) OR (authorization_url ~~ 'https://%'::text))),
    CONSTRAINT custom_oauth_providers_authorization_url_length CHECK (((authorization_url IS NULL) OR (char_length(authorization_url) <= 2048))),
    CONSTRAINT custom_oauth_providers_client_id_length CHECK (((char_length(client_id) >= 1) AND (char_length(client_id) <= 512))),
    CONSTRAINT custom_oauth_providers_discovery_url_length CHECK (((discovery_url IS NULL) OR (char_length(discovery_url) <= 2048))),
    CONSTRAINT custom_oauth_providers_identifier_format CHECK ((identifier ~ '^[a-z0-9][a-z0-9:-]{0,48}[a-z0-9]$'::text)),
    CONSTRAINT custom_oauth_providers_issuer_length CHECK (((issuer IS NULL) OR ((char_length(issuer) >= 1) AND (char_length(issuer) <= 2048)))),
    CONSTRAINT custom_oauth_providers_jwks_uri_https CHECK (((jwks_uri IS NULL) OR (jwks_uri ~~ 'https://%'::text))),
    CONSTRAINT custom_oauth_providers_jwks_uri_length CHECK (((jwks_uri IS NULL) OR (char_length(jwks_uri) <= 2048))),
    CONSTRAINT custom_oauth_providers_name_length CHECK (((char_length(name) >= 1) AND (char_length(name) <= 100))),
    CONSTRAINT custom_oauth_providers_oauth2_requires_endpoints CHECK (((provider_type <> 'oauth2'::text) OR ((authorization_url IS NOT NULL) AND (token_url IS NOT NULL) AND (userinfo_url IS NOT NULL)))),
    CONSTRAINT custom_oauth_providers_oidc_discovery_url_https CHECK (((provider_type <> 'oidc'::text) OR (discovery_url IS NULL) OR (discovery_url ~~ 'https://%'::text))),
    CONSTRAINT custom_oauth_providers_oidc_issuer_https CHECK (((provider_type <> 'oidc'::text) OR (issuer IS NULL) OR (issuer ~~ 'https://%'::text))),
    CONSTRAINT custom_oauth_providers_oidc_requires_issuer CHECK (((provider_type <> 'oidc'::text) OR (issuer IS NOT NULL))),
    CONSTRAINT custom_oauth_providers_provider_type_check CHECK ((provider_type = ANY (ARRAY['oauth2'::text, 'oidc'::text]))),
    CONSTRAINT custom_oauth_providers_token_url_https CHECK (((token_url IS NULL) OR (token_url ~~ 'https://%'::text))),
    CONSTRAINT custom_oauth_providers_token_url_length CHECK (((token_url IS NULL) OR (char_length(token_url) <= 2048))),
    CONSTRAINT custom_oauth_providers_userinfo_url_https CHECK (((userinfo_url IS NULL) OR (userinfo_url ~~ 'https://%'::text))),
    CONSTRAINT custom_oauth_providers_userinfo_url_length CHECK (((userinfo_url IS NULL) OR (char_length(userinfo_url) <= 2048)))
);


--
-- Name: flow_state; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.flow_state (
    id uuid NOT NULL,
    user_id uuid,
    auth_code text,
    code_challenge_method auth.code_challenge_method,
    code_challenge text,
    provider_type text NOT NULL,
    provider_access_token text,
    provider_refresh_token text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    authentication_method text NOT NULL,
    auth_code_issued_at timestamp with time zone,
    invite_token text,
    referrer text,
    oauth_client_state_id uuid,
    linking_target_id uuid,
    email_optional boolean DEFAULT false NOT NULL
);


--
-- Name: TABLE flow_state; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.flow_state IS 'Stores metadata for all OAuth/SSO login flows';


--
-- Name: identities; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.identities (
    provider_id text NOT NULL,
    user_id uuid NOT NULL,
    identity_data jsonb NOT NULL,
    provider text NOT NULL,
    last_sign_in_at timestamp with time zone,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    email text GENERATED ALWAYS AS (lower((identity_data ->> 'email'::text))) STORED,
    id uuid DEFAULT gen_random_uuid() NOT NULL
);


--
-- Name: TABLE identities; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.identities IS 'Auth: Stores identities associated to a user.';


--
-- Name: COLUMN identities.email; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.identities.email IS 'Auth: Email is a generated column that references the optional email property in the identity_data';


--
-- Name: instances; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.instances (
    id uuid NOT NULL,
    uuid uuid,
    raw_base_config text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: TABLE instances; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.instances IS 'Auth: Manages users across multiple sites.';


--
-- Name: mfa_amr_claims; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.mfa_amr_claims (
    session_id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    authentication_method text NOT NULL,
    id uuid NOT NULL
);


--
-- Name: TABLE mfa_amr_claims; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.mfa_amr_claims IS 'auth: stores authenticator method reference claims for multi factor authentication';


--
-- Name: mfa_challenges; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.mfa_challenges (
    id uuid NOT NULL,
    factor_id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    verified_at timestamp with time zone,
    ip_address inet NOT NULL,
    otp_code text,
    web_authn_session_data jsonb
);


--
-- Name: TABLE mfa_challenges; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.mfa_challenges IS 'auth: stores metadata about challenge requests made';


--
-- Name: mfa_factors; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.mfa_factors (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    friendly_name text,
    factor_type auth.factor_type NOT NULL,
    status auth.factor_status NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    secret text,
    phone text,
    last_challenged_at timestamp with time zone,
    web_authn_credential jsonb,
    web_authn_aaguid uuid,
    last_webauthn_challenge_data jsonb
);


--
-- Name: TABLE mfa_factors; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.mfa_factors IS 'auth: stores metadata about factors';


--
-- Name: COLUMN mfa_factors.last_webauthn_challenge_data; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.mfa_factors.last_webauthn_challenge_data IS 'Stores the latest WebAuthn challenge data including attestation/assertion for customer verification';


--
-- Name: oauth_authorizations; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.oauth_authorizations (
    id uuid NOT NULL,
    authorization_id text NOT NULL,
    client_id uuid NOT NULL,
    user_id uuid,
    redirect_uri text NOT NULL,
    scope text NOT NULL,
    state text,
    resource text,
    code_challenge text,
    code_challenge_method auth.code_challenge_method,
    response_type auth.oauth_response_type DEFAULT 'code'::auth.oauth_response_type NOT NULL,
    status auth.oauth_authorization_status DEFAULT 'pending'::auth.oauth_authorization_status NOT NULL,
    authorization_code text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone DEFAULT (now() + '00:03:00'::interval) NOT NULL,
    approved_at timestamp with time zone,
    nonce text,
    CONSTRAINT oauth_authorizations_authorization_code_length CHECK ((char_length(authorization_code) <= 255)),
    CONSTRAINT oauth_authorizations_code_challenge_length CHECK ((char_length(code_challenge) <= 128)),
    CONSTRAINT oauth_authorizations_expires_at_future CHECK ((expires_at > created_at)),
    CONSTRAINT oauth_authorizations_nonce_length CHECK ((char_length(nonce) <= 255)),
    CONSTRAINT oauth_authorizations_redirect_uri_length CHECK ((char_length(redirect_uri) <= 2048)),
    CONSTRAINT oauth_authorizations_resource_length CHECK ((char_length(resource) <= 2048)),
    CONSTRAINT oauth_authorizations_scope_length CHECK ((char_length(scope) <= 4096)),
    CONSTRAINT oauth_authorizations_state_length CHECK ((char_length(state) <= 4096))
);


--
-- Name: oauth_client_states; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.oauth_client_states (
    id uuid NOT NULL,
    provider_type text NOT NULL,
    code_verifier text,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: TABLE oauth_client_states; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.oauth_client_states IS 'Stores OAuth states for third-party provider authentication flows where Supabase acts as the OAuth client.';


--
-- Name: oauth_clients; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.oauth_clients (
    id uuid NOT NULL,
    client_secret_hash text,
    registration_type auth.oauth_registration_type NOT NULL,
    redirect_uris text NOT NULL,
    grant_types text NOT NULL,
    client_name text,
    client_uri text,
    logo_uri text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone,
    client_type auth.oauth_client_type DEFAULT 'confidential'::auth.oauth_client_type NOT NULL,
    token_endpoint_auth_method text NOT NULL,
    CONSTRAINT oauth_clients_client_name_length CHECK ((char_length(client_name) <= 1024)),
    CONSTRAINT oauth_clients_client_uri_length CHECK ((char_length(client_uri) <= 2048)),
    CONSTRAINT oauth_clients_logo_uri_length CHECK ((char_length(logo_uri) <= 2048)),
    CONSTRAINT oauth_clients_token_endpoint_auth_method_check CHECK ((token_endpoint_auth_method = ANY (ARRAY['client_secret_basic'::text, 'client_secret_post'::text, 'none'::text])))
);


--
-- Name: oauth_consents; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.oauth_consents (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    client_id uuid NOT NULL,
    scopes text NOT NULL,
    granted_at timestamp with time zone DEFAULT now() NOT NULL,
    revoked_at timestamp with time zone,
    CONSTRAINT oauth_consents_revoked_after_granted CHECK (((revoked_at IS NULL) OR (revoked_at >= granted_at))),
    CONSTRAINT oauth_consents_scopes_length CHECK ((char_length(scopes) <= 2048)),
    CONSTRAINT oauth_consents_scopes_not_empty CHECK ((char_length(TRIM(BOTH FROM scopes)) > 0))
);


--
-- Name: one_time_tokens; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.one_time_tokens (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    token_type auth.one_time_token_type NOT NULL,
    token_hash text NOT NULL,
    relates_to text NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT one_time_tokens_token_hash_check CHECK ((char_length(token_hash) > 0))
);


--
-- Name: refresh_tokens; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.refresh_tokens (
    instance_id uuid,
    id bigint NOT NULL,
    token character varying(255),
    user_id character varying(255),
    revoked boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    parent character varying(255),
    session_id uuid
);


--
-- Name: TABLE refresh_tokens; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.refresh_tokens IS 'Auth: Store of tokens used to refresh JWT tokens once they expire.';


--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE; Schema: auth; Owner: -
--

CREATE SEQUENCE auth.refresh_tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: auth; Owner: -
--

ALTER SEQUENCE auth.refresh_tokens_id_seq OWNED BY auth.refresh_tokens.id;


--
-- Name: saml_providers; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.saml_providers (
    id uuid NOT NULL,
    sso_provider_id uuid NOT NULL,
    entity_id text NOT NULL,
    metadata_xml text NOT NULL,
    metadata_url text,
    attribute_mapping jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    name_id_format text,
    CONSTRAINT "entity_id not empty" CHECK ((char_length(entity_id) > 0)),
    CONSTRAINT "metadata_url not empty" CHECK (((metadata_url = NULL::text) OR (char_length(metadata_url) > 0))),
    CONSTRAINT "metadata_xml not empty" CHECK ((char_length(metadata_xml) > 0))
);


--
-- Name: TABLE saml_providers; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.saml_providers IS 'Auth: Manages SAML Identity Provider connections.';


--
-- Name: saml_relay_states; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.saml_relay_states (
    id uuid NOT NULL,
    sso_provider_id uuid NOT NULL,
    request_id text NOT NULL,
    for_email text,
    redirect_to text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    flow_state_id uuid,
    CONSTRAINT "request_id not empty" CHECK ((char_length(request_id) > 0))
);


--
-- Name: TABLE saml_relay_states; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.saml_relay_states IS 'Auth: Contains SAML Relay State information for each Service Provider initiated login.';


--
-- Name: schema_migrations; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.schema_migrations (
    version character varying(255) NOT NULL
);


--
-- Name: TABLE schema_migrations; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.schema_migrations IS 'Auth: Manages updates to the auth system.';


--
-- Name: sessions; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.sessions (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    factor_id uuid,
    aal auth.aal_level,
    not_after timestamp with time zone,
    refreshed_at timestamp without time zone,
    user_agent text,
    ip inet,
    tag text,
    oauth_client_id uuid,
    refresh_token_hmac_key text,
    refresh_token_counter bigint,
    scopes text,
    CONSTRAINT sessions_scopes_length CHECK ((char_length(scopes) <= 4096))
);


--
-- Name: TABLE sessions; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.sessions IS 'Auth: Stores session data associated to a user.';


--
-- Name: COLUMN sessions.not_after; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sessions.not_after IS 'Auth: Not after is a nullable column that contains a timestamp after which the session should be regarded as expired.';


--
-- Name: COLUMN sessions.refresh_token_hmac_key; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sessions.refresh_token_hmac_key IS 'Holds a HMAC-SHA256 key used to sign refresh tokens for this session.';


--
-- Name: COLUMN sessions.refresh_token_counter; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sessions.refresh_token_counter IS 'Holds the ID (counter) of the last issued refresh token.';


--
-- Name: sso_domains; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.sso_domains (
    id uuid NOT NULL,
    sso_provider_id uuid NOT NULL,
    domain text NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    CONSTRAINT "domain not empty" CHECK ((char_length(domain) > 0))
);


--
-- Name: TABLE sso_domains; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.sso_domains IS 'Auth: Manages SSO email address domain mapping to an SSO Identity Provider.';


--
-- Name: sso_providers; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.sso_providers (
    id uuid NOT NULL,
    resource_id text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    disabled boolean,
    CONSTRAINT "resource_id not empty" CHECK (((resource_id = NULL::text) OR (char_length(resource_id) > 0)))
);


--
-- Name: TABLE sso_providers; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.sso_providers IS 'Auth: Manages SSO identity provider information; see saml_providers for SAML.';


--
-- Name: COLUMN sso_providers.resource_id; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.sso_providers.resource_id IS 'Auth: Uniquely identifies a SSO provider according to a user-chosen resource ID (case insensitive), useful in infrastructure as code.';


--
-- Name: users; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.users (
    instance_id uuid,
    id uuid NOT NULL,
    aud character varying(255),
    role character varying(255),
    email character varying(255),
    encrypted_password character varying(255),
    email_confirmed_at timestamp with time zone,
    invited_at timestamp with time zone,
    confirmation_token character varying(255),
    confirmation_sent_at timestamp with time zone,
    recovery_token character varying(255),
    recovery_sent_at timestamp with time zone,
    email_change_token_new character varying(255),
    email_change character varying(255),
    email_change_sent_at timestamp with time zone,
    last_sign_in_at timestamp with time zone,
    raw_app_meta_data jsonb,
    raw_user_meta_data jsonb,
    is_super_admin boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    phone text DEFAULT NULL::character varying,
    phone_confirmed_at timestamp with time zone,
    phone_change text DEFAULT ''::character varying,
    phone_change_token character varying(255) DEFAULT ''::character varying,
    phone_change_sent_at timestamp with time zone,
    confirmed_at timestamp with time zone GENERATED ALWAYS AS (LEAST(email_confirmed_at, phone_confirmed_at)) STORED,
    email_change_token_current character varying(255) DEFAULT ''::character varying,
    email_change_confirm_status smallint DEFAULT 0,
    banned_until timestamp with time zone,
    reauthentication_token character varying(255) DEFAULT ''::character varying,
    reauthentication_sent_at timestamp with time zone,
    is_sso_user boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone,
    is_anonymous boolean DEFAULT false NOT NULL,
    CONSTRAINT users_email_change_confirm_status_check CHECK (((email_change_confirm_status >= 0) AND (email_change_confirm_status <= 2)))
);


--
-- Name: TABLE users; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON TABLE auth.users IS 'Auth: Stores user login data within a secure schema.';


--
-- Name: COLUMN users.is_sso_user; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON COLUMN auth.users.is_sso_user IS 'Auth: Set this column to true when the account comes from SSO. These accounts can have duplicate emails.';


--
-- Name: webauthn_challenges; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.webauthn_challenges (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid,
    challenge_type text NOT NULL,
    session_data jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    CONSTRAINT webauthn_challenges_challenge_type_check CHECK ((challenge_type = ANY (ARRAY['signup'::text, 'registration'::text, 'authentication'::text])))
);


--
-- Name: webauthn_credentials; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.webauthn_credentials (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    credential_id bytea NOT NULL,
    public_key bytea NOT NULL,
    attestation_type text DEFAULT ''::text NOT NULL,
    aaguid uuid,
    sign_count bigint DEFAULT 0 NOT NULL,
    transports jsonb DEFAULT '[]'::jsonb NOT NULL,
    backup_eligible boolean DEFAULT false NOT NULL,
    backed_up boolean DEFAULT false NOT NULL,
    friendly_name text DEFAULT ''::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    last_used_at timestamp with time zone
);


--
-- Name: deployments; Type: TABLE; Schema: deploy; Owner: -
--

CREATE TABLE deploy.deployments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    shutdown_time timestamp with time zone,
    image_id text,
    is_active boolean DEFAULT true NOT NULL,
    build_log text
);


--
-- Name: projects; Type: TABLE; Schema: deploy; Owner: -
--

CREATE TABLE deploy.projects (
    id uuid NOT NULL,
    github_oath_access_token text,
    user_callback_url text,
    watch_path text,
    entrypoint text,
    git_branch text,
    git_url text,
    pack_name text
);


--
-- Name: actions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.actions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    session_id uuid NOT NULL,
    agent_id uuid NOT NULL,
    action_type text,
    logs text,
    screenshot text,
    params text,
    returns text,
    init_timestamp timestamp with time zone NOT NULL,
    end_timestamp timestamp with time zone NOT NULL
);


--
-- Name: agents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agents (
    id uuid NOT NULL,
    session_id uuid NOT NULL,
    name text,
    logs text
);


--
-- Name: ai_chat_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_chat_messages (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    session_id uuid NOT NULL,
    sequence_index integer NOT NULL,
    role text NOT NULL,
    external_message_id text,
    content text NOT NULL,
    token_count integer,
    message_created_at timestamp with time zone,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ai_chat_messages_role_check CHECK ((role = ANY (ARRAY['user'::text, 'assistant'::text, 'system'::text, 'tool'::text]))),
    CONSTRAINT ai_chat_messages_sequence_check CHECK ((sequence_index >= 0)),
    CONSTRAINT ai_chat_messages_token_check CHECK (((token_count IS NULL) OR (token_count >= 0)))
);


--
-- Name: ai_chat_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_chat_sessions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    user_id uuid,
    employee_id text NOT NULL,
    employee_name text NOT NULL,
    source text NOT NULL,
    external_conversation_id text,
    title text,
    task_id text DEFAULT 'unassigned'::text NOT NULL,
    task_title text,
    model text,
    status text DEFAULT 'ok'::text NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    ended_at timestamp with time zone,
    duration_ms bigint,
    prompt_tokens integer DEFAULT 0 NOT NULL,
    completion_tokens integer DEFAULT 0 NOT NULL,
    total_tokens integer DEFAULT 0 NOT NULL,
    cost numeric(18,9) DEFAULT 0 NOT NULL,
    error_count integer DEFAULT 0 NOT NULL,
    trace_id text,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    content_fingerprint text,
    gateway_instance_id text,
    gateway_event_id text,
    context_complete boolean DEFAULT false NOT NULL,
    content_complete boolean DEFAULT false NOT NULL,
    context_source text,
    CONSTRAINT ai_chat_sessions_cost_check CHECK ((cost >= (0)::numeric)),
    CONSTRAINT ai_chat_sessions_duration_check CHECK (((duration_ms IS NULL) OR (duration_ms >= 0))),
    CONSTRAINT ai_chat_sessions_error_count_check CHECK ((error_count >= 0)),
    CONSTRAINT ai_chat_sessions_source_check CHECK ((source = ANY (ARRAY['cc_switch'::text, 'chatgpt_web'::text, 'chatgpt_desktop'::text, 'openai_compliance'::text, 'smartbrain'::text, 'ai_gateway'::text, 'personal_api'::text]))),
    CONSTRAINT ai_chat_sessions_status_check CHECK ((status = ANY (ARRAY['ok'::text, 'error'::text, 'partial'::text]))),
    CONSTRAINT ai_chat_sessions_token_check CHECK (((prompt_tokens >= 0) AND (completion_tokens >= 0) AND (total_tokens >= 0)))
);


--
-- Name: ai_daily_work_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_daily_work_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    employee_id text NOT NULL,
    employee_name text NOT NULL,
    work_date date NOT NULL,
    timezone text DEFAULT 'Asia/Shanghai'::text NOT NULL,
    status text NOT NULL,
    report_markdown text,
    work_items jsonb DEFAULT '[]'::jsonb NOT NULL,
    source_session_ids jsonb DEFAULT '[]'::jsonb NOT NULL,
    source_count integer DEFAULT 0 NOT NULL,
    model text NOT NULL,
    generated_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    conversation_count integer DEFAULT 0 NOT NULL,
    wiki_upload_count integer DEFAULT 0 NOT NULL,
    pending_wiki_count integer DEFAULT 0 NOT NULL,
    failed_wiki_count integer DEFAULT 0 NOT NULL,
    project_breakdown jsonb DEFAULT '{}'::jsonb NOT NULL,
    CONSTRAINT ai_daily_work_logs_conversation_count_check CHECK ((conversation_count >= 0)),
    CONSTRAINT ai_daily_work_logs_failed_wiki_count_check CHECK ((failed_wiki_count >= 0)),
    CONSTRAINT ai_daily_work_logs_pending_wiki_count_check CHECK ((pending_wiki_count >= 0)),
    CONSTRAINT ai_daily_work_logs_report_check CHECK ((((status = 'ready'::text) AND (report_markdown IS NOT NULL) AND (jsonb_array_length(work_items) > 0)) OR ((status = 'empty'::text) AND (report_markdown IS NULL) AND (jsonb_array_length(work_items) = 0)))),
    CONSTRAINT ai_daily_work_logs_source_count_check CHECK ((source_count >= 0)),
    CONSTRAINT ai_daily_work_logs_status_check CHECK ((status = ANY (ARRAY['ready'::text, 'empty'::text]))),
    CONSTRAINT ai_daily_work_logs_timezone_check CHECK ((timezone = 'Asia/Shanghai'::text)),
    CONSTRAINT ai_daily_work_logs_wiki_upload_count_check CHECK ((wiki_upload_count >= 0))
);


--
-- Name: ai_gateway_admissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_gateway_admissions (
    id uuid NOT NULL,
    gateway_instance_id text NOT NULL,
    key_id uuid NOT NULL,
    user_id uuid NOT NULL,
    request_sha256 text NOT NULL,
    receipt_hash text NOT NULL,
    admitted_at timestamp with time zone DEFAULT now() NOT NULL,
    event_sha256 text,
    event_payload jsonb,
    delivered_at timestamp with time zone,
    CONSTRAINT ai_gateway_admissions_check CHECK ((((event_sha256 IS NULL) AND (event_payload IS NULL) AND (delivered_at IS NULL)) OR ((event_sha256 IS NOT NULL) AND (event_payload IS NOT NULL) AND (delivered_at IS NOT NULL)))),
    CONSTRAINT ai_gateway_admissions_event_sha256_check CHECK ((event_sha256 ~ '^[0-9a-f]{64}$'::text)),
    CONSTRAINT ai_gateway_admissions_gateway_instance_id_check CHECK (((length(gateway_instance_id) >= 1) AND (length(gateway_instance_id) <= 120))),
    CONSTRAINT ai_gateway_admissions_receipt_hash_check CHECK ((receipt_hash ~ '^[0-9a-f]{64}$'::text)),
    CONSTRAINT ai_gateway_admissions_request_sha256_check CHECK ((request_sha256 ~ '^[0-9a-f]{64}$'::text))
);


--
-- Name: ai_gateway_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_gateway_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    gateway_instance_id text NOT NULL,
    event_id text NOT NULL,
    request_id text,
    key_id uuid,
    user_id uuid NOT NULL,
    employee_id text NOT NULL,
    employee_name text NOT NULL,
    model text DEFAULT ''::text NOT NULL,
    request_model text DEFAULT ''::text NOT NULL,
    requested_model text DEFAULT ''::text NOT NULL,
    resolved_model text DEFAULT ''::text NOT NULL,
    upstream_model text DEFAULT ''::text NOT NULL,
    provider text DEFAULT ''::text NOT NULL,
    app_type text DEFAULT 'codex'::text NOT NULL,
    status_code integer DEFAULT 200 NOT NULL,
    input_tokens bigint DEFAULT 0 NOT NULL,
    output_tokens bigint DEFAULT 0 NOT NULL,
    cache_read_tokens bigint DEFAULT 0 NOT NULL,
    cache_creation_tokens bigint DEFAULT 0 NOT NULL,
    cached_input_tokens bigint DEFAULT 0 NOT NULL,
    cache_write_tokens bigint DEFAULT 0 NOT NULL,
    reasoning_tokens bigint DEFAULT 0 NOT NULL,
    input_token_semantics integer DEFAULT 0 NOT NULL,
    token_semantics_version integer DEFAULT 1 NOT NULL,
    total_tokens bigint DEFAULT 0 NOT NULL,
    usage_missing boolean DEFAULT false NOT NULL,
    raw_usage jsonb DEFAULT '{}'::jsonb NOT NULL,
    total_cost_usd double precision DEFAULT 0 NOT NULL,
    latency_ms integer DEFAULT 0 NOT NULL,
    error_message text,
    usage_date date DEFAULT ((now() AT TIME ZONE 'Asia/Shanghai'::text))::date NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    chat_session_id uuid,
    conversation_id text,
    context_complete boolean DEFAULT false NOT NULL,
    content_complete boolean DEFAULT false NOT NULL,
    content_sync_status text DEFAULT 'not_requested'::text NOT NULL,
    CONSTRAINT ai_gateway_events_cache_creation_tokens_check CHECK ((cache_creation_tokens >= 0)),
    CONSTRAINT ai_gateway_events_cache_read_tokens_check CHECK ((cache_read_tokens >= 0)),
    CONSTRAINT ai_gateway_events_cache_write_tokens_check CHECK ((cache_write_tokens >= 0)),
    CONSTRAINT ai_gateway_events_cached_input_tokens_check CHECK ((cached_input_tokens >= 0)),
    CONSTRAINT ai_gateway_events_content_sync_status_check CHECK ((content_sync_status = ANY (ARRAY['not_requested'::text, 'pending'::text, 'synced'::text, 'failed'::text]))),
    CONSTRAINT ai_gateway_events_input_token_semantics_check CHECK ((input_token_semantics >= 0)),
    CONSTRAINT ai_gateway_events_input_tokens_check CHECK ((input_tokens >= 0)),
    CONSTRAINT ai_gateway_events_latency_ms_check CHECK ((latency_ms >= 0)),
    CONSTRAINT ai_gateway_events_output_tokens_check CHECK ((output_tokens >= 0)),
    CONSTRAINT ai_gateway_events_reasoning_tokens_check CHECK ((reasoning_tokens >= 0)),
    CONSTRAINT ai_gateway_events_token_semantics_version_check CHECK ((token_semantics_version >= 0)),
    CONSTRAINT ai_gateway_events_total_cost_usd_check CHECK ((total_cost_usd >= (0)::double precision)),
    CONSTRAINT ai_gateway_events_total_tokens_check CHECK ((total_tokens >= 0))
);


--
-- Name: ai_gateway_key_allowances; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_gateway_key_allowances (
    user_id uuid NOT NULL,
    max_active_keys integer DEFAULT 1 NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ai_gateway_key_allowances_max_active_keys_check CHECK (((max_active_keys >= 1) AND (max_active_keys <= 100)))
);


--
-- Name: ai_gateway_key_projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_gateway_key_projects (
    key_id uuid NOT NULL,
    user_id uuid NOT NULL,
    project_id uuid NOT NULL,
    project_name text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ai_gateway_key_projects_project_name_check CHECK ((length(project_name) > 0))
);


--
-- Name: TABLE ai_gateway_key_projects; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.ai_gateway_key_projects IS 'Immutable project attribution for newly created personal API keys; project cost joins the trusted event ledger by key_id and user_id, never client project metadata.';


--
-- Name: ai_gateway_key_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_gateway_key_requests (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    reviewer_id uuid,
    requested_limit integer,
    reason text NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    review_comment text DEFAULT ''::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    reviewed_at timestamp with time zone,
    reviewed_by_user_id uuid,
    requested_total integer NOT NULL,
    reviewed_by uuid,
    CONSTRAINT ai_gateway_key_requests_reason_check CHECK (((length(btrim(reason)) >= 1) AND (length(btrim(reason)) <= 2000))),
    CONSTRAINT ai_gateway_key_requests_requested_limit_check CHECK (((requested_limit >= 2) AND (requested_limit <= 100))),
    CONSTRAINT ai_gateway_key_requests_requested_total_check CHECK ((requested_total >= 2)),
    CONSTRAINT ai_gateway_key_requests_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text, 'cancelled'::text])))
);


--
-- Name: ai_gateway_keys; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_gateway_keys (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    key_hash text NOT NULL,
    key_prefix text NOT NULL,
    label text DEFAULT 'SmartBrain Gateway'::text NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    last_used_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    revoked_at timestamp with time zone,
    hidden_at timestamp with time zone
);


--
-- Name: ai_monitor_devices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_monitor_devices (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    user_id uuid,
    employee_id text NOT NULL,
    employee_name text NOT NULL,
    device_id text NOT NULL,
    device_name text,
    installer_version text,
    os text,
    components jsonb DEFAULT '{}'::jsonb NOT NULL,
    last_seen_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ai_monitor_devices_components_check CHECK ((jsonb_typeof(components) = 'object'::text)),
    CONSTRAINT ai_monitor_devices_device_id_check CHECK ((length(device_id) >= 3))
);


--
-- Name: ai_usage_leaderboard_daily; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_usage_leaderboard_daily (
    usage_date date NOT NULL,
    user_id uuid NOT NULL,
    employee_id text NOT NULL,
    employee_name text NOT NULL,
    origin text NOT NULL,
    source text NOT NULL,
    app text NOT NULL,
    model text DEFAULT ''::text NOT NULL,
    request_count bigint DEFAULT 0 NOT NULL,
    total_tokens bigint DEFAULT 0 NOT NULL,
    input_tokens bigint DEFAULT 0 NOT NULL,
    output_tokens bigint DEFAULT 0 NOT NULL,
    cache_read_tokens bigint DEFAULT 0 NOT NULL,
    cache_creation_tokens bigint DEFAULT 0 NOT NULL,
    error_count bigint DEFAULT 0 NOT NULL,
    total_cost_usd numeric DEFAULT 0 NOT NULL,
    refreshed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ai_usage_leaderboard_daily_origin_check CHECK ((origin = ANY (ARRAY['official'::text, 'shared'::text, 'session'::text])))
);


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id bigint NOT NULL,
    user_id uuid,
    action text NOT NULL,
    resource_type text,
    resource_id text,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    ip_address inet,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT audit_logs_action_check CHECK ((action = ANY (ARRAY['upload'::text, 'search'::text, 'answer'::text, 'login'::text, 'logout'::text, 'delete_document'::text, 'add_member'::text, 'remove_member'::text, 'create_project'::text, 'update_project'::text, 'delete_project'::text, 'reset_member_password'::text, 'workday_summary'::text, 'workday_enroll'::text, 'ai_chat_ingest'::text, 'ai_chat_list'::text, 'ai_monitor_device_register'::text, 'ai_monitor_status'::text, 'project_memory_repository_upsert'::text, 'project_memory_draft_create'::text, 'project_memory_review'::text, 'material_batch_upload'::text, 'knowledge_ledger_view'::text, 'ai_usage_view'::text, 'ai_usage_report'::text, 'ai_usage_sync'::text, 'project_wiki_compile'::text, 'project_wiki_view'::text, 'project_wiki_review'::text, 'member_wiki_view'::text, 'meeting_summary_view'::text, 'meeting_summary_create'::text, 'update_profile'::text, 'change_password'::text, 'create_department'::text, 'update_department'::text, 'delete_department'::text, 'rename_member_username'::text, 'request_project_creation'::text, 'review_project_creation'::text, 'create_team_member'::text, 'deactivate_team_member'::text, 'reactivate_team_member'::text, 'rename_team_member_username'::text, 'reset_team_member_password'::text, 'project_department_migration'::text, 'ai_shared_session_start'::text, 'ai_shared_session_schedule'::text, 'ai_shared_session_stop'::text, 'ai_shared_session_finalize'::text])))
);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: billing_audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.billing_audit_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    org_id uuid NOT NULL,
    user_id uuid NOT NULL,
    action character varying(50) NOT NULL,
    details jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: billing_periods; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.billing_periods (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    org_id uuid NOT NULL,
    period_start timestamp without time zone NOT NULL,
    period_end timestamp without time zone NOT NULL,
    stripe_invoice_id character varying(255),
    seat_cost integer DEFAULT 0 NOT NULL,
    seat_count integer DEFAULT 0 NOT NULL,
    usage_costs jsonb DEFAULT '{}'::jsonb NOT NULL,
    usage_quantities jsonb DEFAULT '{}'::jsonb NOT NULL,
    total_cost integer DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying,
    invoiced_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: cc_switch_attributed_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cc_switch_attributed_requests (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    session_id uuid NOT NULL,
    project_id uuid,
    target_user_id uuid NOT NULL,
    target_employee_id text NOT NULL,
    target_employee_name text NOT NULL,
    device_id text NOT NULL,
    request_id text NOT NULL,
    requested_at timestamp with time zone NOT NULL,
    usage_date date NOT NULL,
    app_type text NOT NULL,
    provider_id text NOT NULL,
    model text NOT NULL,
    request_model text DEFAULT ''::text NOT NULL,
    pricing_model text DEFAULT ''::text NOT NULL,
    status_code integer DEFAULT 0 NOT NULL,
    input_tokens bigint DEFAULT 0 NOT NULL,
    output_tokens bigint DEFAULT 0 NOT NULL,
    cache_read_tokens bigint DEFAULT 0 NOT NULL,
    cache_creation_tokens bigint DEFAULT 0 NOT NULL,
    total_tokens bigint DEFAULT 0 NOT NULL,
    total_cost_usd double precision DEFAULT 0 NOT NULL,
    input_token_semantics integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT cc_switch_attributed_requests_cache_creation_tokens_check CHECK ((cache_creation_tokens >= 0)),
    CONSTRAINT cc_switch_attributed_requests_cache_read_tokens_check CHECK ((cache_read_tokens >= 0)),
    CONSTRAINT cc_switch_attributed_requests_input_token_semantics_check CHECK ((input_token_semantics >= 0)),
    CONSTRAINT cc_switch_attributed_requests_input_tokens_check CHECK ((input_tokens >= 0)),
    CONSTRAINT cc_switch_attributed_requests_output_tokens_check CHECK ((output_tokens >= 0)),
    CONSTRAINT cc_switch_attributed_requests_total_cost_usd_check CHECK ((total_cost_usd >= (0)::double precision)),
    CONSTRAINT cc_switch_attributed_requests_total_tokens_check CHECK ((total_tokens >= 0))
);


--
-- Name: cc_switch_attribution_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cc_switch_attribution_sessions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid,
    target_user_id uuid NOT NULL,
    target_employee_id text NOT NULL,
    target_employee_name text NOT NULL,
    device_id text,
    stop_mode text NOT NULL,
    stop_reason text,
    status text DEFAULT 'starting'::text NOT NULL,
    activation_token_hash text NOT NULL,
    activation_expires_at timestamp with time zone NOT NULL,
    requested_at timestamp with time zone DEFAULT now() NOT NULL,
    started_at timestamp with time zone,
    scheduled_stop_at timestamp with time zone NOT NULL,
    actual_stop_at timestamp with time zone,
    start_watermark text,
    request_count bigint DEFAULT 0 NOT NULL,
    input_tokens bigint DEFAULT 0 NOT NULL,
    output_tokens bigint DEFAULT 0 NOT NULL,
    cache_read_tokens bigint DEFAULT 0 NOT NULL,
    cache_creation_tokens bigint DEFAULT 0 NOT NULL,
    total_tokens bigint DEFAULT 0 NOT NULL,
    total_cost_usd double precision DEFAULT 0 NOT NULL,
    finalized_at timestamp with time zone,
    error_message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    last_synced_at timestamp with time zone,
    last_synced_watermark text,
    CONSTRAINT cc_switch_attribution_sessions_cache_creation_tokens_check CHECK ((cache_creation_tokens >= 0)),
    CONSTRAINT cc_switch_attribution_sessions_cache_read_tokens_check CHECK ((cache_read_tokens >= 0)),
    CONSTRAINT cc_switch_attribution_sessions_input_tokens_check CHECK ((input_tokens >= 0)),
    CONSTRAINT cc_switch_attribution_sessions_output_tokens_check CHECK ((output_tokens >= 0)),
    CONSTRAINT cc_switch_attribution_sessions_request_count_check CHECK ((request_count >= 0)),
    CONSTRAINT cc_switch_attribution_sessions_status_check CHECK ((status = ANY (ARRAY['starting'::text, 'active'::text, 'finalizing'::text, 'pending_sync'::text, 'finalized'::text, 'cancelled'::text, 'expired'::text]))),
    CONSTRAINT cc_switch_attribution_sessions_stop_mode_check CHECK ((stop_mode = ANY (ARRAY['default_19'::text, 'custom'::text, 'manual_only'::text]))),
    CONSTRAINT cc_switch_attribution_sessions_stop_reason_check CHECK (((stop_reason IS NULL) OR (stop_reason = ANY (ARRAY['manual'::text, 'scheduled'::text, 'replaced_by_next_user'::text, 'admin_forced'::text, 'safety_timeout'::text])))),
    CONSTRAINT cc_switch_attribution_sessions_total_cost_usd_check CHECK ((total_cost_usd >= (0)::double precision)),
    CONSTRAINT cc_switch_attribution_sessions_total_tokens_check CHECK ((total_tokens >= 0))
);


--
-- Name: COLUMN cc_switch_attribution_sessions.project_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cc_switch_attribution_sessions.project_id IS 'Legacy optional attribution only. New temporary Token Monitor sessions are member-scoped and store NULL.';


--
-- Name: COLUMN cc_switch_attribution_sessions.last_synced_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cc_switch_attribution_sessions.last_synced_at IS 'Most recent successful incremental device sync.';


--
-- Name: COLUMN cc_switch_attribution_sessions.last_synced_watermark; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cc_switch_attribution_sessions.last_synced_watermark IS 'Client cursor acknowledged in the same transaction as the incremental sync.';


--
-- Name: cc_switch_temporary_monitor_probes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cc_switch_temporary_monitor_probes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    target_user_id uuid NOT NULL,
    probe_token_hash text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    detected_at timestamp with time zone,
    consumed_at timestamp with time zone,
    device_id text,
    installer_version text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE cc_switch_temporary_monitor_probes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cc_switch_temporary_monitor_probes IS 'Short-lived account-scoped installation handshakes for the standalone temporary Token Monitor.';


--
-- Name: cc_switch_usage_daily; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cc_switch_usage_daily (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    user_id uuid NOT NULL,
    employee_id text NOT NULL,
    employee_name text NOT NULL,
    device_id text NOT NULL,
    usage_date date NOT NULL,
    app_type text NOT NULL,
    provider_id text NOT NULL,
    model text NOT NULL,
    request_model text DEFAULT ''::text NOT NULL,
    pricing_model text DEFAULT ''::text NOT NULL,
    request_count bigint DEFAULT 0 NOT NULL,
    success_count bigint DEFAULT 0 NOT NULL,
    input_tokens bigint DEFAULT 0 NOT NULL,
    output_tokens bigint DEFAULT 0 NOT NULL,
    cache_read_tokens bigint DEFAULT 0 NOT NULL,
    cache_creation_tokens bigint DEFAULT 0 NOT NULL,
    total_tokens bigint DEFAULT 0 NOT NULL,
    total_cost_usd double precision DEFAULT 0 NOT NULL,
    input_token_semantics integer DEFAULT 0 NOT NULL,
    source_table text NOT NULL,
    synced_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    content_fingerprint text,
    CONSTRAINT cc_switch_usage_daily_cache_creation_tokens_check CHECK ((cache_creation_tokens >= 0)),
    CONSTRAINT cc_switch_usage_daily_cache_read_tokens_check CHECK ((cache_read_tokens >= 0)),
    CONSTRAINT cc_switch_usage_daily_input_token_semantics_check CHECK ((input_token_semantics >= 0)),
    CONSTRAINT cc_switch_usage_daily_input_tokens_check CHECK ((input_tokens >= 0)),
    CONSTRAINT cc_switch_usage_daily_output_tokens_check CHECK ((output_tokens >= 0)),
    CONSTRAINT cc_switch_usage_daily_request_count_check CHECK ((request_count >= 0)),
    CONSTRAINT cc_switch_usage_daily_source_table_check CHECK ((source_table = ANY (ARRAY['usage_daily_rollups'::text, 'proxy_request_logs'::text]))),
    CONSTRAINT cc_switch_usage_daily_success_count_check CHECK ((success_count >= 0)),
    CONSTRAINT cc_switch_usage_daily_total_cost_usd_check CHECK ((total_cost_usd >= (0)::double precision)),
    CONSTRAINT cc_switch_usage_daily_total_tokens_check CHECK ((total_tokens >= 0))
);


--
-- Name: cc_switch_usage_sync_status; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cc_switch_usage_sync_status (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    user_id uuid NOT NULL,
    employee_id text NOT NULL,
    employee_name text NOT NULL,
    device_id text NOT NULL,
    trigger text NOT NULL,
    request_id uuid,
    range_start date NOT NULL,
    range_end date NOT NULL,
    status text NOT NULL,
    cc_switch_running boolean NOT NULL,
    source_table text,
    row_count integer DEFAULT 0 NOT NULL,
    request_count bigint DEFAULT 0 NOT NULL,
    total_tokens bigint DEFAULT 0 NOT NULL,
    attempted_at timestamp with time zone NOT NULL,
    last_success_at timestamp with time zone,
    error_message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    last_ingest_accepted_at timestamp with time zone,
    last_ingest_receipt_id uuid,
    last_success_ingest_accepted_at timestamp with time zone,
    last_success_ingest_receipt_id uuid,
    CONSTRAINT cc_switch_usage_sync_status_request_count_check CHECK ((request_count >= 0)),
    CONSTRAINT cc_switch_usage_sync_status_row_count_check CHECK ((row_count >= 0)),
    CONSTRAINT cc_switch_usage_sync_status_source_table_check CHECK (((source_table IS NULL) OR (source_table = ANY (ARRAY['usage_daily_rollups'::text, 'proxy_request_logs'::text])))),
    CONSTRAINT cc_switch_usage_sync_status_status_check CHECK ((status = ANY (ARRAY['ok'::text, 'not_running'::text, 'error'::text]))),
    CONSTRAINT cc_switch_usage_sync_status_total_tokens_check CHECK ((total_tokens >= 0)),
    CONSTRAINT cc_switch_usage_sync_status_trigger_check CHECK ((trigger = ANY (ARRAY['automatic'::text, 'manual'::text])))
);


--
-- Name: customers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customers (
    id uuid NOT NULL,
    stripe_customer_id text
);


--
-- Name: departments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.departments (
    id text NOT NULL,
    name text NOT NULL,
    sort_order integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by_user_id uuid,
    parent_id text,
    allows_projects boolean DEFAULT true NOT NULL,
    is_direct boolean DEFAULT false NOT NULL,
    CONSTRAINT departments_direct_category_shape_check CHECK (((NOT is_direct) OR ((parent_id IS NOT NULL) AND allows_projects AND (name = '直属分级'::text)))),
    CONSTRAINT departments_id_check CHECK ((id ~ '^[a-z][a-z0-9_-]{1,39}$'::text)),
    CONSTRAINT departments_name_check CHECK (((char_length(btrim(name)) >= 1) AND (char_length(btrim(name)) <= 80))),
    CONSTRAINT departments_parent_not_self_check CHECK (((parent_id IS NULL) OR (parent_id <> id)))
);


--
-- Name: developer_errors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.developer_errors (
    id bigint NOT NULL,
    api_key uuid NOT NULL,
    sdk_version text,
    type text,
    message text,
    stack_trace text,
    host_env jsonb,
    "timestamp" timestamp with time zone DEFAULT now(),
    session_id uuid
);


--
-- Name: developer_errors_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.developer_errors ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.developer_errors_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: document_chunks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_chunks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    document_id uuid NOT NULL,
    project_id uuid NOT NULL,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    token_count integer NOT NULL,
    source_page integer,
    source_line integer,
    embedding public.vector(384) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT document_chunks_chunk_index_check CHECK ((chunk_index >= 0)),
    CONSTRAINT document_chunks_token_count_check CHECK ((token_count > 0))
);


--
-- Name: document_chunks_v2; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_chunks_v2 (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    document_id uuid NOT NULL,
    project_id uuid NOT NULL,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    token_count integer NOT NULL,
    source_page integer,
    source_line integer,
    heading_path text,
    fts_text text DEFAULT ''::text NOT NULL,
    content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple'::regconfig, COALESCE(fts_text, ''::text))) STORED,
    embedding_model text NOT NULL,
    embedding_version text NOT NULL,
    embedding public.vector(1024) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT document_chunks_v2_chunk_index_check CHECK ((chunk_index >= 0)),
    CONSTRAINT document_chunks_v2_token_count_check CHECK ((token_count > 0))
);


--
-- Name: document_chunks_v3_shadow; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_chunks_v3_shadow (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    document_id uuid NOT NULL,
    project_id uuid NOT NULL,
    source_type text NOT NULL,
    source_locator text,
    page integer,
    slide integer,
    sheet text,
    cell_range text,
    heading_path text,
    parent_chunk_id uuid,
    previous_chunk_id uuid,
    next_chunk_id uuid,
    parser_version text NOT NULL,
    chunker_version text NOT NULL,
    retrieval_version text DEFAULT 'v3-shadow'::text NOT NULL,
    original_text text NOT NULL,
    contextual_prefix text DEFAULT ''::text NOT NULL,
    content_hash text NOT NULL,
    content text GENERATED ALWAYS AS (
CASE
    WHEN (contextual_prefix = ''::text) THEN original_text
    ELSE ((contextual_prefix || '

'::text) || original_text)
END) STORED,
    content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple'::regconfig,
CASE
    WHEN (contextual_prefix = ''::text) THEN original_text
    ELSE ((contextual_prefix || '

'::text) || original_text)
END)) STORED,
    embedding_model text,
    embedding_version text,
    embedding public.vector(1024),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    chunk_index integer DEFAULT 0 NOT NULL,
    CONSTRAINT document_chunks_v3_shadow_chunk_index_check CHECK ((chunk_index >= 0))
);


--
-- Name: document_chunks_v3_shadow_pre_idempotency_20260828; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_chunks_v3_shadow_pre_idempotency_20260828 (
    id uuid,
    document_id uuid,
    project_id uuid,
    source_type text,
    source_locator text,
    page integer,
    slide integer,
    sheet text,
    cell_range text,
    heading_path text,
    parent_chunk_id uuid,
    previous_chunk_id uuid,
    next_chunk_id uuid,
    parser_version text,
    chunker_version text,
    retrieval_version text,
    original_text text,
    contextual_prefix text,
    content_hash text,
    content text,
    content_tsv tsvector,
    embedding_model text,
    embedding_version text,
    embedding public.vector(1024),
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    chunk_index integer
);


--
-- Name: documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documents (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    filename text NOT NULL,
    display_name text NOT NULL,
    format text NOT NULL,
    size_bytes bigint NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    error_message text,
    chunk_count integer DEFAULT 0 NOT NULL,
    created_by_user_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    department_id text,
    memory_type text,
    memory_draft_id uuid,
    template_version text,
    asset_family_id uuid,
    version_number integer,
    is_current boolean DEFAULT true NOT NULL,
    supersedes_document_id uuid,
    normalized_filename text,
    effective_at timestamp with time zone,
    source_modified_at timestamp with time zone,
    approval_status text,
    source_relative_path text,
    version_conflict boolean DEFAULT false NOT NULL,
    version_conflict_reason text,
    CONSTRAINT documents_format_check CHECK ((format = ANY (ARRAY['bat'::text, 'c'::text, 'conf'::text, 'cpp'::text, 'cs'::text, 'css'::text, 'csv'::text, 'docx'::text, 'go'::text, 'h'::text, 'hpp'::text, 'html'::text, 'java'::text, 'js'::text, 'json'::text, 'jsx'::text, 'jpeg'::text, 'jpg'::text, 'log'::text, 'md'::text, 'pdf'::text, 'png'::text, 'pptx'::text, 'ps1'::text, 'py'::text, 'rs'::text, 'scss'::text, 'sh'::text, 'sql'::text, 'ts'::text, 'tsx'::text, 'txt'::text, 'vue'::text, 'xml'::text, 'xlsx'::text, 'yaml'::text, 'yml'::text, 'zip'::text]))),
    CONSTRAINT documents_size_bytes_check CHECK ((size_bytes > 0)),
    CONSTRAINT documents_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'processing'::text, 'ready'::text, 'failed'::text])))
);


--
-- Name: errors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.errors (
    id bigint NOT NULL,
    session_id uuid NOT NULL,
    trigger_event_id uuid,
    trigger_event_type public.trigger_event_type,
    error_type text,
    code text,
    details text,
    logs text,
    "timestamp" timestamp with time zone NOT NULL
);


--
-- Name: errors_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.errors ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.errors_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: ingest_queue_receipts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ingest_queue_receipts (
    id uuid NOT NULL,
    stream text NOT NULL,
    payload_fingerprint text NOT NULL,
    payload jsonb NOT NULL,
    claims jsonb NOT NULL,
    status text NOT NULL,
    attempt_count integer DEFAULT 0 NOT NULL,
    accepted_at timestamp with time zone DEFAULT now() NOT NULL,
    synced_at timestamp with time zone,
    last_error text,
    next_attempt_at timestamp with time zone DEFAULT now() NOT NULL,
    claim_token uuid,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ingest_queue_receipts_status_check CHECK ((status = ANY (ARRAY['accepted'::text, 'processing'::text, 'synced'::text, 'dead_letter'::text])))
);


--
-- Name: llm_credential_refs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.llm_credential_refs (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    instance_id uuid NOT NULL,
    creation_operation_id uuid NOT NULL,
    key_hash text NOT NULL,
    key_prefix text NOT NULL,
    label text NOT NULL,
    state text NOT NULL,
    hidden_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    verified_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT llm_credential_refs_key_hash_check CHECK ((key_hash ~ '^[a-f0-9]{64}$'::text)),
    CONSTRAINT llm_credential_refs_state_check CHECK ((state = ANY (ARRAY['active'::text, 'revoking'::text, 'revoked'::text, 'removing'::text, 'removed'::text, 'needs_attention'::text])))
);


--
-- Name: llm_gateway_instances; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.llm_gateway_instances (
    id uuid NOT NULL,
    endpoint_ref text NOT NULL,
    base_url text NOT NULL,
    models jsonb NOT NULL,
    enabled boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT llm_gateway_instances_models_check CHECK (((jsonb_typeof(models) = 'array'::text) AND (jsonb_array_length(models) > 0)))
);


--
-- Name: llm_key_operations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.llm_key_operations (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    instance_id uuid NOT NULL,
    idempotency_key uuid NOT NULL,
    request_hash text NOT NULL,
    kind text NOT NULL,
    state text NOT NULL,
    credential_id uuid NOT NULL,
    key_hash text NOT NULL,
    key_prefix text NOT NULL,
    label text NOT NULL,
    reserved_slot boolean DEFAULT false NOT NULL,
    error_code text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT llm_key_operations_check CHECK (((NOT reserved_slot) OR (kind = 'create'::text))),
    CONSTRAINT llm_key_operations_key_hash_check CHECK ((key_hash ~ '^[a-f0-9]{64}$'::text)),
    CONSTRAINT llm_key_operations_kind_check CHECK ((kind = ANY (ARRAY['create'::text, 'revoke'::text, 'remove'::text]))),
    CONSTRAINT llm_key_operations_state_check CHECK ((state = ANY (ARRAY['reserved'::text, 'submitted'::text, 'confirmed'::text, 'reconciling'::text, 'needs_attention'::text, 'failed_confirmed'::text])))
);


--
-- Name: llm_member_rollout; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.llm_member_rollout (
    user_id uuid NOT NULL,
    instance_id uuid NOT NULL,
    enabled boolean DEFAULT false NOT NULL
);


--
-- Name: llms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.llms (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    session_id uuid NOT NULL,
    agent_id uuid,
    thread_id uuid,
    prompt jsonb,
    completion jsonb,
    model text,
    prompt_tokens numeric,
    completion_tokens numeric,
    cost numeric,
    promptarmor_flag boolean,
    params text,
    returns text,
    init_timestamp timestamp with time zone NOT NULL,
    end_timestamp timestamp with time zone NOT NULL
);


--
-- Name: meeting_summaries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.meeting_summaries (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    title text NOT NULL,
    meeting_date date NOT NULL,
    participants text[] DEFAULT ARRAY[]::text[] NOT NULL,
    tags text[] DEFAULT ARRAY[]::text[] NOT NULL,
    summary_markdown text NOT NULL,
    decisions text[] DEFAULT ARRAY[]::text[] NOT NULL,
    action_items text[] DEFAULT ARRAY[]::text[] NOT NULL,
    source_filename text,
    created_by uuid NOT NULL,
    embedding public.vector(1024),
    embedding_model text,
    embedding_version text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    participant_user_ids uuid[] DEFAULT ARRAY[]::uuid[] NOT NULL,
    approval_draft_id uuid,
    CONSTRAINT meeting_summaries_summary_markdown_check CHECK ((char_length(summary_markdown) > 0)),
    CONSTRAINT meeting_summaries_title_check CHECK (((char_length(title) >= 1) AND (char_length(title) <= 200)))
);


--
-- Name: meeting_summary_files; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.meeting_summary_files (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    meeting_summary_id uuid NOT NULL,
    filename text NOT NULL,
    format text NOT NULL,
    mime_type text,
    size_bytes bigint NOT NULL,
    content_hash text NOT NULL,
    raw_content bytea NOT NULL,
    extracted_text text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT meeting_summary_files_content_hash_check CHECK ((char_length(content_hash) = 64)),
    CONSTRAINT meeting_summary_files_extracted_text_check CHECK ((char_length(extracted_text) > 0)),
    CONSTRAINT meeting_summary_files_filename_check CHECK (((char_length(filename) >= 1) AND (char_length(filename) <= 255))),
    CONSTRAINT meeting_summary_files_format_check CHECK (((char_length(format) >= 1) AND (char_length(format) <= 32))),
    CONSTRAINT meeting_summary_files_size_bytes_check CHECK (((size_bytes > 0) AND (size_bytes <= 20971520)))
);


--
-- Name: member_wiki_experience_sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.member_wiki_experience_sources (
    experience_id uuid NOT NULL,
    session_id uuid NOT NULL,
    trace_id text,
    observed_at timestamp with time zone NOT NULL,
    source text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: member_wiki_experience_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.member_wiki_experience_versions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    experience_id uuid NOT NULL,
    version integer NOT NULL,
    run_id uuid,
    structured_content jsonb NOT NULL,
    markdown_content text NOT NULL,
    source_session_ids jsonb DEFAULT '[]'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT member_wiki_experience_versions_version_check CHECK ((version >= 1))
);


--
-- Name: member_wiki_experiences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.member_wiki_experiences (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    employee_id text NOT NULL,
    employee_name text NOT NULL,
    experience_key text NOT NULL,
    title text NOT NULL,
    task_type text NOT NULL,
    outcome text NOT NULL,
    summary text DEFAULT ''::text NOT NULL,
    structured_content jsonb NOT NULL,
    markdown_content text NOT NULL,
    tags text[] DEFAULT ARRAY[]::text[] NOT NULL,
    tools text[] DEFAULT ARRAY[]::text[] NOT NULL,
    confidence numeric(4,3) DEFAULT 0 NOT NULL,
    first_observed date NOT NULL,
    last_observed date NOT NULL,
    observation_count integer DEFAULT 1 NOT NULL,
    source_session_ids jsonb DEFAULT '[]'::jsonb NOT NULL,
    source_trace_ids jsonb DEFAULT '[]'::jsonb NOT NULL,
    current_version integer DEFAULT 1 NOT NULL,
    embedding public.vector(1024),
    embedding_model text,
    embedding_version text,
    status text DEFAULT 'active'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT member_wiki_experiences_confidence_check CHECK (((confidence >= (0)::numeric) AND (confidence <= (1)::numeric))),
    CONSTRAINT member_wiki_experiences_key_check CHECK ((experience_key ~ '^[a-z0-9][a-z0-9_-]{2,119}$'::text)),
    CONSTRAINT member_wiki_experiences_observation_check CHECK (((observation_count >= 1) AND (last_observed >= first_observed))),
    CONSTRAINT member_wiki_experiences_outcome_check CHECK ((outcome = ANY (ARRAY['success'::text, 'partial'::text, 'failure'::text]))),
    CONSTRAINT member_wiki_experiences_status_check CHECK ((status = ANY (ARRAY['active'::text, 'stale'::text]))),
    CONSTRAINT member_wiki_experiences_task_type_check CHECK ((task_type = ANY (ARRAY['development'::text, 'debugging'::text, 'deployment'::text, 'configuration'::text, 'data_processing'::text, 'documentation'::text, 'testing'::text, 'research'::text, 'operations'::text, 'other'::text]))),
    CONSTRAINT member_wiki_experiences_version_check CHECK ((current_version >= 1))
);


--
-- Name: member_wiki_processed_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.member_wiki_processed_sessions (
    session_id uuid NOT NULL,
    employee_id text NOT NULL,
    run_id uuid,
    observed_at timestamp with time zone NOT NULL,
    experience_count integer DEFAULT 0 NOT NULL,
    processed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT member_wiki_processed_count_check CHECK ((experience_count >= 0))
);


--
-- Name: member_wiki_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.member_wiki_runs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    cutoff_at timestamp with time zone NOT NULL,
    timezone text DEFAULT 'Asia/Shanghai'::text NOT NULL,
    status text NOT NULL,
    model text NOT NULL,
    candidate_member_count integer DEFAULT 0 NOT NULL,
    updated_member_count integer DEFAULT 0 NOT NULL,
    empty_member_count integer DEFAULT 0 NOT NULL,
    session_count integer DEFAULT 0 NOT NULL,
    experience_count integer DEFAULT 0 NOT NULL,
    failure_count integer DEFAULT 0 NOT NULL,
    error_message text,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    CONSTRAINT member_wiki_runs_count_check CHECK (((candidate_member_count >= 0) AND (updated_member_count >= 0) AND (empty_member_count >= 0) AND (session_count >= 0) AND (experience_count >= 0) AND (failure_count >= 0))),
    CONSTRAINT member_wiki_runs_status_check CHECK ((status = ANY (ARRAY['running'::text, 'completed'::text, 'failed'::text]))),
    CONSTRAINT member_wiki_runs_timezone_check CHECK ((timezone = 'Asia/Shanghai'::text))
);


--
-- Name: org_invites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.org_invites (
    inviter_id uuid NOT NULL,
    org_id uuid NOT NULL,
    role public.org_roles NOT NULL,
    org_name text NOT NULL,
    invitee_email text NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: orgs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.orgs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    prem_status public.prem_status DEFAULT 'free'::public.prem_status NOT NULL,
    subscription_id text
);


--
-- Name: prices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prices (
    id text NOT NULL,
    product_id text,
    active boolean,
    description text,
    unit_amount bigint,
    currency text,
    type public.pricing_type,
    "interval" public.pricing_plan_interval,
    interval_count integer,
    trial_period_days integer,
    metadata jsonb,
    CONSTRAINT prices_currency_check CHECK ((char_length(currency) = 3))
);


--
-- Name: products; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.products (
    id text NOT NULL,
    active boolean,
    name text,
    description text,
    image text,
    metadata jsonb
);


--
-- Name: project_agents_file_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_agents_file_versions (
    project_id uuid NOT NULL,
    version integer NOT NULL,
    content text NOT NULL,
    updated_by_user_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid(),
    filename text DEFAULT 'AGENTS.md'::text NOT NULL,
    sha256 text NOT NULL,
    updated_by uuid,
    CONSTRAINT project_agents_file_versions_content_size_check CHECK (((octet_length(content) >= 1) AND (octet_length(content) <= 65536)))
);


--
-- Name: project_agents_files; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_agents_files (
    project_id uuid NOT NULL,
    content text NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    updated_by_user_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    filename text DEFAULT 'AGENTS.md'::text NOT NULL,
    sha256 text NOT NULL,
    updated_by uuid,
    CONSTRAINT project_agents_files_content_check CHECK (((octet_length(content) >= 1) AND (octet_length(content) <= 65536))),
    CONSTRAINT project_agents_files_content_size_check CHECK (((octet_length(content) >= 1) AND (octet_length(content) <= 65536))),
    CONSTRAINT project_agents_files_version_check CHECK ((version > 0))
);


--
-- Name: project_context_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_context_tokens (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    key_id uuid,
    project_id uuid NOT NULL,
    agents_version integer NOT NULL,
    agents_sha256 text NOT NULL,
    token_hash text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    revoked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT project_context_tokens_agents_sha256_check CHECK ((agents_sha256 ~ '^[a-f0-9]{64}$'::text)),
    CONSTRAINT project_context_tokens_agents_version_check CHECK ((agents_version > 0)),
    CONSTRAINT project_context_tokens_token_hash_check CHECK ((token_hash ~ '^[a-f0-9]{64}$'::text))
);


--
-- Name: project_conversation_record_attempts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_conversation_record_attempts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    record_id uuid NOT NULL,
    status text NOT NULL,
    error_message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT project_conversation_record_attempts_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'published'::text, 'failed'::text])))
);


--
-- Name: project_conversation_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_conversation_records (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    request_id text NOT NULL,
    project_id uuid NOT NULL,
    user_id uuid NOT NULL,
    employee_id text NOT NULL,
    employee_name text NOT NULL,
    model text DEFAULT 'unknown'::text NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    input_tokens integer DEFAULT 0 NOT NULL,
    output_tokens integer DEFAULT 0 NOT NULL,
    total_tokens integer DEFAULT 0 NOT NULL,
    token_status text DEFAULT 'unknown'::text NOT NULL,
    messages jsonb DEFAULT '[]'::jsonb NOT NULL,
    wiki_status text DEFAULT 'pending'::text NOT NULL,
    wiki_page_id uuid,
    wiki_error text,
    attempt_count integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    record_source text DEFAULT 'gateway'::text NOT NULL,
    submission_id uuid,
    content_sha256 text,
    title text DEFAULT ''::text NOT NULL,
    task_result text DEFAULT ''::text NOT NULL,
    model_source text DEFAULT 'gateway_reported'::text NOT NULL,
    CONSTRAINT project_conversation_records_attempt_count_check CHECK ((attempt_count >= 0)),
    CONSTRAINT project_conversation_records_input_tokens_check CHECK ((input_tokens >= 0)),
    CONSTRAINT project_conversation_records_output_tokens_check CHECK ((output_tokens >= 0)),
    CONSTRAINT project_conversation_records_token_status_check CHECK ((token_status = ANY (ARRAY['gateway_reported'::text, 'unknown'::text, 'invalid'::text]))),
    CONSTRAINT project_conversation_records_total_tokens_check CHECK ((total_tokens >= 0)),
    CONSTRAINT project_conversation_records_wiki_status_check CHECK ((wiki_status = ANY (ARRAY['pending'::text, 'published'::text, 'failed'::text]))),
    CONSTRAINT project_conversation_submission_check CHECK (((record_source = ANY (ARRAY['gateway'::text, 'company_memory'::text])) AND (model_source = ANY (ARRAY['gateway_reported'::text, 'client_declared'::text, 'unknown'::text])) AND ((record_source <> 'company_memory'::text) OR ((submission_id IS NOT NULL) AND (content_sha256 IS NOT NULL) AND (content_sha256 ~ '^[a-f0-9]{64}$'::text) AND ((char_length(TRIM(BOTH FROM title)) >= 1) AND (char_length(TRIM(BOTH FROM title)) <= 200)) AND (model_source = ANY (ARRAY['client_declared'::text, 'unknown'::text])) AND (token_status = 'unknown'::text) AND (input_tokens = 0) AND (output_tokens = 0) AND (total_tokens = 0)))))
);


--
-- Name: project_creation_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_creation_requests (
    id uuid NOT NULL,
    requester_id uuid NOT NULL,
    org_id uuid NOT NULL,
    name text NOT NULL,
    environment public.environment DEFAULT 'development'::public.environment NOT NULL,
    department_id text NOT NULL,
    completed_at date,
    reason text NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    review_comment text,
    reviewed_by_user_id uuid,
    created_project_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    reviewed_at timestamp with time zone,
    CONSTRAINT project_creation_requests_name_check CHECK (((char_length(btrim(name)) >= 1) AND (char_length(btrim(name)) <= 200))),
    CONSTRAINT project_creation_requests_reason_check CHECK (((char_length(btrim(reason)) >= 1) AND (char_length(btrim(reason)) <= 2000))),
    CONSTRAINT project_creation_requests_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'approved'::text, 'rejected'::text])))
);


--
-- Name: project_department_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_department_migrations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    source_department_id text,
    target_department_id text,
    requested_by_user_id uuid NOT NULL,
    idempotency_key text,
    status text DEFAULT 'queued'::text NOT NULL,
    current_step text DEFAULT 'queued'::text NOT NULL,
    progress integer DEFAULT 0 NOT NULL,
    raw_material_count integer DEFAULT 0 NOT NULL,
    wiki_page_count integer DEFAULT 0 NOT NULL,
    meeting_record_count integer DEFAULT 0 NOT NULL,
    documents_updated integer DEFAULT 0 NOT NULL,
    material_intakes_updated integer DEFAULT 0 NOT NULL,
    memory_drafts_updated integer DEFAULT 0 NOT NULL,
    pending_requests_updated integer DEFAULT 0 NOT NULL,
    verified boolean DEFAULT false NOT NULL,
    error_message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    source_department_name text NOT NULL,
    target_department_name text NOT NULL,
    task_id uuid DEFAULT gen_random_uuid() NOT NULL,
    claimed_by text,
    lease_expires_at timestamp with time zone,
    attempt_count integer DEFAULT 0 NOT NULL,
    max_attempts integer DEFAULT 3 NOT NULL,
    next_attempt_at timestamp with time zone DEFAULT now() NOT NULL,
    cursor jsonb DEFAULT '{}'::jsonb NOT NULL,
    last_cursor jsonb DEFAULT '{}'::jsonb NOT NULL,
    cancel_requested boolean DEFAULT false NOT NULL,
    pause_requested boolean DEFAULT false NOT NULL,
    total_count integer DEFAULT 0 NOT NULL,
    succeeded_count integer DEFAULT 0 NOT NULL,
    failed_count integer DEFAULT 0 NOT NULL,
    remaining_count integer DEFAULT 0 NOT NULL,
    elapsed_seconds integer DEFAULT 0 NOT NULL,
    CONSTRAINT project_department_migrations_attempts_check CHECK (((attempt_count >= 0) AND (max_attempts > 0))),
    CONSTRAINT project_department_migrations_distinct_departments_check CHECK ((source_department_id <> target_department_id)),
    CONSTRAINT project_department_migrations_documents_updated_check CHECK ((documents_updated >= 0)),
    CONSTRAINT project_department_migrations_idempotency_key_check CHECK (((idempotency_key IS NULL) OR ((char_length(idempotency_key) >= 1) AND (char_length(idempotency_key) <= 120)))),
    CONSTRAINT project_department_migrations_material_intakes_updated_check CHECK ((material_intakes_updated >= 0)),
    CONSTRAINT project_department_migrations_meeting_record_count_check CHECK ((meeting_record_count >= 0)),
    CONSTRAINT project_department_migrations_memory_drafts_updated_check CHECK ((memory_drafts_updated >= 0)),
    CONSTRAINT project_department_migrations_metrics_check CHECK (((total_count >= 0) AND (succeeded_count >= 0) AND (failed_count >= 0) AND (remaining_count >= 0) AND (((succeeded_count + failed_count) + remaining_count) = total_count) AND (elapsed_seconds >= 0))),
    CONSTRAINT project_department_migrations_pending_requests_updated_check CHECK ((pending_requests_updated >= 0)),
    CONSTRAINT project_department_migrations_progress_check CHECK (((progress >= 0) AND (progress <= 100))),
    CONSTRAINT project_department_migrations_raw_material_count_check CHECK ((raw_material_count >= 0)),
    CONSTRAINT project_department_migrations_status_check CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'paused'::text, 'completed'::text, 'failed'::text, 'cancelled'::text]))),
    CONSTRAINT project_department_migrations_wiki_page_count_check CHECK ((wiki_page_count >= 0))
);


--
-- Name: project_material_documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_material_documents (
    document_id uuid NOT NULL,
    project_id uuid NOT NULL,
    draft_id uuid,
    uploaded_by_user_id uuid,
    uploaded_at timestamp with time zone DEFAULT now() NOT NULL,
    content_hash text,
    original_file_id uuid
);


--
-- Name: project_material_intake_files; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_material_intake_files (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    intake_id uuid NOT NULL,
    filename text NOT NULL,
    format text NOT NULL,
    size_bytes bigint NOT NULL,
    content_hash text NOT NULL,
    raw_content bytea NOT NULL,
    extracted_text text NOT NULL,
    recommendation text NOT NULL,
    included boolean DEFAULT true NOT NULL,
    reason text DEFAULT ''::text NOT NULL,
    issues jsonb DEFAULT '[]'::jsonb NOT NULL,
    document_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    storage_key text,
    uploaded_bytes bigint DEFAULT 0 NOT NULL,
    relative_path text NOT NULL,
    parser_metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    CONSTRAINT project_material_intake_files_check CHECK (((uploaded_bytes >= 0) AND (uploaded_bytes <= size_bytes))),
    CONSTRAINT project_material_intake_files_recommendation_check CHECK ((recommendation = ANY (ARRAY['keep'::text, 'review'::text, 'duplicate'::text, 'sensitive'::text, 'low_value'::text]))),
    CONSTRAINT project_material_intake_files_relative_path_length_check CHECK (((char_length(relative_path) >= 1) AND (char_length(relative_path) <= 1024))),
    CONSTRAINT project_material_intake_files_relative_path_safe_check CHECK (((relative_path !~ '(^/|(^|/)\.\.?(/|$)|[[:cntrl:]])'::text) AND (relative_path !~ '^[A-Za-z]:/'::text) AND (relative_path !~ '\\'::text))),
    CONSTRAINT project_material_intake_files_size_bytes_check CHECK ((size_bytes > 0))
);


--
-- Name: project_material_intakes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_material_intakes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    department_id text NOT NULL,
    status text DEFAULT 'preview_ready'::text NOT NULL,
    preview_summary text DEFAULT ''::text NOT NULL,
    preview_model text,
    preview_used_fallback boolean DEFAULT false NOT NULL,
    created_by_user_id uuid,
    confirmed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    client_upload_id uuid,
    upload_completed_at timestamp with time zone,
    CONSTRAINT project_material_intakes_status_check CHECK ((status = ANY (ARRAY['uploading'::text, 'preview_ready'::text, 'processing'::text, 'pending_review'::text, 'approved'::text, 'rejected'::text, 'failed'::text])))
);


--
-- Name: project_material_parse_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_material_parse_jobs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    intake_file_id uuid NOT NULL,
    status text DEFAULT 'queued'::text NOT NULL,
    claimed_by text,
    lease_expires_at timestamp with time zone,
    attempt_count integer DEFAULT 0 NOT NULL,
    max_attempts integer DEFAULT 3 NOT NULL,
    timeout_seconds integer DEFAULT 900 NOT NULL,
    next_attempt_at timestamp with time zone DEFAULT now() NOT NULL,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    error_message text,
    result_metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_by_user_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT project_material_parse_jobs_attempt_count_check CHECK ((attempt_count >= 0)),
    CONSTRAINT project_material_parse_jobs_max_attempts_check CHECK ((max_attempts > 0)),
    CONSTRAINT project_material_parse_jobs_status_check CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'completed'::text, 'failed'::text, 'cancelled'::text]))),
    CONSTRAINT project_material_parse_jobs_timeout_seconds_check CHECK ((timeout_seconds > 0))
);


--
-- Name: project_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_members (
    project_id uuid NOT NULL,
    user_id uuid NOT NULL,
    role public.org_roles DEFAULT 'developer'::public.org_roles NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: project_memory_approval_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_memory_approval_jobs (
    id uuid NOT NULL,
    draft_id uuid NOT NULL,
    decision text NOT NULL,
    requested_by_user_id uuid NOT NULL,
    comment text,
    status text DEFAULT 'queued'::text NOT NULL,
    progress integer DEFAULT 0 NOT NULL,
    current_step text DEFAULT 'queued'::text NOT NULL,
    error_message text,
    attempt_count integer DEFAULT 0 NOT NULL,
    next_attempt_at timestamp with time zone DEFAULT now() NOT NULL,
    claim_token uuid,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT project_memory_approval_jobs_decision_check CHECK ((decision = ANY (ARRAY['approve'::text, 'reject'::text]))),
    CONSTRAINT project_memory_approval_jobs_progress_check CHECK (((progress >= 0) AND (progress <= 100))),
    CONSTRAINT project_memory_approval_jobs_status_check CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'completed'::text, 'failed'::text])))
);


--
-- Name: project_memory_draft_sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_memory_draft_sources (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    draft_id uuid NOT NULL,
    filename text NOT NULL,
    format text NOT NULL,
    extracted_text text NOT NULL,
    size_bytes bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    content_hash text,
    CONSTRAINT project_memory_draft_sources_format_check CHECK ((format = ANY (ARRAY['bat'::text, 'c'::text, 'conf'::text, 'cpp'::text, 'cs'::text, 'css'::text, 'csv'::text, 'docx'::text, 'go'::text, 'h'::text, 'hpp'::text, 'html'::text, 'java'::text, 'js'::text, 'json'::text, 'jsx'::text, 'jpeg'::text, 'jpg'::text, 'log'::text, 'md'::text, 'pdf'::text, 'png'::text, 'pptx'::text, 'ps1'::text, 'py'::text, 'rs'::text, 'scss'::text, 'sh'::text, 'sql'::text, 'ts'::text, 'tsx'::text, 'txt'::text, 'vue'::text, 'xml'::text, 'xlsx'::text, 'yaml'::text, 'yml'::text, 'zip'::text]))),
    CONSTRAINT project_memory_draft_sources_size_bytes_check CHECK ((size_bytes > 0))
);


--
-- Name: project_memory_drafts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_memory_drafts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    department_id text DEFAULT 'research-direct'::text NOT NULL,
    title text NOT NULL,
    status text DEFAULT 'pending_review'::text NOT NULL,
    template_version text DEFAULT 'project-memory-v1'::text NOT NULL,
    markdown_content text NOT NULL,
    source_count integer DEFAULT 0 NOT NULL,
    approved_document_id uuid,
    created_by_user_id uuid,
    reviewed_by_user_id uuid,
    review_comment text,
    reviewed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    intake_id uuid,
    curated_markdown_content text,
    skill_candidates jsonb DEFAULT '[]'::jsonb NOT NULL,
    generation_model text,
    generation_used_fallback boolean DEFAULT false NOT NULL,
    submission_id uuid,
    approval_progress integer DEFAULT 0 NOT NULL,
    approval_step text DEFAULT 'idle'::text NOT NULL,
    approval_error text,
    CONSTRAINT project_memory_drafts_approval_progress_check CHECK (((approval_progress >= 0) AND (approval_progress <= 100))),
    CONSTRAINT project_memory_drafts_source_count_check CHECK ((source_count >= 0)),
    CONSTRAINT project_memory_drafts_status_check CHECK ((status = ANY (ARRAY['pending_review'::text, 'approved'::text, 'rejected'::text])))
);


--
-- Name: project_memory_reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_memory_reviews (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    draft_id uuid NOT NULL,
    reviewer_user_id uuid,
    decision text NOT NULL,
    comment text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT project_memory_reviews_decision_check CHECK ((decision = ANY (ARRAY['approve'::text, 'reject'::text])))
);


--
-- Name: project_memory_submissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_memory_submissions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    submission_type text NOT NULL,
    payload jsonb DEFAULT '{}'::jsonb NOT NULL,
    filename text,
    format text,
    mime_type text,
    size_bytes bigint,
    content_hash text,
    raw_content bytea,
    status text DEFAULT 'pending_review'::text NOT NULL,
    approved_resource_id uuid,
    created_by_user_id uuid,
    reviewed_by_user_id uuid,
    review_comment text,
    reviewed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT project_memory_submissions_check CHECK ((((submission_type = 'meeting_summary'::text) AND (filename IS NOT NULL) AND (format IS NOT NULL) AND (size_bytes IS NOT NULL) AND (content_hash IS NOT NULL) AND ((status <> 'pending_review'::text) OR (raw_content IS NOT NULL))) OR ((submission_type = 'project_repository'::text) AND (filename IS NULL) AND (format IS NULL) AND (size_bytes IS NULL) AND (content_hash IS NULL) AND (raw_content IS NULL)))),
    CONSTRAINT project_memory_submissions_size_bytes_check CHECK (((size_bytes IS NULL) OR (size_bytes > 0))),
    CONSTRAINT project_memory_submissions_status_check CHECK ((status = ANY (ARRAY['pending_review'::text, 'approved'::text, 'rejected'::text]))),
    CONSTRAINT project_memory_submissions_submission_type_check CHECK ((submission_type = ANY (ARRAY['meeting_summary'::text, 'project_repository'::text])))
);


--
-- Name: project_repositories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_repositories (
    project_id uuid NOT NULL,
    git_url text NOT NULL,
    git_branch text DEFAULT 'main'::text NOT NULL,
    created_by_user_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    note text DEFAULT ''::text NOT NULL,
    CONSTRAINT project_repositories_git_url_check CHECK ((git_url ~* '^https?://'::text)),
    CONSTRAINT project_repositories_note_length_check CHECK ((char_length(note) <= 1000))
);


--
-- Name: project_wiki_changes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_wiki_changes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    run_id uuid NOT NULL,
    project_id uuid NOT NULL,
    page_key text NOT NULL,
    title text NOT NULL,
    page_type text NOT NULL,
    disposition text NOT NULL,
    reason_code text NOT NULL,
    status text NOT NULL,
    summary text DEFAULT ''::text NOT NULL,
    proposed_markdown text NOT NULL,
    usefulness numeric(4,3) NOT NULL,
    confidence numeric(4,3) NOT NULL,
    contradiction boolean DEFAULT false NOT NULL,
    source_ids jsonb DEFAULT '[]'::jsonb NOT NULL,
    link_titles jsonb DEFAULT '[]'::jsonb NOT NULL,
    page_id uuid,
    reviewed_by_user_id uuid,
    review_comment text,
    reviewed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    memory_kind text DEFAULT 'reference'::text NOT NULL,
    tags text[] DEFAULT ARRAY[]::text[] NOT NULL,
    valid_from date,
    valid_until date,
    CONSTRAINT project_wiki_changes_confidence_check CHECK (((confidence >= (0)::numeric) AND (confidence <= (1)::numeric))),
    CONSTRAINT project_wiki_changes_disposition_check CHECK ((disposition = ANY (ARRAY['auto_apply'::text, 'pending_review'::text, 'discard'::text]))),
    CONSTRAINT project_wiki_changes_status_check CHECK ((status = ANY (ARRAY['pending_review'::text, 'applied'::text, 'rejected'::text, 'discarded'::text]))),
    CONSTRAINT project_wiki_changes_usefulness_check CHECK (((usefulness >= (0)::numeric) AND (usefulness <= (1)::numeric)))
);


--
-- Name: project_wiki_compile_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_wiki_compile_runs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    status text DEFAULT 'running'::text NOT NULL,
    trigger_type text NOT NULL,
    triggered_by_user_id uuid,
    model text NOT NULL,
    source_count integer DEFAULT 0 NOT NULL,
    candidate_count integer DEFAULT 0 NOT NULL,
    auto_applied_count integer DEFAULT 0 NOT NULL,
    pending_review_count integer DEFAULT 0 NOT NULL,
    discarded_count integer DEFAULT 0 NOT NULL,
    error_message text,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    CONSTRAINT project_wiki_compile_runs_auto_applied_count_check CHECK ((auto_applied_count >= 0)),
    CONSTRAINT project_wiki_compile_runs_candidate_count_check CHECK ((candidate_count >= 0)),
    CONSTRAINT project_wiki_compile_runs_discarded_count_check CHECK ((discarded_count >= 0)),
    CONSTRAINT project_wiki_compile_runs_pending_review_count_check CHECK ((pending_review_count >= 0)),
    CONSTRAINT project_wiki_compile_runs_source_count_check CHECK ((source_count >= 0)),
    CONSTRAINT project_wiki_compile_runs_status_check CHECK ((status = ANY (ARRAY['running'::text, 'completed'::text, 'failed'::text]))),
    CONSTRAINT project_wiki_compile_runs_trigger_type_check CHECK ((trigger_type = ANY (ARRAY['manual'::text, 'scheduled'::text, 'mcp_proposal'::text])))
);


--
-- Name: project_wiki_links; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_wiki_links (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    from_page_id uuid NOT NULL,
    to_title text NOT NULL,
    relation text DEFAULT 'related'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    to_page_id uuid
);


--
-- Name: project_wiki_page_sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_wiki_page_sources (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    page_id uuid NOT NULL,
    source_type text NOT NULL,
    source_id text NOT NULL,
    locator text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: project_wiki_page_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_wiki_page_versions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    page_id uuid NOT NULL,
    version integer NOT NULL,
    markdown_content text NOT NULL,
    summary text DEFAULT ''::text NOT NULL,
    source_ids jsonb DEFAULT '[]'::jsonb NOT NULL,
    change_reason text NOT NULL,
    created_by_user_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT project_wiki_page_versions_version_check CHECK ((version > 0))
);


--
-- Name: project_wiki_pages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_wiki_pages (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    page_key text NOT NULL,
    title text NOT NULL,
    page_type text NOT NULL,
    status text DEFAULT 'active'::text NOT NULL,
    summary text DEFAULT ''::text NOT NULL,
    markdown_content text NOT NULL,
    usefulness numeric(4,3) NOT NULL,
    confidence numeric(4,3) NOT NULL,
    current_version integer DEFAULT 1 NOT NULL,
    document_id uuid,
    created_by_user_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    memory_kind text DEFAULT 'reference'::text NOT NULL,
    tags text[] DEFAULT ARRAY[]::text[] NOT NULL,
    verification_status text DEFAULT 'generated'::text NOT NULL,
    valid_from date,
    valid_until date,
    verified_by_user_id uuid,
    verified_at timestamp with time zone,
    CONSTRAINT project_wiki_pages_confidence_check CHECK (((confidence >= (0)::numeric) AND (confidence <= (1)::numeric))),
    CONSTRAINT project_wiki_pages_current_version_check CHECK ((current_version > 0)),
    CONSTRAINT project_wiki_pages_memory_kind_check CHECK ((memory_kind = ANY (ARRAY['workflow_template'::text, 'failure_case'::text, 'success_case'::text, 'strategy'::text, 'retrospective'::text, 'decision_record'::text, 'checklist'::text, 'background'::text, 'timeline_event'::text, 'reference'::text, 'conversation_record'::text]))),
    CONSTRAINT project_wiki_pages_page_type_check CHECK ((page_type = ANY (ARRAY['fact'::text, 'concept'::text, 'procedure'::text, 'troubleshooting'::text, 'lesson'::text, 'decision'::text, 'policy'::text, 'architecture'::text, 'requirement'::text, 'note'::text]))),
    CONSTRAINT project_wiki_pages_status_check CHECK ((status = ANY (ARRAY['active'::text, 'archived'::text]))),
    CONSTRAINT project_wiki_pages_usefulness_check CHECK (((usefulness >= (0)::numeric) AND (usefulness <= (1)::numeric))),
    CONSTRAINT project_wiki_pages_verification_status_check CHECK ((verification_status = ANY (ARRAY['generated'::text, 'verified'::text, 'stale'::text])))
);


--
-- Name: project_wiki_processed_sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_wiki_processed_sources (
    project_id uuid NOT NULL,
    source_id text NOT NULL,
    source_type text NOT NULL,
    content_hash text NOT NULL,
    observed_at timestamp with time zone NOT NULL,
    last_run_id uuid,
    processed_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.projects (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    org_id uuid NOT NULL,
    api_key uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    environment public.environment DEFAULT 'development'::public.environment NOT NULL,
    user_callback_url text,
    department_id text DEFAULT 'research-direct'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at date
);


--
-- Name: rag_v3_index_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rag_v3_index_jobs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    document_id uuid,
    status text DEFAULT 'queued'::text NOT NULL,
    parser_version text NOT NULL,
    chunker_version text NOT NULL,
    retrieval_version text DEFAULT 'v3-shadow'::text NOT NULL,
    processed_items integer DEFAULT 0 NOT NULL,
    total_items integer,
    retry_count integer DEFAULT 0 NOT NULL,
    max_retries integer DEFAULT 3 NOT NULL,
    rate_limit_per_minute integer,
    last_error text,
    idempotency_key text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT rag_v3_index_jobs_max_retries_check CHECK ((max_retries >= 0)),
    CONSTRAINT rag_v3_index_jobs_processed_items_check CHECK ((processed_items >= 0)),
    CONSTRAINT rag_v3_index_jobs_rate_limit_per_minute_check CHECK (((rate_limit_per_minute IS NULL) OR (rate_limit_per_minute > 0))),
    CONSTRAINT rag_v3_index_jobs_retry_count_check CHECK ((retry_count >= 0)),
    CONSTRAINT rag_v3_index_jobs_status_check CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'paused'::text, 'cancelling'::text, 'cancelled'::text, 'failed'::text, 'completed'::text]))),
    CONSTRAINT rag_v3_index_jobs_total_items_check CHECK (((total_items IS NULL) OR (total_items >= 0)))
);


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sessions (
    id uuid NOT NULL,
    project_id uuid NOT NULL,
    project_id_secondary uuid,
    init_timestamp timestamp with time zone NOT NULL,
    end_timestamp timestamp with time zone,
    tags text,
    end_state public.end_state DEFAULT 'Indeterminate'::public.end_state,
    end_state_reason text,
    video text,
    host_env jsonb
);


--
-- Name: spans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.spans (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    session_id uuid NOT NULL,
    agent_id uuid,
    trace_id text NOT NULL,
    span_id text NOT NULL,
    parent_span_id text,
    name text NOT NULL,
    kind text NOT NULL,
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone NOT NULL,
    attributes bytea,
    span_type text NOT NULL
);


--
-- Name: stats; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.stats (
    session_id uuid NOT NULL,
    cost numeric,
    events integer DEFAULT 0 NOT NULL,
    prompt_tokens integer DEFAULT 0 NOT NULL,
    completion_tokens integer DEFAULT 0 NOT NULL,
    errors integer DEFAULT 0 NOT NULL
);


--
-- Name: subscriptions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subscriptions (
    id text NOT NULL,
    user_id uuid NOT NULL,
    status public.subscription_status,
    metadata jsonb,
    price_id text,
    quantity integer,
    cancel_at_period_end boolean,
    created timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    current_period_start timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    current_period_end timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    ended_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
    cancel_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
    canceled_at timestamp with time zone DEFAULT timezone('utc'::text, now()),
    trial_start timestamp with time zone DEFAULT timezone('utc'::text, now()),
    trial_end timestamp with time zone DEFAULT timezone('utc'::text, now())
);


--
-- Name: threads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.threads (
    id uuid NOT NULL,
    session_id uuid NOT NULL,
    agent_id uuid NOT NULL
);


--
-- Name: tools; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tools (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    session_id uuid NOT NULL,
    agent_id uuid NOT NULL,
    name text,
    logs text,
    params text,
    returns text,
    init_timestamp timestamp with time zone NOT NULL,
    end_timestamp timestamp with time zone NOT NULL
);


--
-- Name: ttd; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ttd (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    ttd_id uuid NOT NULL,
    branch_name text NOT NULL,
    session_id uuid,
    llm_id uuid,
    prompt jsonb,
    completion jsonb,
    model text,
    prompt_tokens numeric,
    completion_tokens numeric,
    params text,
    returns text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: user_orgs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_orgs (
    user_id uuid NOT NULL,
    org_id uuid NOT NULL,
    role public.org_roles DEFAULT 'owner'::public.org_roles NOT NULL,
    user_email text,
    is_paid boolean DEFAULT false
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    full_name text,
    avatar_url text,
    billing_address jsonb,
    payment_method jsonb,
    email text DEFAULT ''::text,
    survey_is_complete boolean DEFAULT false NOT NULL,
    nickname text,
    ai_detail_visible_to_admin boolean DEFAULT false NOT NULL,
    is_system_admin boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    deactivated_at timestamp with time zone,
    deactivated_by_user_id uuid,
    CONSTRAINT users_nickname_length_check CHECK (((nickname IS NULL) OR (char_length(nickname) <= 80)))
);


--
-- Name: COLUMN users.ai_detail_visible_to_admin; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.ai_detail_visible_to_admin IS 'When true, organization administrators may read this member''s detailed AI conversation records. Daily work logs remain administrator-visible regardless.';


--
-- Name: webhook_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.webhook_events (
    event_id character varying NOT NULL,
    processed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: wiki_mcp_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wiki_mcp_tokens (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    name text NOT NULL,
    token_hash text NOT NULL,
    scopes text[] DEFAULT ARRAY['wiki:read'::text] NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone,
    last_used_at timestamp with time zone,
    revoked_at timestamp with time zone,
    CONSTRAINT wiki_mcp_tokens_name_check CHECK (((char_length(name) >= 1) AND (char_length(name) <= 100))),
    CONSTRAINT wiki_mcp_tokens_scopes_check CHECK ((scopes <@ ARRAY['wiki:read'::text, 'wiki:propose'::text]))
);


--
-- Name: messages; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.messages (
    topic text NOT NULL,
    extension text NOT NULL,
    payload jsonb,
    event text,
    private boolean DEFAULT false,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    inserted_at timestamp without time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    binary_payload bytea
)
PARTITION BY RANGE (inserted_at);


--
-- Name: messages_2026_07_14; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.messages_2026_07_14 (
    topic text NOT NULL,
    extension text NOT NULL,
    payload jsonb,
    event text,
    private boolean DEFAULT false,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    inserted_at timestamp without time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    binary_payload bytea,
    CONSTRAINT messages_payload_exclusive CHECK (((payload IS NULL) OR (binary_payload IS NULL)))
);


--
-- Name: messages_2026_07_15; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.messages_2026_07_15 (
    topic text NOT NULL,
    extension text NOT NULL,
    payload jsonb,
    event text,
    private boolean DEFAULT false,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    inserted_at timestamp without time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    binary_payload bytea,
    CONSTRAINT messages_payload_exclusive CHECK (((payload IS NULL) OR (binary_payload IS NULL)))
);


--
-- Name: messages_2026_07_16; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.messages_2026_07_16 (
    topic text NOT NULL,
    extension text NOT NULL,
    payload jsonb,
    event text,
    private boolean DEFAULT false,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    inserted_at timestamp without time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    binary_payload bytea,
    CONSTRAINT messages_payload_exclusive CHECK (((payload IS NULL) OR (binary_payload IS NULL)))
);


--
-- Name: messages_2026_07_17; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.messages_2026_07_17 (
    topic text NOT NULL,
    extension text NOT NULL,
    payload jsonb,
    event text,
    private boolean DEFAULT false,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    inserted_at timestamp without time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    binary_payload bytea,
    CONSTRAINT messages_payload_exclusive CHECK (((payload IS NULL) OR (binary_payload IS NULL)))
);


--
-- Name: messages_2026_07_18; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.messages_2026_07_18 (
    topic text NOT NULL,
    extension text NOT NULL,
    payload jsonb,
    event text,
    private boolean DEFAULT false,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    inserted_at timestamp without time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    binary_payload bytea,
    CONSTRAINT messages_payload_exclusive CHECK (((payload IS NULL) OR (binary_payload IS NULL)))
);


--
-- Name: schema_migrations; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.schema_migrations (
    version bigint NOT NULL,
    inserted_at timestamp(0) without time zone
);


--
-- Name: subscription; Type: TABLE; Schema: realtime; Owner: -
--

CREATE TABLE realtime.subscription (
    id bigint NOT NULL,
    subscription_id uuid NOT NULL,
    entity regclass NOT NULL,
    filters realtime.user_defined_filter[] DEFAULT '{}'::realtime.user_defined_filter[] NOT NULL,
    claims jsonb NOT NULL,
    claims_role regrole GENERATED ALWAYS AS (realtime.to_regrole((claims ->> 'role'::text))) STORED NOT NULL,
    created_at timestamp without time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    action_filter text DEFAULT '*'::text,
    selected_columns text[],
    CONSTRAINT subscription_action_filter_check CHECK ((action_filter = ANY (ARRAY['*'::text, 'INSERT'::text, 'UPDATE'::text, 'DELETE'::text])))
);


--
-- Name: subscription_id_seq; Type: SEQUENCE; Schema: realtime; Owner: -
--

ALTER TABLE realtime.subscription ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME realtime.subscription_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: buckets; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.buckets (
    id text NOT NULL,
    name text NOT NULL,
    owner uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    public boolean DEFAULT false,
    avif_autodetection boolean DEFAULT false,
    file_size_limit bigint,
    allowed_mime_types text[],
    owner_id text,
    type storage.buckettype DEFAULT 'STANDARD'::storage.buckettype NOT NULL
);


--
-- Name: COLUMN buckets.owner; Type: COMMENT; Schema: storage; Owner: -
--

COMMENT ON COLUMN storage.buckets.owner IS 'Field is deprecated, use owner_id instead';


--
-- Name: buckets_analytics; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.buckets_analytics (
    name text NOT NULL,
    type storage.buckettype DEFAULT 'ANALYTICS'::storage.buckettype NOT NULL,
    format text DEFAULT 'ICEBERG'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    deleted_at timestamp with time zone
);


--
-- Name: buckets_vectors; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.buckets_vectors (
    id text NOT NULL,
    type storage.buckettype DEFAULT 'VECTOR'::storage.buckettype NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: iceberg_namespaces; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.iceberg_namespaces (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    bucket_name text NOT NULL,
    name text NOT NULL COLLATE pg_catalog."C",
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    catalog_id uuid NOT NULL
);


--
-- Name: iceberg_tables; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.iceberg_tables (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    namespace_id uuid NOT NULL,
    bucket_name text NOT NULL,
    name text NOT NULL COLLATE pg_catalog."C",
    location text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    remote_table_id text,
    shard_key text,
    shard_id text,
    catalog_id uuid NOT NULL
);


--
-- Name: migrations; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.migrations (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    hash character varying(40) NOT NULL,
    executed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: objects; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.objects (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    bucket_id text,
    name text,
    owner uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_accessed_at timestamp with time zone DEFAULT now(),
    metadata jsonb,
    path_tokens text[] GENERATED ALWAYS AS (string_to_array(name, '/'::text)) STORED,
    version text,
    owner_id text,
    user_metadata jsonb
);


--
-- Name: COLUMN objects.owner; Type: COMMENT; Schema: storage; Owner: -
--

COMMENT ON COLUMN storage.objects.owner IS 'Field is deprecated, use owner_id instead';


--
-- Name: s3_multipart_uploads; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.s3_multipart_uploads (
    id text NOT NULL,
    in_progress_size bigint DEFAULT 0 NOT NULL,
    upload_signature text NOT NULL,
    bucket_id text NOT NULL,
    key text NOT NULL COLLATE pg_catalog."C",
    version text NOT NULL,
    owner_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    user_metadata jsonb,
    metadata jsonb
);


--
-- Name: s3_multipart_uploads_parts; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.s3_multipart_uploads_parts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    upload_id text NOT NULL,
    size bigint DEFAULT 0 NOT NULL,
    part_number integer NOT NULL,
    bucket_id text NOT NULL,
    key text NOT NULL COLLATE pg_catalog."C",
    etag text NOT NULL,
    owner_id text,
    version text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: vector_indexes; Type: TABLE; Schema: storage; Owner: -
--

CREATE TABLE storage.vector_indexes (
    id text DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL COLLATE pg_catalog."C",
    bucket_id text NOT NULL,
    data_type text NOT NULL,
    dimension integer NOT NULL,
    distance_metric text NOT NULL,
    metadata_configuration jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: hooks; Type: TABLE; Schema: supabase_functions; Owner: -
--

CREATE TABLE supabase_functions.hooks (
    id bigint NOT NULL,
    hook_table_id integer NOT NULL,
    hook_name text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    request_id bigint
);


--
-- Name: TABLE hooks; Type: COMMENT; Schema: supabase_functions; Owner: -
--

COMMENT ON TABLE supabase_functions.hooks IS 'Supabase Functions Hooks: Audit trail for triggered hooks.';


--
-- Name: hooks_id_seq; Type: SEQUENCE; Schema: supabase_functions; Owner: -
--

CREATE SEQUENCE supabase_functions.hooks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: hooks_id_seq; Type: SEQUENCE OWNED BY; Schema: supabase_functions; Owner: -
--

ALTER SEQUENCE supabase_functions.hooks_id_seq OWNED BY supabase_functions.hooks.id;


--
-- Name: migrations; Type: TABLE; Schema: supabase_functions; Owner: -
--

CREATE TABLE supabase_functions.migrations (
    version text NOT NULL,
    inserted_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: schema_migrations; Type: TABLE; Schema: supabase_migrations; Owner: -
--

CREATE TABLE supabase_migrations.schema_migrations (
    version text NOT NULL,
    statements text[],
    name text
);


--
-- Name: seed_files; Type: TABLE; Schema: supabase_migrations; Owner: -
--

CREATE TABLE supabase_migrations.seed_files (
    path text NOT NULL,
    hash text NOT NULL
);


--
-- Name: messages_2026_07_14; Type: TABLE ATTACH; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.messages ATTACH PARTITION realtime.messages_2026_07_14 FOR VALUES FROM ('2026-07-14 00:00:00') TO ('2026-07-15 00:00:00');


--
-- Name: messages_2026_07_15; Type: TABLE ATTACH; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.messages ATTACH PARTITION realtime.messages_2026_07_15 FOR VALUES FROM ('2026-07-15 00:00:00') TO ('2026-07-16 00:00:00');


--
-- Name: messages_2026_07_16; Type: TABLE ATTACH; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.messages ATTACH PARTITION realtime.messages_2026_07_16 FOR VALUES FROM ('2026-07-16 00:00:00') TO ('2026-07-17 00:00:00');


--
-- Name: messages_2026_07_17; Type: TABLE ATTACH; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.messages ATTACH PARTITION realtime.messages_2026_07_17 FOR VALUES FROM ('2026-07-17 00:00:00') TO ('2026-07-18 00:00:00');


--
-- Name: messages_2026_07_18; Type: TABLE ATTACH; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.messages ATTACH PARTITION realtime.messages_2026_07_18 FOR VALUES FROM ('2026-07-18 00:00:00') TO ('2026-07-19 00:00:00');


--
-- Name: refresh_tokens id; Type: DEFAULT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.refresh_tokens ALTER COLUMN id SET DEFAULT nextval('auth.refresh_tokens_id_seq'::regclass);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: hooks id; Type: DEFAULT; Schema: supabase_functions; Owner: -
--

ALTER TABLE ONLY supabase_functions.hooks ALTER COLUMN id SET DEFAULT nextval('supabase_functions.hooks_id_seq'::regclass);


--
-- Name: extensions extensions_pkey; Type: CONSTRAINT; Schema: _realtime; Owner: -
--

ALTER TABLE ONLY _realtime.extensions
    ADD CONSTRAINT extensions_pkey PRIMARY KEY (id);


--
-- Name: feature_flags feature_flags_pkey; Type: CONSTRAINT; Schema: _realtime; Owner: -
--

ALTER TABLE ONLY _realtime.feature_flags
    ADD CONSTRAINT feature_flags_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: _realtime; Owner: -
--

ALTER TABLE ONLY _realtime.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: tenants tenants_pkey; Type: CONSTRAINT; Schema: _realtime; Owner: -
--

ALTER TABLE ONLY _realtime.tenants
    ADD CONSTRAINT tenants_pkey PRIMARY KEY (id);


--
-- Name: mfa_amr_claims amr_id_pk; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_amr_claims
    ADD CONSTRAINT amr_id_pk PRIMARY KEY (id);


--
-- Name: audit_log_entries audit_log_entries_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.audit_log_entries
    ADD CONSTRAINT audit_log_entries_pkey PRIMARY KEY (id);


--
-- Name: custom_oauth_providers custom_oauth_providers_identifier_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.custom_oauth_providers
    ADD CONSTRAINT custom_oauth_providers_identifier_key UNIQUE (identifier);


--
-- Name: custom_oauth_providers custom_oauth_providers_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.custom_oauth_providers
    ADD CONSTRAINT custom_oauth_providers_pkey PRIMARY KEY (id);


--
-- Name: flow_state flow_state_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.flow_state
    ADD CONSTRAINT flow_state_pkey PRIMARY KEY (id);


--
-- Name: identities identities_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.identities
    ADD CONSTRAINT identities_pkey PRIMARY KEY (id);


--
-- Name: identities identities_provider_id_provider_unique; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.identities
    ADD CONSTRAINT identities_provider_id_provider_unique UNIQUE (provider_id, provider);


--
-- Name: instances instances_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.instances
    ADD CONSTRAINT instances_pkey PRIMARY KEY (id);


--
-- Name: mfa_amr_claims mfa_amr_claims_session_id_authentication_method_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_amr_claims
    ADD CONSTRAINT mfa_amr_claims_session_id_authentication_method_pkey UNIQUE (session_id, authentication_method);


--
-- Name: mfa_challenges mfa_challenges_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_challenges
    ADD CONSTRAINT mfa_challenges_pkey PRIMARY KEY (id);


--
-- Name: mfa_factors mfa_factors_last_challenged_at_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_factors
    ADD CONSTRAINT mfa_factors_last_challenged_at_key UNIQUE (last_challenged_at);


--
-- Name: mfa_factors mfa_factors_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_factors
    ADD CONSTRAINT mfa_factors_pkey PRIMARY KEY (id);


--
-- Name: oauth_authorizations oauth_authorizations_authorization_code_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_authorizations
    ADD CONSTRAINT oauth_authorizations_authorization_code_key UNIQUE (authorization_code);


--
-- Name: oauth_authorizations oauth_authorizations_authorization_id_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_authorizations
    ADD CONSTRAINT oauth_authorizations_authorization_id_key UNIQUE (authorization_id);


--
-- Name: oauth_authorizations oauth_authorizations_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_authorizations
    ADD CONSTRAINT oauth_authorizations_pkey PRIMARY KEY (id);


--
-- Name: oauth_client_states oauth_client_states_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_client_states
    ADD CONSTRAINT oauth_client_states_pkey PRIMARY KEY (id);


--
-- Name: oauth_clients oauth_clients_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_clients
    ADD CONSTRAINT oauth_clients_pkey PRIMARY KEY (id);


--
-- Name: oauth_consents oauth_consents_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_consents
    ADD CONSTRAINT oauth_consents_pkey PRIMARY KEY (id);


--
-- Name: oauth_consents oauth_consents_user_client_unique; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_consents
    ADD CONSTRAINT oauth_consents_user_client_unique UNIQUE (user_id, client_id);


--
-- Name: one_time_tokens one_time_tokens_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.one_time_tokens
    ADD CONSTRAINT one_time_tokens_pkey PRIMARY KEY (id);


--
-- Name: refresh_tokens refresh_tokens_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);


--
-- Name: refresh_tokens refresh_tokens_token_unique; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.refresh_tokens
    ADD CONSTRAINT refresh_tokens_token_unique UNIQUE (token);


--
-- Name: saml_providers saml_providers_entity_id_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_providers
    ADD CONSTRAINT saml_providers_entity_id_key UNIQUE (entity_id);


--
-- Name: saml_providers saml_providers_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_providers
    ADD CONSTRAINT saml_providers_pkey PRIMARY KEY (id);


--
-- Name: saml_relay_states saml_relay_states_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_relay_states
    ADD CONSTRAINT saml_relay_states_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: sso_domains sso_domains_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sso_domains
    ADD CONSTRAINT sso_domains_pkey PRIMARY KEY (id);


--
-- Name: sso_providers sso_providers_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sso_providers
    ADD CONSTRAINT sso_providers_pkey PRIMARY KEY (id);


--
-- Name: users users_phone_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT users_phone_key UNIQUE (phone);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: webauthn_challenges webauthn_challenges_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.webauthn_challenges
    ADD CONSTRAINT webauthn_challenges_pkey PRIMARY KEY (id);


--
-- Name: webauthn_credentials webauthn_credentials_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.webauthn_credentials
    ADD CONSTRAINT webauthn_credentials_pkey PRIMARY KEY (id);


--
-- Name: deployments deployments_pkey; Type: CONSTRAINT; Schema: deploy; Owner: -
--

ALTER TABLE ONLY deploy.deployments
    ADD CONSTRAINT deployments_pkey PRIMARY KEY (id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: deploy; Owner: -
--

ALTER TABLE ONLY deploy.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: actions actions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_pkey PRIMARY KEY (id);


--
-- Name: agents agents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT agents_pkey PRIMARY KEY (id);


--
-- Name: ai_chat_messages ai_chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_chat_messages
    ADD CONSTRAINT ai_chat_messages_pkey PRIMARY KEY (id);


--
-- Name: ai_chat_sessions ai_chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_chat_sessions
    ADD CONSTRAINT ai_chat_sessions_pkey PRIMARY KEY (id);


--
-- Name: ai_daily_work_logs ai_daily_work_logs_employee_date_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_daily_work_logs
    ADD CONSTRAINT ai_daily_work_logs_employee_date_key UNIQUE (employee_id, work_date);


--
-- Name: ai_daily_work_logs ai_daily_work_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_daily_work_logs
    ADD CONSTRAINT ai_daily_work_logs_pkey PRIMARY KEY (id);


--
-- Name: ai_gateway_admissions ai_gateway_admissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_admissions
    ADD CONSTRAINT ai_gateway_admissions_pkey PRIMARY KEY (id);


--
-- Name: ai_gateway_admissions ai_gateway_admissions_receipt_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_admissions
    ADD CONSTRAINT ai_gateway_admissions_receipt_hash_key UNIQUE (receipt_hash);


--
-- Name: ai_gateway_events ai_gateway_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_events
    ADD CONSTRAINT ai_gateway_events_pkey PRIMARY KEY (id);


--
-- Name: ai_gateway_key_allowances ai_gateway_key_allowances_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_key_allowances
    ADD CONSTRAINT ai_gateway_key_allowances_pkey PRIMARY KEY (user_id);


--
-- Name: ai_gateway_key_projects ai_gateway_key_projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_key_projects
    ADD CONSTRAINT ai_gateway_key_projects_pkey PRIMARY KEY (key_id);


--
-- Name: ai_gateway_key_requests ai_gateway_key_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_key_requests
    ADD CONSTRAINT ai_gateway_key_requests_pkey PRIMARY KEY (id);


--
-- Name: ai_gateway_keys ai_gateway_keys_key_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_keys
    ADD CONSTRAINT ai_gateway_keys_key_hash_key UNIQUE (key_hash);


--
-- Name: ai_gateway_keys ai_gateway_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_keys
    ADD CONSTRAINT ai_gateway_keys_pkey PRIMARY KEY (id);


--
-- Name: ai_monitor_devices ai_monitor_devices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_monitor_devices
    ADD CONSTRAINT ai_monitor_devices_pkey PRIMARY KEY (id);


--
-- Name: ai_usage_leaderboard_daily ai_usage_leaderboard_daily_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_usage_leaderboard_daily
    ADD CONSTRAINT ai_usage_leaderboard_daily_pkey PRIMARY KEY (usage_date, user_id, origin, source, app, model);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: billing_audit_logs billing_audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.billing_audit_logs
    ADD CONSTRAINT billing_audit_logs_pkey PRIMARY KEY (id);


--
-- Name: billing_periods billing_periods_org_id_period_start_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.billing_periods
    ADD CONSTRAINT billing_periods_org_id_period_start_key UNIQUE (org_id, period_start);


--
-- Name: billing_periods billing_periods_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.billing_periods
    ADD CONSTRAINT billing_periods_pkey PRIMARY KEY (id);


--
-- Name: cc_switch_attributed_requests cc_switch_attributed_request_identity; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_attributed_requests
    ADD CONSTRAINT cc_switch_attributed_request_identity UNIQUE (device_id, request_id);


--
-- Name: cc_switch_attributed_requests cc_switch_attributed_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_attributed_requests
    ADD CONSTRAINT cc_switch_attributed_requests_pkey PRIMARY KEY (id);


--
-- Name: cc_switch_attribution_sessions cc_switch_attribution_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_attribution_sessions
    ADD CONSTRAINT cc_switch_attribution_sessions_pkey PRIMARY KEY (id);


--
-- Name: cc_switch_temporary_monitor_probes cc_switch_temporary_monitor_probes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_temporary_monitor_probes
    ADD CONSTRAINT cc_switch_temporary_monitor_probes_pkey PRIMARY KEY (id);


--
-- Name: cc_switch_usage_daily cc_switch_usage_daily_identity_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_usage_daily
    ADD CONSTRAINT cc_switch_usage_daily_identity_key UNIQUE (user_id, device_id, usage_date, app_type, provider_id, model, request_model, pricing_model);


--
-- Name: cc_switch_usage_daily cc_switch_usage_daily_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_usage_daily
    ADD CONSTRAINT cc_switch_usage_daily_pkey PRIMARY KEY (id);


--
-- Name: cc_switch_usage_sync_status cc_switch_usage_sync_status_device_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_usage_sync_status
    ADD CONSTRAINT cc_switch_usage_sync_status_device_key UNIQUE (user_id, device_id);


--
-- Name: cc_switch_usage_sync_status cc_switch_usage_sync_status_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_usage_sync_status
    ADD CONSTRAINT cc_switch_usage_sync_status_pkey PRIMARY KEY (id);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (id);


--
-- Name: developer_errors developer_errors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.developer_errors
    ADD CONSTRAINT developer_errors_pkey PRIMARY KEY (id);


--
-- Name: document_chunks document_chunks_document_id_chunk_index_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_document_id_chunk_index_key UNIQUE (document_id, chunk_index);


--
-- Name: document_chunks document_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_pkey PRIMARY KEY (id);


--
-- Name: document_chunks_v2 document_chunks_v2_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks_v2
    ADD CONSTRAINT document_chunks_v2_pkey PRIMARY KEY (id);


--
-- Name: document_chunks_v3_shadow document_chunks_v3_shadow_document_id_retrieval_version_chunk_k; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks_v3_shadow
    ADD CONSTRAINT document_chunks_v3_shadow_document_id_retrieval_version_chunk_k UNIQUE (document_id, retrieval_version, chunker_version, parser_version, chunk_index);


--
-- Name: document_chunks_v3_shadow document_chunks_v3_shadow_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks_v3_shadow
    ADD CONSTRAINT document_chunks_v3_shadow_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: documents documents_source_relative_path_safe; Type: CHECK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.documents
    ADD CONSTRAINT documents_source_relative_path_safe CHECK (((source_relative_path IS NULL) OR ((source_relative_path <> ''::text) AND (source_relative_path !~ '^/'::text) AND (source_relative_path !~ '^[A-Za-z]:'::text) AND (source_relative_path !~ '(^|/)\.\.(/|$)'::text) AND (source_relative_path !~ '\\'::text)))) NOT VALID;


--
-- Name: documents documents_version_conflict_reason_present; Type: CHECK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.documents
    ADD CONSTRAINT documents_version_conflict_reason_present CHECK (((version_conflict = false) OR (NULLIF(version_conflict_reason, ''::text) IS NOT NULL))) NOT VALID;


--
-- Name: documents documents_version_number_positive; Type: CHECK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.documents
    ADD CONSTRAINT documents_version_number_positive CHECK (((version_number IS NULL) OR (version_number > 0))) NOT VALID;


--
-- Name: errors errors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.errors
    ADD CONSTRAINT errors_pkey PRIMARY KEY (id);


--
-- Name: ingest_queue_receipts ingest_queue_receipts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingest_queue_receipts
    ADD CONSTRAINT ingest_queue_receipts_pkey PRIMARY KEY (id);


--
-- Name: ingest_queue_receipts ingest_queue_receipts_stream_payload_fingerprint_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingest_queue_receipts
    ADD CONSTRAINT ingest_queue_receipts_stream_payload_fingerprint_key UNIQUE (stream, payload_fingerprint);


--
-- Name: llm_credential_refs llm_credential_refs_creation_operation_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_credential_refs
    ADD CONSTRAINT llm_credential_refs_creation_operation_id_key UNIQUE (creation_operation_id);


--
-- Name: llm_credential_refs llm_credential_refs_instance_id_key_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_credential_refs
    ADD CONSTRAINT llm_credential_refs_instance_id_key_hash_key UNIQUE (instance_id, key_hash);


--
-- Name: llm_credential_refs llm_credential_refs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_credential_refs
    ADD CONSTRAINT llm_credential_refs_pkey PRIMARY KEY (id);


--
-- Name: llm_gateway_instances llm_gateway_instances_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_gateway_instances
    ADD CONSTRAINT llm_gateway_instances_pkey PRIMARY KEY (id);


--
-- Name: llm_key_operations llm_key_operations_id_user_id_instance_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_key_operations
    ADD CONSTRAINT llm_key_operations_id_user_id_instance_id_key UNIQUE (id, user_id, instance_id);


--
-- Name: llm_key_operations llm_key_operations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_key_operations
    ADD CONSTRAINT llm_key_operations_pkey PRIMARY KEY (id);


--
-- Name: llm_key_operations llm_key_operations_user_id_kind_idempotency_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_key_operations
    ADD CONSTRAINT llm_key_operations_user_id_kind_idempotency_key_key UNIQUE (user_id, kind, idempotency_key);


--
-- Name: llm_member_rollout llm_member_rollout_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_member_rollout
    ADD CONSTRAINT llm_member_rollout_pkey PRIMARY KEY (user_id);


--
-- Name: llms llms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llms
    ADD CONSTRAINT llms_pkey PRIMARY KEY (id);


--
-- Name: project_material_intake_files material_intake_files_relative_path_safe; Type: CHECK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.project_material_intake_files
    ADD CONSTRAINT material_intake_files_relative_path_safe CHECK (((relative_path IS NULL) OR ((relative_path <> ''::text) AND (relative_path !~ '^/'::text) AND (relative_path !~ '^[A-Za-z]:'::text) AND (relative_path !~ '(^|/)\.\.(/|$)'::text) AND (relative_path !~ '\\'::text)))) NOT VALID;


--
-- Name: meeting_summaries meeting_summaries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meeting_summaries
    ADD CONSTRAINT meeting_summaries_pkey PRIMARY KEY (id);


--
-- Name: meeting_summary_files meeting_summary_files_meeting_summary_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meeting_summary_files
    ADD CONSTRAINT meeting_summary_files_meeting_summary_id_key UNIQUE (meeting_summary_id);


--
-- Name: meeting_summary_files meeting_summary_files_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meeting_summary_files
    ADD CONSTRAINT meeting_summary_files_pkey PRIMARY KEY (id);


--
-- Name: member_wiki_experience_sources member_wiki_experience_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_wiki_experience_sources
    ADD CONSTRAINT member_wiki_experience_sources_pkey PRIMARY KEY (experience_id, session_id);


--
-- Name: member_wiki_experience_versions member_wiki_experience_versions_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_wiki_experience_versions
    ADD CONSTRAINT member_wiki_experience_versions_key UNIQUE (experience_id, version);


--
-- Name: member_wiki_experience_versions member_wiki_experience_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_wiki_experience_versions
    ADD CONSTRAINT member_wiki_experience_versions_pkey PRIMARY KEY (id);


--
-- Name: member_wiki_experiences member_wiki_experiences_employee_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_wiki_experiences
    ADD CONSTRAINT member_wiki_experiences_employee_key UNIQUE (employee_id, experience_key);


--
-- Name: member_wiki_experiences member_wiki_experiences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_wiki_experiences
    ADD CONSTRAINT member_wiki_experiences_pkey PRIMARY KEY (id);


--
-- Name: member_wiki_processed_sessions member_wiki_processed_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_wiki_processed_sessions
    ADD CONSTRAINT member_wiki_processed_sessions_pkey PRIMARY KEY (session_id);


--
-- Name: member_wiki_runs member_wiki_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_wiki_runs
    ADD CONSTRAINT member_wiki_runs_pkey PRIMARY KEY (id);


--
-- Name: org_invites org_invites_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_invites
    ADD CONSTRAINT org_invites_pkey PRIMARY KEY (org_id, invitee_email);


--
-- Name: orgs orgs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.orgs
    ADD CONSTRAINT orgs_pkey PRIMARY KEY (id);


--
-- Name: prices prices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prices
    ADD CONSTRAINT prices_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: project_agents_file_versions project_agents_file_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_agents_file_versions
    ADD CONSTRAINT project_agents_file_versions_pkey PRIMARY KEY (project_id, version);


--
-- Name: project_agents_files project_agents_files_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_agents_files
    ADD CONSTRAINT project_agents_files_pkey PRIMARY KEY (project_id);


--
-- Name: project_context_tokens project_context_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_context_tokens
    ADD CONSTRAINT project_context_tokens_pkey PRIMARY KEY (id);


--
-- Name: project_context_tokens project_context_tokens_token_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_context_tokens
    ADD CONSTRAINT project_context_tokens_token_hash_key UNIQUE (token_hash);


--
-- Name: project_conversation_record_attempts project_conversation_record_attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_conversation_record_attempts
    ADD CONSTRAINT project_conversation_record_attempts_pkey PRIMARY KEY (id);


--
-- Name: project_conversation_records project_conversation_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_conversation_records
    ADD CONSTRAINT project_conversation_records_pkey PRIMARY KEY (id);


--
-- Name: project_conversation_records project_conversation_records_project_id_request_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_conversation_records
    ADD CONSTRAINT project_conversation_records_project_id_request_id_key UNIQUE (project_id, request_id);


--
-- Name: project_creation_requests project_creation_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_creation_requests
    ADD CONSTRAINT project_creation_requests_pkey PRIMARY KEY (id);


--
-- Name: project_department_migrations project_department_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_department_migrations
    ADD CONSTRAINT project_department_migrations_pkey PRIMARY KEY (id);


--
-- Name: project_material_documents project_material_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_material_documents
    ADD CONSTRAINT project_material_documents_pkey PRIMARY KEY (document_id);


--
-- Name: project_material_intake_files project_material_intake_files_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_material_intake_files
    ADD CONSTRAINT project_material_intake_files_pkey PRIMARY KEY (id);


--
-- Name: project_material_intakes project_material_intakes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_material_intakes
    ADD CONSTRAINT project_material_intakes_pkey PRIMARY KEY (id);


--
-- Name: project_material_parse_jobs project_material_parse_jobs_intake_file_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_material_parse_jobs
    ADD CONSTRAINT project_material_parse_jobs_intake_file_id_key UNIQUE (intake_file_id);


--
-- Name: project_material_parse_jobs project_material_parse_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_material_parse_jobs
    ADD CONSTRAINT project_material_parse_jobs_pkey PRIMARY KEY (id);


--
-- Name: project_members project_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_pkey PRIMARY KEY (project_id, user_id);


--
-- Name: project_memory_approval_jobs project_memory_approval_jobs_draft_id_decision_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_memory_approval_jobs
    ADD CONSTRAINT project_memory_approval_jobs_draft_id_decision_key UNIQUE (draft_id, decision);


--
-- Name: project_memory_approval_jobs project_memory_approval_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_memory_approval_jobs
    ADD CONSTRAINT project_memory_approval_jobs_pkey PRIMARY KEY (id);


--
-- Name: project_memory_draft_sources project_memory_draft_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_memory_draft_sources
    ADD CONSTRAINT project_memory_draft_sources_pkey PRIMARY KEY (id);


--
-- Name: project_memory_drafts project_memory_drafts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_memory_drafts
    ADD CONSTRAINT project_memory_drafts_pkey PRIMARY KEY (id);


--
-- Name: project_memory_reviews project_memory_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_memory_reviews
    ADD CONSTRAINT project_memory_reviews_pkey PRIMARY KEY (id);


--
-- Name: project_memory_submissions project_memory_submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_memory_submissions
    ADD CONSTRAINT project_memory_submissions_pkey PRIMARY KEY (id);


--
-- Name: project_repositories project_repositories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_repositories
    ADD CONSTRAINT project_repositories_pkey PRIMARY KEY (id);


--
-- Name: project_wiki_changes project_wiki_changes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_changes
    ADD CONSTRAINT project_wiki_changes_pkey PRIMARY KEY (id);


--
-- Name: project_wiki_compile_runs project_wiki_compile_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_compile_runs
    ADD CONSTRAINT project_wiki_compile_runs_pkey PRIMARY KEY (id);


--
-- Name: project_wiki_links project_wiki_links_from_page_id_to_title_relation_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_links
    ADD CONSTRAINT project_wiki_links_from_page_id_to_title_relation_key UNIQUE (from_page_id, to_title, relation);


--
-- Name: project_wiki_links project_wiki_links_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_links
    ADD CONSTRAINT project_wiki_links_pkey PRIMARY KEY (id);


--
-- Name: project_wiki_page_sources project_wiki_page_sources_page_id_source_type_source_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_page_sources
    ADD CONSTRAINT project_wiki_page_sources_page_id_source_type_source_id_key UNIQUE (page_id, source_type, source_id);


--
-- Name: project_wiki_page_sources project_wiki_page_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_page_sources
    ADD CONSTRAINT project_wiki_page_sources_pkey PRIMARY KEY (id);


--
-- Name: project_wiki_page_versions project_wiki_page_versions_page_id_version_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_page_versions
    ADD CONSTRAINT project_wiki_page_versions_page_id_version_key UNIQUE (page_id, version);


--
-- Name: project_wiki_page_versions project_wiki_page_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_page_versions
    ADD CONSTRAINT project_wiki_page_versions_pkey PRIMARY KEY (id);


--
-- Name: project_wiki_pages project_wiki_pages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_pages
    ADD CONSTRAINT project_wiki_pages_pkey PRIMARY KEY (id);


--
-- Name: project_wiki_pages project_wiki_pages_project_id_page_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_pages
    ADD CONSTRAINT project_wiki_pages_project_id_page_key_key UNIQUE (project_id, page_key);


--
-- Name: project_wiki_processed_sources project_wiki_processed_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_processed_sources
    ADD CONSTRAINT project_wiki_processed_sources_pkey PRIMARY KEY (project_id, source_id);


--
-- Name: projects projects_api_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_api_key_key UNIQUE (api_key);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: rag_v3_index_jobs rag_v3_index_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_v3_index_jobs
    ADD CONSTRAINT rag_v3_index_jobs_pkey PRIMARY KEY (id);


--
-- Name: rag_v3_index_jobs rag_v3_index_jobs_project_id_document_id_idempotency_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_v3_index_jobs
    ADD CONSTRAINT rag_v3_index_jobs_project_id_document_id_idempotency_key_key UNIQUE (project_id, document_id, idempotency_key);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: spans spans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.spans
    ADD CONSTRAINT spans_pkey PRIMARY KEY (id);


--
-- Name: stats stats_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stats
    ADD CONSTRAINT stats_pkey PRIMARY KEY (session_id);


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_pkey PRIMARY KEY (id);


--
-- Name: threads threads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.threads
    ADD CONSTRAINT threads_pkey PRIMARY KEY (id);


--
-- Name: tools tools_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tools
    ADD CONSTRAINT tools_pkey PRIMARY KEY (id);


--
-- Name: ttd ttd_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ttd
    ADD CONSTRAINT ttd_pkey PRIMARY KEY (id);


--
-- Name: document_chunks_v2 uq_doc_chunk_v2_index; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks_v2
    ADD CONSTRAINT uq_doc_chunk_v2_index UNIQUE (document_id, embedding_version, chunk_index);


--
-- Name: user_orgs user_orgs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_orgs
    ADD CONSTRAINT user_orgs_pkey PRIMARY KEY (user_id, org_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: webhook_events webhook_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.webhook_events
    ADD CONSTRAINT webhook_events_pkey PRIMARY KEY (event_id);


--
-- Name: wiki_mcp_tokens wiki_mcp_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wiki_mcp_tokens
    ADD CONSTRAINT wiki_mcp_tokens_pkey PRIMARY KEY (id);


--
-- Name: wiki_mcp_tokens wiki_mcp_tokens_token_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wiki_mcp_tokens
    ADD CONSTRAINT wiki_mcp_tokens_token_hash_key UNIQUE (token_hash);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id, inserted_at);


--
-- Name: messages_2026_07_14 messages_2026_07_14_pkey; Type: CONSTRAINT; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.messages_2026_07_14
    ADD CONSTRAINT messages_2026_07_14_pkey PRIMARY KEY (id, inserted_at);


--
-- Name: messages_2026_07_15 messages_2026_07_15_pkey; Type: CONSTRAINT; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.messages_2026_07_15
    ADD CONSTRAINT messages_2026_07_15_pkey PRIMARY KEY (id, inserted_at);


--
-- Name: messages_2026_07_16 messages_2026_07_16_pkey; Type: CONSTRAINT; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.messages_2026_07_16
    ADD CONSTRAINT messages_2026_07_16_pkey PRIMARY KEY (id, inserted_at);


--
-- Name: messages_2026_07_17 messages_2026_07_17_pkey; Type: CONSTRAINT; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.messages_2026_07_17
    ADD CONSTRAINT messages_2026_07_17_pkey PRIMARY KEY (id, inserted_at);


--
-- Name: messages_2026_07_18 messages_2026_07_18_pkey; Type: CONSTRAINT; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.messages_2026_07_18
    ADD CONSTRAINT messages_2026_07_18_pkey PRIMARY KEY (id, inserted_at);


--
-- Name: messages messages_payload_exclusive; Type: CHECK CONSTRAINT; Schema: realtime; Owner: -
--

ALTER TABLE realtime.messages
    ADD CONSTRAINT messages_payload_exclusive CHECK (((payload IS NULL) OR (binary_payload IS NULL))) NOT VALID;


--
-- Name: subscription pk_subscription; Type: CONSTRAINT; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.subscription
    ADD CONSTRAINT pk_subscription PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: realtime; Owner: -
--

ALTER TABLE ONLY realtime.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: buckets_analytics buckets_analytics_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.buckets_analytics
    ADD CONSTRAINT buckets_analytics_pkey PRIMARY KEY (id);


--
-- Name: buckets buckets_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.buckets
    ADD CONSTRAINT buckets_pkey PRIMARY KEY (id);


--
-- Name: buckets_vectors buckets_vectors_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.buckets_vectors
    ADD CONSTRAINT buckets_vectors_pkey PRIMARY KEY (id);


--
-- Name: iceberg_namespaces iceberg_namespaces_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.iceberg_namespaces
    ADD CONSTRAINT iceberg_namespaces_pkey PRIMARY KEY (id);


--
-- Name: iceberg_tables iceberg_tables_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.iceberg_tables
    ADD CONSTRAINT iceberg_tables_pkey PRIMARY KEY (id);


--
-- Name: migrations migrations_name_key; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.migrations
    ADD CONSTRAINT migrations_name_key UNIQUE (name);


--
-- Name: migrations migrations_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.migrations
    ADD CONSTRAINT migrations_pkey PRIMARY KEY (id);


--
-- Name: objects objects_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.objects
    ADD CONSTRAINT objects_pkey PRIMARY KEY (id);


--
-- Name: s3_multipart_uploads_parts s3_multipart_uploads_parts_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.s3_multipart_uploads_parts
    ADD CONSTRAINT s3_multipart_uploads_parts_pkey PRIMARY KEY (id);


--
-- Name: s3_multipart_uploads s3_multipart_uploads_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.s3_multipart_uploads
    ADD CONSTRAINT s3_multipart_uploads_pkey PRIMARY KEY (id);


--
-- Name: vector_indexes vector_indexes_pkey; Type: CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.vector_indexes
    ADD CONSTRAINT vector_indexes_pkey PRIMARY KEY (id);


--
-- Name: hooks hooks_pkey; Type: CONSTRAINT; Schema: supabase_functions; Owner: -
--

ALTER TABLE ONLY supabase_functions.hooks
    ADD CONSTRAINT hooks_pkey PRIMARY KEY (id);


--
-- Name: migrations migrations_pkey; Type: CONSTRAINT; Schema: supabase_functions; Owner: -
--

ALTER TABLE ONLY supabase_functions.migrations
    ADD CONSTRAINT migrations_pkey PRIMARY KEY (version);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: supabase_migrations; Owner: -
--

ALTER TABLE ONLY supabase_migrations.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: seed_files seed_files_pkey; Type: CONSTRAINT; Schema: supabase_migrations; Owner: -
--

ALTER TABLE ONLY supabase_migrations.seed_files
    ADD CONSTRAINT seed_files_pkey PRIMARY KEY (path);


--
-- Name: extensions_tenant_external_id_index; Type: INDEX; Schema: _realtime; Owner: -
--

CREATE INDEX extensions_tenant_external_id_index ON _realtime.extensions USING btree (tenant_external_id);


--
-- Name: extensions_tenant_external_id_type_index; Type: INDEX; Schema: _realtime; Owner: -
--

CREATE UNIQUE INDEX extensions_tenant_external_id_type_index ON _realtime.extensions USING btree (tenant_external_id, type);


--
-- Name: feature_flags_name_index; Type: INDEX; Schema: _realtime; Owner: -
--

CREATE UNIQUE INDEX feature_flags_name_index ON _realtime.feature_flags USING btree (name);


--
-- Name: tenants_external_id_index; Type: INDEX; Schema: _realtime; Owner: -
--

CREATE UNIQUE INDEX tenants_external_id_index ON _realtime.tenants USING btree (external_id);


--
-- Name: audit_logs_instance_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX audit_logs_instance_id_idx ON auth.audit_log_entries USING btree (instance_id);


--
-- Name: confirmation_token_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX confirmation_token_idx ON auth.users USING btree (confirmation_token) WHERE ((confirmation_token)::text !~ '^[0-9 ]*$'::text);


--
-- Name: custom_oauth_providers_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX custom_oauth_providers_created_at_idx ON auth.custom_oauth_providers USING btree (created_at);


--
-- Name: custom_oauth_providers_enabled_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX custom_oauth_providers_enabled_idx ON auth.custom_oauth_providers USING btree (enabled);


--
-- Name: custom_oauth_providers_identifier_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX custom_oauth_providers_identifier_idx ON auth.custom_oauth_providers USING btree (identifier);


--
-- Name: custom_oauth_providers_provider_type_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX custom_oauth_providers_provider_type_idx ON auth.custom_oauth_providers USING btree (provider_type);


--
-- Name: email_change_token_current_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX email_change_token_current_idx ON auth.users USING btree (email_change_token_current) WHERE ((email_change_token_current)::text !~ '^[0-9 ]*$'::text);


--
-- Name: email_change_token_new_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX email_change_token_new_idx ON auth.users USING btree (email_change_token_new) WHERE ((email_change_token_new)::text !~ '^[0-9 ]*$'::text);


--
-- Name: factor_id_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX factor_id_created_at_idx ON auth.mfa_factors USING btree (user_id, created_at);


--
-- Name: flow_state_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX flow_state_created_at_idx ON auth.flow_state USING btree (created_at DESC);


--
-- Name: identities_email_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX identities_email_idx ON auth.identities USING btree (email text_pattern_ops);


--
-- Name: INDEX identities_email_idx; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON INDEX auth.identities_email_idx IS 'Auth: Ensures indexed queries on the email column';


--
-- Name: identities_user_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX identities_user_id_idx ON auth.identities USING btree (user_id);


--
-- Name: idx_auth_code; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX idx_auth_code ON auth.flow_state USING btree (auth_code);


--
-- Name: idx_oauth_client_states_created_at; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX idx_oauth_client_states_created_at ON auth.oauth_client_states USING btree (created_at);


--
-- Name: idx_user_id_auth_method; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX idx_user_id_auth_method ON auth.flow_state USING btree (user_id, authentication_method);


--
-- Name: mfa_challenge_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX mfa_challenge_created_at_idx ON auth.mfa_challenges USING btree (created_at DESC);


--
-- Name: mfa_factors_user_friendly_name_unique; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX mfa_factors_user_friendly_name_unique ON auth.mfa_factors USING btree (friendly_name, user_id) WHERE (TRIM(BOTH FROM friendly_name) <> ''::text);


--
-- Name: mfa_factors_user_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX mfa_factors_user_id_idx ON auth.mfa_factors USING btree (user_id);


--
-- Name: oauth_auth_pending_exp_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX oauth_auth_pending_exp_idx ON auth.oauth_authorizations USING btree (expires_at) WHERE (status = 'pending'::auth.oauth_authorization_status);


--
-- Name: oauth_clients_deleted_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX oauth_clients_deleted_at_idx ON auth.oauth_clients USING btree (deleted_at);


--
-- Name: oauth_consents_active_client_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX oauth_consents_active_client_idx ON auth.oauth_consents USING btree (client_id) WHERE (revoked_at IS NULL);


--
-- Name: oauth_consents_active_user_client_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX oauth_consents_active_user_client_idx ON auth.oauth_consents USING btree (user_id, client_id) WHERE (revoked_at IS NULL);


--
-- Name: oauth_consents_user_order_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX oauth_consents_user_order_idx ON auth.oauth_consents USING btree (user_id, granted_at DESC);


--
-- Name: one_time_tokens_relates_to_hash_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX one_time_tokens_relates_to_hash_idx ON auth.one_time_tokens USING hash (relates_to);


--
-- Name: one_time_tokens_token_hash_hash_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX one_time_tokens_token_hash_hash_idx ON auth.one_time_tokens USING hash (token_hash);


--
-- Name: one_time_tokens_user_id_token_type_key; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX one_time_tokens_user_id_token_type_key ON auth.one_time_tokens USING btree (user_id, token_type);


--
-- Name: reauthentication_token_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX reauthentication_token_idx ON auth.users USING btree (reauthentication_token) WHERE ((reauthentication_token)::text !~ '^[0-9 ]*$'::text);


--
-- Name: recovery_token_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX recovery_token_idx ON auth.users USING btree (recovery_token) WHERE ((recovery_token)::text !~ '^[0-9 ]*$'::text);


--
-- Name: refresh_tokens_instance_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX refresh_tokens_instance_id_idx ON auth.refresh_tokens USING btree (instance_id);


--
-- Name: refresh_tokens_instance_id_user_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX refresh_tokens_instance_id_user_id_idx ON auth.refresh_tokens USING btree (instance_id, user_id);


--
-- Name: refresh_tokens_parent_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX refresh_tokens_parent_idx ON auth.refresh_tokens USING btree (parent);


--
-- Name: refresh_tokens_session_id_revoked_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX refresh_tokens_session_id_revoked_idx ON auth.refresh_tokens USING btree (session_id, revoked);


--
-- Name: refresh_tokens_updated_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX refresh_tokens_updated_at_idx ON auth.refresh_tokens USING btree (updated_at DESC);


--
-- Name: saml_providers_sso_provider_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX saml_providers_sso_provider_id_idx ON auth.saml_providers USING btree (sso_provider_id);


--
-- Name: saml_relay_states_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX saml_relay_states_created_at_idx ON auth.saml_relay_states USING btree (created_at DESC);


--
-- Name: saml_relay_states_for_email_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX saml_relay_states_for_email_idx ON auth.saml_relay_states USING btree (for_email);


--
-- Name: saml_relay_states_sso_provider_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX saml_relay_states_sso_provider_id_idx ON auth.saml_relay_states USING btree (sso_provider_id);


--
-- Name: sessions_not_after_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX sessions_not_after_idx ON auth.sessions USING btree (not_after DESC);


--
-- Name: sessions_oauth_client_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX sessions_oauth_client_id_idx ON auth.sessions USING btree (oauth_client_id);


--
-- Name: sessions_user_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX sessions_user_id_idx ON auth.sessions USING btree (user_id);


--
-- Name: sso_domains_domain_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX sso_domains_domain_idx ON auth.sso_domains USING btree (lower(domain));


--
-- Name: sso_domains_sso_provider_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX sso_domains_sso_provider_id_idx ON auth.sso_domains USING btree (sso_provider_id);


--
-- Name: sso_providers_resource_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX sso_providers_resource_id_idx ON auth.sso_providers USING btree (lower(resource_id));


--
-- Name: sso_providers_resource_id_pattern_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX sso_providers_resource_id_pattern_idx ON auth.sso_providers USING btree (resource_id text_pattern_ops);


--
-- Name: unique_phone_factor_per_user; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX unique_phone_factor_per_user ON auth.mfa_factors USING btree (user_id, phone);


--
-- Name: user_id_created_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX user_id_created_at_idx ON auth.sessions USING btree (user_id, created_at);


--
-- Name: users_email_partial_key; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX users_email_partial_key ON auth.users USING btree (email) WHERE (is_sso_user = false);


--
-- Name: INDEX users_email_partial_key; Type: COMMENT; Schema: auth; Owner: -
--

COMMENT ON INDEX auth.users_email_partial_key IS 'Auth: A partial unique index that applies only when is_sso_user is false';


--
-- Name: users_instance_id_email_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX users_instance_id_email_idx ON auth.users USING btree (instance_id, lower((email)::text));


--
-- Name: users_instance_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX users_instance_id_idx ON auth.users USING btree (instance_id);


--
-- Name: users_is_anonymous_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX users_is_anonymous_idx ON auth.users USING btree (is_anonymous);


--
-- Name: webauthn_challenges_expires_at_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX webauthn_challenges_expires_at_idx ON auth.webauthn_challenges USING btree (expires_at);


--
-- Name: webauthn_challenges_user_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX webauthn_challenges_user_id_idx ON auth.webauthn_challenges USING btree (user_id);


--
-- Name: webauthn_credentials_credential_id_key; Type: INDEX; Schema: auth; Owner: -
--

CREATE UNIQUE INDEX webauthn_credentials_credential_id_key ON auth.webauthn_credentials USING btree (credential_id);


--
-- Name: webauthn_credentials_user_id_idx; Type: INDEX; Schema: auth; Owner: -
--

CREATE INDEX webauthn_credentials_user_id_idx ON auth.webauthn_credentials USING btree (user_id);


--
-- Name: deployments_project_id_idx; Type: INDEX; Schema: deploy; Owner: -
--

CREATE INDEX deployments_project_id_idx ON deploy.deployments USING btree (project_id);


--
-- Name: actions_agent_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX actions_agent_id_idx ON public.actions USING btree (agent_id);


--
-- Name: actions_session_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX actions_session_id_idx ON public.actions USING btree (session_id);


--
-- Name: agents_session_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX agents_session_id_idx ON public.agents USING btree (session_id);


--
-- Name: ai_gateway_admissions_member_time_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ai_gateway_admissions_member_time_idx ON public.ai_gateway_admissions USING btree (user_id, admitted_at);


--
-- Name: ai_gateway_events_chat_session_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ai_gateway_events_chat_session_idx ON public.ai_gateway_events USING btree (chat_session_id) WHERE (chat_session_id IS NOT NULL);


--
-- Name: ai_gateway_events_conversation_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ai_gateway_events_conversation_idx ON public.ai_gateway_events USING btree (user_id, conversation_id) WHERE (conversation_id IS NOT NULL);


--
-- Name: ai_gateway_events_employee_date_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ai_gateway_events_employee_date_idx ON public.ai_gateway_events USING btree (employee_id, usage_date);


--
-- Name: ai_gateway_events_instance_event_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ai_gateway_events_instance_event_idx ON public.ai_gateway_events USING btree (gateway_instance_id, event_id);


--
-- Name: ai_gateway_events_request_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ai_gateway_events_request_idx ON public.ai_gateway_events USING btree (gateway_instance_id, request_id) WHERE (request_id IS NOT NULL);


--
-- Name: ai_gateway_key_projects_project_user_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ai_gateway_key_projects_project_user_idx ON public.ai_gateway_key_projects USING btree (project_id, user_id);


--
-- Name: ai_gateway_key_requests_one_pending; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ai_gateway_key_requests_one_pending ON public.ai_gateway_key_requests USING btree (user_id) WHERE (status = 'pending'::text);


--
-- Name: ai_gateway_keys_user_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ai_gateway_keys_user_idx ON public.ai_gateway_keys USING btree (user_id, is_active);


--
-- Name: ai_gateway_keys_visible_user_created_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ai_gateway_keys_visible_user_created_idx ON public.ai_gateway_keys USING btree (user_id, created_at DESC) WHERE (hidden_at IS NULL);


--
-- Name: ai_gateway_sessions_gateway_event_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ai_gateway_sessions_gateway_event_idx ON public.ai_chat_sessions USING btree (gateway_instance_id, gateway_event_id) WHERE ((gateway_instance_id IS NOT NULL) AND (gateway_event_id IS NOT NULL));


--
-- Name: cc_switch_usage_daily_employee_date_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cc_switch_usage_daily_employee_date_idx ON public.cc_switch_usage_daily USING btree (employee_id, usage_date);


--
-- Name: cc_switch_usage_daily_user_date_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cc_switch_usage_daily_user_date_idx ON public.cc_switch_usage_daily USING btree (user_id, usage_date);


--
-- Name: cc_switch_usage_sync_status_request_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX cc_switch_usage_sync_status_request_idx ON public.cc_switch_usage_sync_status USING btree (user_id, request_id) WHERE (request_id IS NOT NULL);


--
-- Name: departments_child_name_unique_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX departments_child_name_unique_idx ON public.departments USING btree (parent_id, lower(btrim(name))) WHERE (parent_id IS NOT NULL);


--
-- Name: departments_one_direct_child_per_root_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX departments_one_direct_child_per_root_idx ON public.departments USING btree (parent_id) WHERE is_direct;


--
-- Name: departments_parent_sort_order_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX departments_parent_sort_order_idx ON public.departments USING btree (parent_id, sort_order, id);


--
-- Name: departments_root_name_unique_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX departments_root_name_unique_idx ON public.departments USING btree (lower(btrim(name))) WHERE (parent_id IS NULL);


--
-- Name: errors_session_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX errors_session_id_idx ON public.errors USING btree (session_id);


--
-- Name: idx_ai_chat_messages_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_chat_messages_session ON public.ai_chat_messages USING btree (session_id, sequence_index);


--
-- Name: idx_ai_chat_sessions_employee_started; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_chat_sessions_employee_started ON public.ai_chat_sessions USING btree (employee_id, started_at DESC);


--
-- Name: idx_ai_chat_sessions_employee_started_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_chat_sessions_employee_started_at ON public.ai_chat_sessions USING btree (employee_id, started_at);


--
-- Name: idx_ai_chat_sessions_project_started; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_chat_sessions_project_started ON public.ai_chat_sessions USING btree (project_id, started_at DESC);


--
-- Name: idx_ai_chat_sessions_source_started; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_chat_sessions_source_started ON public.ai_chat_sessions USING btree (source, started_at DESC);


--
-- Name: idx_ai_chat_sessions_started_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_chat_sessions_started_at ON public.ai_chat_sessions USING btree (started_at);


--
-- Name: idx_ai_chat_sessions_task; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_chat_sessions_task ON public.ai_chat_sessions USING btree (project_id, task_id);


--
-- Name: idx_ai_daily_work_logs_employee_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_daily_work_logs_employee_date ON public.ai_daily_work_logs USING btree (employee_id, work_date DESC);


--
-- Name: idx_ai_gateway_key_requests_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_gateway_key_requests_status ON public.ai_gateway_key_requests USING btree (status, created_at DESC);


--
-- Name: idx_ai_monitor_devices_project_employee; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_monitor_devices_project_employee ON public.ai_monitor_devices USING btree (project_id, employee_id, last_seen_at DESC);


--
-- Name: idx_ai_usage_leaderboard_daily_range; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_usage_leaderboard_daily_range ON public.ai_usage_leaderboard_daily USING btree (usage_date, employee_id);


--
-- Name: idx_audit_action_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_action_time ON public.audit_logs USING btree (action, created_at DESC);


--
-- Name: idx_audit_user_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_user_time ON public.audit_logs USING btree (user_id, created_at DESC);


--
-- Name: idx_billing_audit_logs_org_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_billing_audit_logs_org_id ON public.billing_audit_logs USING btree (org_id);


--
-- Name: idx_billing_periods_org; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_billing_periods_org ON public.billing_periods USING btree (org_id, period_end DESC);


--
-- Name: idx_cc_switch_attributed_member_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cc_switch_attributed_member_date ON public.cc_switch_attributed_requests USING btree (target_employee_id, usage_date);


--
-- Name: idx_cc_switch_attributed_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cc_switch_attributed_session ON public.cc_switch_attributed_requests USING btree (session_id, requested_at);


--
-- Name: idx_cc_switch_attribution_schedule; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cc_switch_attribution_schedule ON public.cc_switch_attribution_sessions USING btree (scheduled_stop_at) WHERE (status = 'active'::text);


--
-- Name: idx_cc_switch_attribution_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cc_switch_attribution_target ON public.cc_switch_attribution_sessions USING btree (target_user_id, requested_at DESC);


--
-- Name: idx_cc_switch_temporary_monitor_probes_expiry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cc_switch_temporary_monitor_probes_expiry ON public.cc_switch_temporary_monitor_probes USING btree (expires_at) WHERE (consumed_at IS NULL);


--
-- Name: idx_cc_switch_temporary_monitor_probes_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cc_switch_temporary_monitor_probes_user ON public.cc_switch_temporary_monitor_probes USING btree (target_user_id, created_at DESC);


--
-- Name: idx_document_chunks_document_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_document_id ON public.document_chunks USING btree (document_id);


--
-- Name: idx_document_chunks_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_embedding ON public.document_chunks USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_document_chunks_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_project_id ON public.document_chunks USING btree (project_id);


--
-- Name: idx_document_chunks_v2_content_tsv; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_v2_content_tsv ON public.document_chunks_v2 USING gin (content_tsv);


--
-- Name: idx_document_chunks_v2_document_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_v2_document_id ON public.document_chunks_v2 USING btree (document_id);


--
-- Name: idx_document_chunks_v2_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_v2_embedding ON public.document_chunks_v2 USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_document_chunks_v2_model_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_v2_model_version ON public.document_chunks_v2 USING btree (embedding_model, embedding_version);


--
-- Name: idx_document_chunks_v2_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_v2_project_id ON public.document_chunks_v2 USING btree (project_id);


--
-- Name: idx_document_chunks_v3_shadow_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_v3_shadow_embedding ON public.document_chunks_v3_shadow USING hnsw (embedding public.vector_cosine_ops) WHERE (embedding IS NOT NULL);


--
-- Name: idx_document_chunks_v3_shadow_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_v3_shadow_project ON public.document_chunks_v3_shadow USING btree (project_id, document_id);


--
-- Name: idx_document_chunks_v3_shadow_tsv; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_chunks_v3_shadow_tsv ON public.document_chunks_v3_shadow USING gin (content_tsv);


--
-- Name: idx_documents_asset_family_current; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_asset_family_current ON public.documents USING btree (project_id, asset_family_id, is_current) WHERE (is_current = true);


--
-- Name: idx_documents_project_family_version; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_documents_project_family_version ON public.documents USING btree (project_id, asset_family_id, version_number) WHERE ((asset_family_id IS NOT NULL) AND (version_number IS NOT NULL));


--
-- Name: idx_documents_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_project_id ON public.documents USING btree (project_id);


--
-- Name: idx_documents_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documents_status ON public.documents USING btree (status);


--
-- Name: idx_ingest_queue_receipts_pending; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ingest_queue_receipts_pending ON public.ingest_queue_receipts USING btree (status, next_attempt_at) WHERE (status = ANY (ARRAY['accepted'::text, 'processing'::text]));


--
-- Name: idx_material_parse_jobs_claim; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_material_parse_jobs_claim ON public.project_material_parse_jobs USING btree (status, next_attempt_at, created_at);


--
-- Name: idx_material_parse_jobs_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_material_parse_jobs_project ON public.project_material_parse_jobs USING btree (project_id, created_at DESC);


--
-- Name: idx_meeting_summaries_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_meeting_summaries_embedding_hnsw ON public.meeting_summaries USING hnsw (embedding public.vector_cosine_ops) WHERE (embedding IS NOT NULL);


--
-- Name: idx_meeting_summaries_project_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_meeting_summaries_project_date ON public.meeting_summaries USING btree (project_id, meeting_date DESC, created_at DESC);


--
-- Name: idx_meeting_summaries_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_meeting_summaries_tags ON public.meeting_summaries USING gin (tags);


--
-- Name: idx_meeting_summaries_title_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_meeting_summaries_title_trgm ON public.meeting_summaries USING gin (title public.gin_trgm_ops);


--
-- Name: idx_meeting_summary_files_content_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_meeting_summary_files_content_hash ON public.meeting_summary_files USING btree (content_hash);


--
-- Name: idx_member_wiki_experiences_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_member_wiki_experiences_embedding ON public.member_wiki_experiences USING hnsw (embedding public.vector_cosine_ops) WHERE (embedding IS NOT NULL);


--
-- Name: idx_member_wiki_experiences_member_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_member_wiki_experiences_member_type ON public.member_wiki_experiences USING btree (employee_id, task_type, outcome, last_observed DESC) WHERE (status = 'active'::text);


--
-- Name: idx_member_wiki_experiences_member_updated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_member_wiki_experiences_member_updated ON public.member_wiki_experiences USING btree (employee_id, updated_at DESC) WHERE (status = 'active'::text);


--
-- Name: idx_member_wiki_experiences_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_member_wiki_experiences_tags ON public.member_wiki_experiences USING gin (tags);


--
-- Name: idx_member_wiki_experiences_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_member_wiki_experiences_trgm ON public.member_wiki_experiences USING gin ((((((title || ' '::text) || summary) || ' '::text) || markdown_content)) public.gin_trgm_ops);


--
-- Name: idx_member_wiki_processed_employee; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_member_wiki_processed_employee ON public.member_wiki_processed_sessions USING btree (employee_id, observed_at DESC);


--
-- Name: idx_member_wiki_runs_started; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_member_wiki_runs_started ON public.member_wiki_runs USING btree (started_at DESC);


--
-- Name: idx_member_wiki_sources_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_member_wiki_sources_session ON public.member_wiki_experience_sources USING btree (session_id);


--
-- Name: idx_member_wiki_versions_experience; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_member_wiki_versions_experience ON public.member_wiki_experience_versions USING btree (experience_id, version DESC);


--
-- Name: idx_org_invites_invitee_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_invites_invitee_email ON public.org_invites USING btree (invitee_email);


--
-- Name: idx_org_invites_inviter_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_org_invites_inviter_id ON public.org_invites USING btree (inviter_id);


--
-- Name: idx_project_agents_versions_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_agents_versions_project ON public.project_agents_file_versions USING btree (project_id, version DESC);


--
-- Name: idx_project_context_tokens_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_context_tokens_lookup ON public.project_context_tokens USING btree (user_id, key_id, expires_at DESC) WHERE (revoked_at IS NULL);


--
-- Name: idx_project_conversation_records_project_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_conversation_records_project_created ON public.project_conversation_records USING btree (project_id, created_at DESC);


--
-- Name: idx_project_conversation_records_user_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_conversation_records_user_created ON public.project_conversation_records USING btree (user_id, created_at DESC);


--
-- Name: idx_project_conversation_records_wiki_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_conversation_records_wiki_status ON public.project_conversation_records USING btree (project_id, wiki_status, created_at DESC);


--
-- Name: idx_project_material_documents_draft; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_material_documents_draft ON public.project_material_documents USING btree (draft_id);


--
-- Name: idx_project_material_documents_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_material_documents_hash ON public.project_material_documents USING btree (project_id, content_hash) WHERE (content_hash IS NOT NULL);


--
-- Name: idx_project_material_documents_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_material_documents_project ON public.project_material_documents USING btree (project_id, uploaded_at DESC);


--
-- Name: idx_project_material_intake_files_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_material_intake_files_hash ON public.project_material_intake_files USING btree (content_hash);


--
-- Name: idx_project_material_intakes_project_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_material_intakes_project_status ON public.project_material_intakes USING btree (project_id, status, created_at DESC);


--
-- Name: idx_project_members_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_members_user ON public.project_members USING btree (user_id);


--
-- Name: idx_project_memory_draft_sources_draft; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_memory_draft_sources_draft ON public.project_memory_draft_sources USING btree (draft_id);


--
-- Name: idx_project_memory_drafts_department; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_memory_drafts_department ON public.project_memory_drafts USING btree (department_id, created_at DESC);


--
-- Name: idx_project_memory_drafts_project_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_memory_drafts_project_status ON public.project_memory_drafts USING btree (project_id, status, created_at DESC);


--
-- Name: idx_project_memory_reviews_draft; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_memory_reviews_draft ON public.project_memory_reviews USING btree (draft_id, created_at DESC);


--
-- Name: idx_project_memory_submissions_project_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_memory_submissions_project_status ON public.project_memory_submissions USING btree (project_id, status, created_at DESC);


--
-- Name: idx_project_repositories_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_repositories_project ON public.project_repositories USING btree (project_id, created_at DESC);


--
-- Name: idx_project_wiki_changes_project_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_wiki_changes_project_status ON public.project_wiki_changes USING btree (project_id, status, created_at DESC);


--
-- Name: idx_project_wiki_links_from; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_wiki_links_from ON public.project_wiki_links USING btree (from_page_id);


--
-- Name: idx_project_wiki_links_to; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_wiki_links_to ON public.project_wiki_links USING btree (to_page_id);


--
-- Name: idx_project_wiki_pages_content_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_wiki_pages_content_search ON public.project_wiki_pages USING gin (to_tsvector('simple'::regconfig, ((((COALESCE(title, ''::text) || ' '::text) || COALESCE(summary, ''::text)) || ' '::text) || COALESCE(markdown_content, ''::text))));


--
-- Name: idx_project_wiki_pages_kind_updated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_wiki_pages_kind_updated ON public.project_wiki_pages USING btree (project_id, memory_kind, updated_at DESC);


--
-- Name: idx_project_wiki_pages_project_updated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_wiki_pages_project_updated ON public.project_wiki_pages USING btree (project_id, updated_at DESC);


--
-- Name: idx_project_wiki_pages_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_wiki_pages_tags ON public.project_wiki_pages USING gin (tags);


--
-- Name: idx_project_wiki_pages_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_wiki_pages_type ON public.project_wiki_pages USING btree (project_id, page_type);


--
-- Name: idx_project_wiki_runs_project_started; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_wiki_runs_project_started ON public.project_wiki_compile_runs USING btree (project_id, started_at DESC);


--
-- Name: idx_project_wiki_sources_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_wiki_sources_source ON public.project_wiki_page_sources USING btree (source_type, source_id);


--
-- Name: idx_project_wiki_versions_page; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_wiki_versions_page ON public.project_wiki_page_versions USING btree (page_id, version DESC);


--
-- Name: idx_projects_department_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_department_id ON public.projects USING btree (department_id);


--
-- Name: idx_projects_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_id ON public.projects USING btree (id);


--
-- Name: idx_rag_v3_index_jobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rag_v3_index_jobs_status ON public.rag_v3_index_jobs USING btree (status, updated_at);


--
-- Name: idx_user_orgs_is_paid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_orgs_is_paid ON public.user_orgs USING btree (org_id, is_paid);


--
-- Name: idx_user_orgs_user_id_org_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_orgs_user_id_org_id ON public.user_orgs USING btree (user_id, org_id);


--
-- Name: idx_webhook_events_processed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_webhook_events_processed_at ON public.webhook_events USING btree (processed_at);


--
-- Name: idx_wiki_mcp_tokens_user_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_wiki_mcp_tokens_user_created ON public.wiki_mcp_tokens USING btree (user_id, created_at DESC);


--
-- Name: llm_credential_refs_visible_user_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX llm_credential_refs_visible_user_idx ON public.llm_credential_refs USING btree (user_id, created_at DESC) WHERE (hidden_at IS NULL);


--
-- Name: llm_key_operations_pending_user_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX llm_key_operations_pending_user_idx ON public.llm_key_operations USING btree (user_id) WHERE reserved_slot;


--
-- Name: llms_agent_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX llms_agent_id_idx ON public.llms USING btree (agent_id);


--
-- Name: llms_session_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX llms_session_id_idx ON public.llms USING btree (session_id);


--
-- Name: llms_thread_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX llms_thread_id_idx ON public.llms USING btree (thread_id);


--
-- Name: project_creation_requests_pending_name_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX project_creation_requests_pending_name_idx ON public.project_creation_requests USING btree (requester_id, org_id, lower(btrim(name))) WHERE (status = 'pending'::text);


--
-- Name: project_creation_requests_requester_created_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX project_creation_requests_requester_created_idx ON public.project_creation_requests USING btree (requester_id, created_at DESC);


--
-- Name: project_creation_requests_status_created_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX project_creation_requests_status_created_idx ON public.project_creation_requests USING btree (status, created_at DESC);


--
-- Name: project_department_migrations_active_project_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX project_department_migrations_active_project_idx ON public.project_department_migrations USING btree (project_id) WHERE (status = ANY (ARRAY['queued'::text, 'running'::text]));


--
-- Name: project_department_migrations_claim_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX project_department_migrations_claim_idx ON public.project_department_migrations USING btree (status, next_attempt_at, created_at);


--
-- Name: project_department_migrations_idempotency_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX project_department_migrations_idempotency_idx ON public.project_department_migrations USING btree (project_id, requested_by_user_id, idempotency_key) WHERE (idempotency_key IS NOT NULL);


--
-- Name: project_department_migrations_project_created_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX project_department_migrations_project_created_idx ON public.project_department_migrations USING btree (project_id, created_at DESC);


--
-- Name: project_department_migrations_task_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX project_department_migrations_task_id_idx ON public.project_department_migrations USING btree (task_id);


--
-- Name: project_memory_approval_jobs_draft_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX project_memory_approval_jobs_draft_idx ON public.project_memory_approval_jobs USING btree (draft_id, created_at DESC);


--
-- Name: project_memory_approval_jobs_pending_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX project_memory_approval_jobs_pending_idx ON public.project_memory_approval_jobs USING btree (status, next_attempt_at, created_at) WHERE (status = ANY (ARRAY['queued'::text, 'failed'::text]));


--
-- Name: projects_org_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX projects_org_id_idx ON public.projects USING btree (org_id);


--
-- Name: sessions_init_timestamp_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX sessions_init_timestamp_idx ON public.sessions USING btree (init_timestamp);


--
-- Name: sessions_project_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX sessions_project_id_idx ON public.sessions USING btree (project_id);


--
-- Name: sessions_project_id_secondary_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX sessions_project_id_secondary_idx ON public.sessions USING btree (project_id_secondary);


--
-- Name: spans_session_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX spans_session_id_idx ON public.spans USING btree (session_id);


--
-- Name: spans_span_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX spans_span_id_idx ON public.spans USING btree (span_id);


--
-- Name: spans_span_type_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX spans_span_type_idx ON public.spans USING btree (span_type);


--
-- Name: spans_trace_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX spans_trace_id_idx ON public.spans USING btree (trace_id);


--
-- Name: threads_agent_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX threads_agent_id_idx ON public.threads USING btree (agent_id);


--
-- Name: threads_session_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX threads_session_id_idx ON public.threads USING btree (session_id);


--
-- Name: tools_agent_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tools_agent_id_idx ON public.tools USING btree (agent_id);


--
-- Name: tools_session_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX tools_session_id_idx ON public.tools USING btree (session_id);


--
-- Name: ttd_session_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ttd_session_id_idx ON public.ttd USING btree (session_id);


--
-- Name: uq_ai_chat_message_sequence; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_ai_chat_message_sequence ON public.ai_chat_messages USING btree (session_id, sequence_index);


--
-- Name: uq_ai_chat_session_external; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_ai_chat_session_external ON public.ai_chat_sessions USING btree (project_id, source, employee_id, external_conversation_id) WHERE (external_conversation_id IS NOT NULL);


--
-- Name: uq_ai_gateway_key_requests_pending_user; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_ai_gateway_key_requests_pending_user ON public.ai_gateway_key_requests USING btree (user_id) WHERE (status = 'pending'::text);


--
-- Name: uq_ai_monitor_devices_identity; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_ai_monitor_devices_identity ON public.ai_monitor_devices USING btree (project_id, employee_id, device_id);


--
-- Name: uq_cc_switch_attribution_active_device; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_cc_switch_attribution_active_device ON public.cc_switch_attribution_sessions USING btree (device_id) WHERE ((device_id IS NOT NULL) AND (status = ANY (ARRAY['active'::text, 'finalizing'::text, 'pending_sync'::text])));


--
-- Name: uq_cc_switch_attribution_active_member; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_cc_switch_attribution_active_member ON public.cc_switch_attribution_sessions USING btree (target_user_id) WHERE (status = ANY (ARRAY['starting'::text, 'active'::text, 'finalizing'::text, 'pending_sync'::text]));


--
-- Name: uq_meeting_summaries_approval_draft; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_meeting_summaries_approval_draft ON public.meeting_summaries USING btree (approval_draft_id) WHERE (approval_draft_id IS NOT NULL);


--
-- Name: uq_project_conversation_submission; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_project_conversation_submission ON public.project_conversation_records USING btree (project_id, user_id, submission_id) WHERE (record_source = 'company_memory'::text);


--
-- Name: uq_project_material_intake_files_relative_path; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_project_material_intake_files_relative_path ON public.project_material_intake_files USING btree (intake_id, lower(relative_path));


--
-- Name: uq_project_material_intake_files_storage_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_project_material_intake_files_storage_key ON public.project_material_intake_files USING btree (storage_key) WHERE (storage_key IS NOT NULL);


--
-- Name: uq_project_material_intakes_client_upload; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_project_material_intakes_client_upload ON public.project_material_intakes USING btree (project_id, created_by_user_id, client_upload_id) WHERE (client_upload_id IS NOT NULL);


--
-- Name: uq_project_memory_drafts_intake; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_project_memory_drafts_intake ON public.project_memory_drafts USING btree (intake_id) WHERE (intake_id IS NOT NULL);


--
-- Name: uq_project_memory_drafts_submission; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_project_memory_drafts_submission ON public.project_memory_drafts USING btree (submission_id) WHERE (submission_id IS NOT NULL);


--
-- Name: uq_project_memory_pending_repository_url_submission; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_project_memory_pending_repository_url_submission ON public.project_memory_submissions USING btree (project_id, lower((payload ->> 'git_url'::text))) WHERE ((submission_type = 'project_repository'::text) AND (status = 'pending_review'::text));


--
-- Name: uq_project_repositories_project_url; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_project_repositories_project_url ON public.project_repositories USING btree (project_id, lower(git_url));


--
-- Name: user_orgs_org_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_orgs_org_id_idx ON public.user_orgs USING btree (org_id);


--
-- Name: user_orgs_user_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX user_orgs_user_id_idx ON public.user_orgs USING btree (user_id);


--
-- Name: users_active_display_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX users_active_display_idx ON public.users USING btree (is_active, nickname, email);


--
-- Name: ix_realtime_subscription_entity; Type: INDEX; Schema: realtime; Owner: -
--

CREATE INDEX ix_realtime_subscription_entity ON realtime.subscription USING btree (entity);


--
-- Name: messages_inserted_at_topic_index; Type: INDEX; Schema: realtime; Owner: -
--

CREATE INDEX messages_inserted_at_topic_index ON ONLY realtime.messages USING btree (inserted_at DESC, topic) WHERE ((extension = 'broadcast'::text) AND (private IS TRUE));


--
-- Name: messages_2026_07_14_inserted_at_topic_idx; Type: INDEX; Schema: realtime; Owner: -
--

CREATE INDEX messages_2026_07_14_inserted_at_topic_idx ON realtime.messages_2026_07_14 USING btree (inserted_at DESC, topic) WHERE ((extension = 'broadcast'::text) AND (private IS TRUE));


--
-- Name: messages_2026_07_15_inserted_at_topic_idx; Type: INDEX; Schema: realtime; Owner: -
--

CREATE INDEX messages_2026_07_15_inserted_at_topic_idx ON realtime.messages_2026_07_15 USING btree (inserted_at DESC, topic) WHERE ((extension = 'broadcast'::text) AND (private IS TRUE));


--
-- Name: messages_2026_07_16_inserted_at_topic_idx; Type: INDEX; Schema: realtime; Owner: -
--

CREATE INDEX messages_2026_07_16_inserted_at_topic_idx ON realtime.messages_2026_07_16 USING btree (inserted_at DESC, topic) WHERE ((extension = 'broadcast'::text) AND (private IS TRUE));


--
-- Name: messages_2026_07_17_inserted_at_topic_idx; Type: INDEX; Schema: realtime; Owner: -
--

CREATE INDEX messages_2026_07_17_inserted_at_topic_idx ON realtime.messages_2026_07_17 USING btree (inserted_at DESC, topic) WHERE ((extension = 'broadcast'::text) AND (private IS TRUE));


--
-- Name: messages_2026_07_18_inserted_at_topic_idx; Type: INDEX; Schema: realtime; Owner: -
--

CREATE INDEX messages_2026_07_18_inserted_at_topic_idx ON realtime.messages_2026_07_18 USING btree (inserted_at DESC, topic) WHERE ((extension = 'broadcast'::text) AND (private IS TRUE));


--
-- Name: subscription_subscription_id_entity_filters_action_filter_selec; Type: INDEX; Schema: realtime; Owner: -
--

CREATE UNIQUE INDEX subscription_subscription_id_entity_filters_action_filter_selec ON realtime.subscription USING btree (subscription_id, entity, filters, action_filter, COALESCE(selected_columns, '{}'::text[]));


--
-- Name: bname; Type: INDEX; Schema: storage; Owner: -
--

CREATE UNIQUE INDEX bname ON storage.buckets USING btree (name);


--
-- Name: bucketid_objname; Type: INDEX; Schema: storage; Owner: -
--

CREATE UNIQUE INDEX bucketid_objname ON storage.objects USING btree (bucket_id, name);


--
-- Name: buckets_analytics_unique_name_idx; Type: INDEX; Schema: storage; Owner: -
--

CREATE UNIQUE INDEX buckets_analytics_unique_name_idx ON storage.buckets_analytics USING btree (name) WHERE (deleted_at IS NULL);


--
-- Name: idx_iceberg_namespaces_bucket_id; Type: INDEX; Schema: storage; Owner: -
--

CREATE UNIQUE INDEX idx_iceberg_namespaces_bucket_id ON storage.iceberg_namespaces USING btree (catalog_id, name);


--
-- Name: idx_iceberg_tables_location; Type: INDEX; Schema: storage; Owner: -
--

CREATE UNIQUE INDEX idx_iceberg_tables_location ON storage.iceberg_tables USING btree (location);


--
-- Name: idx_iceberg_tables_namespace_id; Type: INDEX; Schema: storage; Owner: -
--

CREATE UNIQUE INDEX idx_iceberg_tables_namespace_id ON storage.iceberg_tables USING btree (catalog_id, namespace_id, name);


--
-- Name: idx_multipart_uploads_list; Type: INDEX; Schema: storage; Owner: -
--

CREATE INDEX idx_multipart_uploads_list ON storage.s3_multipart_uploads USING btree (bucket_id, key, created_at);


--
-- Name: idx_objects_bucket_id_name; Type: INDEX; Schema: storage; Owner: -
--

CREATE INDEX idx_objects_bucket_id_name ON storage.objects USING btree (bucket_id, name COLLATE "C");


--
-- Name: idx_objects_bucket_id_name_lower; Type: INDEX; Schema: storage; Owner: -
--

CREATE INDEX idx_objects_bucket_id_name_lower ON storage.objects USING btree (bucket_id, lower(name) COLLATE "C");


--
-- Name: name_prefix_search; Type: INDEX; Schema: storage; Owner: -
--

CREATE INDEX name_prefix_search ON storage.objects USING btree (name text_pattern_ops);


--
-- Name: vector_indexes_name_bucket_id_idx; Type: INDEX; Schema: storage; Owner: -
--

CREATE UNIQUE INDEX vector_indexes_name_bucket_id_idx ON storage.vector_indexes USING btree (name, bucket_id);


--
-- Name: supabase_functions_hooks_h_table_id_h_name_idx; Type: INDEX; Schema: supabase_functions; Owner: -
--

CREATE INDEX supabase_functions_hooks_h_table_id_h_name_idx ON supabase_functions.hooks USING btree (hook_table_id, hook_name);


--
-- Name: supabase_functions_hooks_request_id_idx; Type: INDEX; Schema: supabase_functions; Owner: -
--

CREATE INDEX supabase_functions_hooks_request_id_idx ON supabase_functions.hooks USING btree (request_id);


--
-- Name: messages_2026_07_14_inserted_at_topic_idx; Type: INDEX ATTACH; Schema: realtime; Owner: -
--

ALTER INDEX realtime.messages_inserted_at_topic_index ATTACH PARTITION realtime.messages_2026_07_14_inserted_at_topic_idx;


--
-- Name: messages_2026_07_14_pkey; Type: INDEX ATTACH; Schema: realtime; Owner: -
--

ALTER INDEX realtime.messages_pkey ATTACH PARTITION realtime.messages_2026_07_14_pkey;


--
-- Name: messages_2026_07_15_inserted_at_topic_idx; Type: INDEX ATTACH; Schema: realtime; Owner: -
--

ALTER INDEX realtime.messages_inserted_at_topic_index ATTACH PARTITION realtime.messages_2026_07_15_inserted_at_topic_idx;


--
-- Name: messages_2026_07_15_pkey; Type: INDEX ATTACH; Schema: realtime; Owner: -
--

ALTER INDEX realtime.messages_pkey ATTACH PARTITION realtime.messages_2026_07_15_pkey;


--
-- Name: messages_2026_07_16_inserted_at_topic_idx; Type: INDEX ATTACH; Schema: realtime; Owner: -
--

ALTER INDEX realtime.messages_inserted_at_topic_index ATTACH PARTITION realtime.messages_2026_07_16_inserted_at_topic_idx;


--
-- Name: messages_2026_07_16_pkey; Type: INDEX ATTACH; Schema: realtime; Owner: -
--

ALTER INDEX realtime.messages_pkey ATTACH PARTITION realtime.messages_2026_07_16_pkey;


--
-- Name: messages_2026_07_17_inserted_at_topic_idx; Type: INDEX ATTACH; Schema: realtime; Owner: -
--

ALTER INDEX realtime.messages_inserted_at_topic_index ATTACH PARTITION realtime.messages_2026_07_17_inserted_at_topic_idx;


--
-- Name: messages_2026_07_17_pkey; Type: INDEX ATTACH; Schema: realtime; Owner: -
--

ALTER INDEX realtime.messages_pkey ATTACH PARTITION realtime.messages_2026_07_17_pkey;


--
-- Name: messages_2026_07_18_inserted_at_topic_idx; Type: INDEX ATTACH; Schema: realtime; Owner: -
--

ALTER INDEX realtime.messages_inserted_at_topic_index ATTACH PARTITION realtime.messages_2026_07_18_inserted_at_topic_idx;


--
-- Name: messages_2026_07_18_pkey; Type: INDEX ATTACH; Schema: realtime; Owner: -
--

ALTER INDEX realtime.messages_pkey ATTACH PARTITION realtime.messages_2026_07_18_pkey;


--
-- Name: users on_new_user_add_to_shared_org; Type: TRIGGER; Schema: auth; Owner: -
--

CREATE TRIGGER on_new_user_add_to_shared_org AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION public.add_to_shared_org();


--
-- Name: users on_new_user_creation; Type: TRIGGER; Schema: auth; Owner: -
--

CREATE TRIGGER on_new_user_creation AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION public.setup_new_users();


--
-- Name: actions actions_insert_trigger; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER actions_insert_trigger BEFORE INSERT ON public.actions FOR EACH ROW EXECUTE FUNCTION public.add_default_agent_if_null();


--
-- Name: ai_gateway_key_projects ai_gateway_key_project_binding_guard; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER ai_gateway_key_project_binding_guard BEFORE INSERT OR DELETE OR UPDATE ON public.ai_gateway_key_projects FOR EACH ROW EXECUTE FUNCTION public.guard_gateway_key_project_binding();


--
-- Name: project_agents_files archive_project_agents_version; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER archive_project_agents_version AFTER INSERT OR UPDATE ON public.project_agents_files FOR EACH ROW EXECUTE FUNCTION public.archive_project_agents_version();


--
-- Name: departments departments_ensure_root_direct_child; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER departments_ensure_root_direct_child AFTER INSERT OR UPDATE OF parent_id ON public.departments FOR EACH ROW WHEN ((new.parent_id IS NULL)) EXECUTE FUNCTION public.ensure_root_direct_department();


--
-- Name: departments departments_protect_direct_category; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER departments_protect_direct_category BEFORE UPDATE ON public.departments FOR EACH ROW EXECUTE FUNCTION public.protect_direct_department();


--
-- Name: departments departments_protect_direct_category_delete; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER departments_protect_direct_category_delete BEFORE DELETE ON public.departments FOR EACH ROW EXECUTE FUNCTION public.protect_direct_department_delete();


--
-- Name: projects initialize_project_agents; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER initialize_project_agents AFTER INSERT ON public.projects FOR EACH ROW EXECUTE FUNCTION public.initialize_project_agents();


--
-- Name: llms llms_insert_trigger; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER llms_insert_trigger BEFORE INSERT ON public.llms FOR EACH ROW EXECUTE FUNCTION public.add_default_agent_if_null();


--
-- Name: threads threads_insert_trigger; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER threads_insert_trigger BEFORE INSERT ON public.threads FOR EACH ROW EXECUTE FUNCTION public.add_default_agent_if_null();


--
-- Name: tools tools_insert_trigger; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER tools_insert_trigger BEFORE INSERT ON public.tools FOR EACH ROW EXECUTE FUNCTION public.add_default_agent_if_null();


--
-- Name: documents trg_documents_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_documents_updated_at BEFORE UPDATE ON public.documents FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();


--
-- Name: subscription tr_check_filters; Type: TRIGGER; Schema: realtime; Owner: -
--

CREATE TRIGGER tr_check_filters BEFORE INSERT OR UPDATE ON realtime.subscription FOR EACH ROW EXECUTE FUNCTION realtime.subscription_check_filters();


--
-- Name: buckets enforce_bucket_name_length_trigger; Type: TRIGGER; Schema: storage; Owner: -
--

CREATE TRIGGER enforce_bucket_name_length_trigger BEFORE INSERT OR UPDATE OF name ON storage.buckets FOR EACH ROW EXECUTE FUNCTION storage.enforce_bucket_name_length();


--
-- Name: buckets protect_buckets_delete; Type: TRIGGER; Schema: storage; Owner: -
--

CREATE TRIGGER protect_buckets_delete BEFORE DELETE ON storage.buckets FOR EACH STATEMENT EXECUTE FUNCTION storage.protect_delete();


--
-- Name: objects protect_objects_delete; Type: TRIGGER; Schema: storage; Owner: -
--

CREATE TRIGGER protect_objects_delete BEFORE DELETE ON storage.objects FOR EACH STATEMENT EXECUTE FUNCTION storage.protect_delete();


--
-- Name: objects update_objects_updated_at; Type: TRIGGER; Schema: storage; Owner: -
--

CREATE TRIGGER update_objects_updated_at BEFORE UPDATE ON storage.objects FOR EACH ROW EXECUTE FUNCTION storage.update_updated_at_column();


--
-- Name: extensions extensions_tenant_external_id_fkey; Type: FK CONSTRAINT; Schema: _realtime; Owner: -
--

ALTER TABLE ONLY _realtime.extensions
    ADD CONSTRAINT extensions_tenant_external_id_fkey FOREIGN KEY (tenant_external_id) REFERENCES _realtime.tenants(external_id) ON DELETE CASCADE;


--
-- Name: identities identities_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.identities
    ADD CONSTRAINT identities_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: mfa_amr_claims mfa_amr_claims_session_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_amr_claims
    ADD CONSTRAINT mfa_amr_claims_session_id_fkey FOREIGN KEY (session_id) REFERENCES auth.sessions(id) ON DELETE CASCADE;


--
-- Name: mfa_challenges mfa_challenges_auth_factor_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_challenges
    ADD CONSTRAINT mfa_challenges_auth_factor_id_fkey FOREIGN KEY (factor_id) REFERENCES auth.mfa_factors(id) ON DELETE CASCADE;


--
-- Name: mfa_factors mfa_factors_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.mfa_factors
    ADD CONSTRAINT mfa_factors_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: oauth_authorizations oauth_authorizations_client_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_authorizations
    ADD CONSTRAINT oauth_authorizations_client_id_fkey FOREIGN KEY (client_id) REFERENCES auth.oauth_clients(id) ON DELETE CASCADE;


--
-- Name: oauth_authorizations oauth_authorizations_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_authorizations
    ADD CONSTRAINT oauth_authorizations_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: oauth_consents oauth_consents_client_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_consents
    ADD CONSTRAINT oauth_consents_client_id_fkey FOREIGN KEY (client_id) REFERENCES auth.oauth_clients(id) ON DELETE CASCADE;


--
-- Name: oauth_consents oauth_consents_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.oauth_consents
    ADD CONSTRAINT oauth_consents_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: one_time_tokens one_time_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.one_time_tokens
    ADD CONSTRAINT one_time_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: refresh_tokens refresh_tokens_session_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.refresh_tokens
    ADD CONSTRAINT refresh_tokens_session_id_fkey FOREIGN KEY (session_id) REFERENCES auth.sessions(id) ON DELETE CASCADE;


--
-- Name: saml_providers saml_providers_sso_provider_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_providers
    ADD CONSTRAINT saml_providers_sso_provider_id_fkey FOREIGN KEY (sso_provider_id) REFERENCES auth.sso_providers(id) ON DELETE CASCADE;


--
-- Name: saml_relay_states saml_relay_states_flow_state_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_relay_states
    ADD CONSTRAINT saml_relay_states_flow_state_id_fkey FOREIGN KEY (flow_state_id) REFERENCES auth.flow_state(id) ON DELETE CASCADE;


--
-- Name: saml_relay_states saml_relay_states_sso_provider_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.saml_relay_states
    ADD CONSTRAINT saml_relay_states_sso_provider_id_fkey FOREIGN KEY (sso_provider_id) REFERENCES auth.sso_providers(id) ON DELETE CASCADE;


--
-- Name: sessions sessions_oauth_client_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sessions
    ADD CONSTRAINT sessions_oauth_client_id_fkey FOREIGN KEY (oauth_client_id) REFERENCES auth.oauth_clients(id) ON DELETE CASCADE;


--
-- Name: sessions sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sessions
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: sso_domains sso_domains_sso_provider_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.sso_domains
    ADD CONSTRAINT sso_domains_sso_provider_id_fkey FOREIGN KEY (sso_provider_id) REFERENCES auth.sso_providers(id) ON DELETE CASCADE;


--
-- Name: webauthn_challenges webauthn_challenges_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.webauthn_challenges
    ADD CONSTRAINT webauthn_challenges_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: webauthn_credentials webauthn_credentials_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.webauthn_credentials
    ADD CONSTRAINT webauthn_credentials_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: deployments deployments_project_id_fkey; Type: FK CONSTRAINT; Schema: deploy; Owner: -
--

ALTER TABLE ONLY deploy.deployments
    ADD CONSTRAINT deployments_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: projects projects_id_fkey; Type: FK CONSTRAINT; Schema: deploy; Owner: -
--

ALTER TABLE ONLY deploy.projects
    ADD CONSTRAINT projects_id_fkey FOREIGN KEY (id) REFERENCES public.projects(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: actions actions_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: actions actions_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.actions
    ADD CONSTRAINT actions_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: agents agents_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT agents_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ai_gateway_admissions ai_gateway_admissions_key_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_admissions
    ADD CONSTRAINT ai_gateway_admissions_key_id_fkey FOREIGN KEY (key_id) REFERENCES public.ai_gateway_keys(id);


--
-- Name: ai_gateway_admissions ai_gateway_admissions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_admissions
    ADD CONSTRAINT ai_gateway_admissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: ai_gateway_events ai_gateway_events_chat_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_events
    ADD CONSTRAINT ai_gateway_events_chat_session_id_fkey FOREIGN KEY (chat_session_id) REFERENCES public.ai_chat_sessions(id) ON DELETE SET NULL;


--
-- Name: ai_gateway_events ai_gateway_events_key_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_events
    ADD CONSTRAINT ai_gateway_events_key_id_fkey FOREIGN KEY (key_id) REFERENCES public.ai_gateway_keys(id) ON DELETE SET NULL;


--
-- Name: ai_gateway_events ai_gateway_events_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_events
    ADD CONSTRAINT ai_gateway_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: ai_gateway_key_allowances ai_gateway_key_allowances_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_key_allowances
    ADD CONSTRAINT ai_gateway_key_allowances_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: ai_gateway_key_projects ai_gateway_key_projects_key_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_key_projects
    ADD CONSTRAINT ai_gateway_key_projects_key_id_fkey FOREIGN KEY (key_id) REFERENCES public.ai_gateway_keys(id) ON DELETE RESTRICT;


--
-- Name: ai_gateway_key_requests ai_gateway_key_requests_reviewed_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_key_requests
    ADD CONSTRAINT ai_gateway_key_requests_reviewed_by_user_id_fkey FOREIGN KEY (reviewed_by_user_id) REFERENCES public.users(id);


--
-- Name: ai_gateway_key_requests ai_gateway_key_requests_reviewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_key_requests
    ADD CONSTRAINT ai_gateway_key_requests_reviewer_id_fkey FOREIGN KEY (reviewer_id) REFERENCES public.users(id);


--
-- Name: ai_gateway_key_requests ai_gateway_key_requests_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_key_requests
    ADD CONSTRAINT ai_gateway_key_requests_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: ai_gateway_keys ai_gateway_keys_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_gateway_keys
    ADD CONSTRAINT ai_gateway_keys_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: billing_audit_logs billing_audit_logs_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.billing_audit_logs
    ADD CONSTRAINT billing_audit_logs_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.orgs(id);


--
-- Name: billing_audit_logs billing_audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.billing_audit_logs
    ADD CONSTRAINT billing_audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id);


--
-- Name: billing_periods billing_periods_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.billing_periods
    ADD CONSTRAINT billing_periods_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.orgs(id) ON DELETE CASCADE;


--
-- Name: cc_switch_attributed_requests cc_switch_attributed_requests_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_attributed_requests
    ADD CONSTRAINT cc_switch_attributed_requests_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: cc_switch_attributed_requests cc_switch_attributed_requests_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_attributed_requests
    ADD CONSTRAINT cc_switch_attributed_requests_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.cc_switch_attribution_sessions(id) ON DELETE CASCADE;


--
-- Name: cc_switch_attributed_requests cc_switch_attributed_requests_target_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_attributed_requests
    ADD CONSTRAINT cc_switch_attributed_requests_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: cc_switch_attribution_sessions cc_switch_attribution_sessions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_attribution_sessions
    ADD CONSTRAINT cc_switch_attribution_sessions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: cc_switch_attribution_sessions cc_switch_attribution_sessions_target_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_attribution_sessions
    ADD CONSTRAINT cc_switch_attribution_sessions_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: cc_switch_temporary_monitor_probes cc_switch_temporary_monitor_probes_target_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_temporary_monitor_probes
    ADD CONSTRAINT cc_switch_temporary_monitor_probes_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: cc_switch_usage_daily cc_switch_usage_daily_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_usage_daily
    ADD CONSTRAINT cc_switch_usage_daily_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: cc_switch_usage_daily cc_switch_usage_daily_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_usage_daily
    ADD CONSTRAINT cc_switch_usage_daily_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: cc_switch_usage_sync_status cc_switch_usage_sync_status_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_usage_sync_status
    ADD CONSTRAINT cc_switch_usage_sync_status_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: cc_switch_usage_sync_status cc_switch_usage_sync_status_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cc_switch_usage_sync_status
    ADD CONSTRAINT cc_switch_usage_sync_status_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: customers customers_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id);


--
-- Name: departments departments_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: departments departments_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.departments(id) ON DELETE CASCADE;


--
-- Name: document_chunks document_chunks_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: document_chunks document_chunks_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: document_chunks_v2 document_chunks_v2_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks_v2
    ADD CONSTRAINT document_chunks_v2_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: document_chunks_v2 document_chunks_v2_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks_v2
    ADD CONSTRAINT document_chunks_v2_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: document_chunks_v3_shadow document_chunks_v3_shadow_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_chunks_v3_shadow
    ADD CONSTRAINT document_chunks_v3_shadow_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: documents documents_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: documents documents_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: documents documents_memory_draft_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_memory_draft_id_fkey FOREIGN KEY (memory_draft_id) REFERENCES public.project_memory_drafts(id) ON DELETE SET NULL;


--
-- Name: documents documents_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: errors errors_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.errors
    ADD CONSTRAINT errors_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: llm_credential_refs llm_credential_refs_creation_operation_id_user_id_instance_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_credential_refs
    ADD CONSTRAINT llm_credential_refs_creation_operation_id_user_id_instance_fkey FOREIGN KEY (creation_operation_id, user_id, instance_id) REFERENCES public.llm_key_operations(id, user_id, instance_id);


--
-- Name: llm_credential_refs llm_credential_refs_instance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_credential_refs
    ADD CONSTRAINT llm_credential_refs_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES public.llm_gateway_instances(id);


--
-- Name: llm_credential_refs llm_credential_refs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_credential_refs
    ADD CONSTRAINT llm_credential_refs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: llm_key_operations llm_key_operations_instance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_key_operations
    ADD CONSTRAINT llm_key_operations_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES public.llm_gateway_instances(id);


--
-- Name: llm_key_operations llm_key_operations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_key_operations
    ADD CONSTRAINT llm_key_operations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: llm_member_rollout llm_member_rollout_instance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_member_rollout
    ADD CONSTRAINT llm_member_rollout_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES public.llm_gateway_instances(id);


--
-- Name: llm_member_rollout llm_member_rollout_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llm_member_rollout
    ADD CONSTRAINT llm_member_rollout_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: llms llms_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.llms
    ADD CONSTRAINT llms_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: meeting_summaries meeting_summaries_approval_draft_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meeting_summaries
    ADD CONSTRAINT meeting_summaries_approval_draft_id_fkey FOREIGN KEY (approval_draft_id) REFERENCES public.project_memory_drafts(id) ON DELETE SET NULL;


--
-- Name: meeting_summaries meeting_summaries_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meeting_summaries
    ADD CONSTRAINT meeting_summaries_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: meeting_summary_files meeting_summary_files_meeting_summary_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.meeting_summary_files
    ADD CONSTRAINT meeting_summary_files_meeting_summary_id_fkey FOREIGN KEY (meeting_summary_id) REFERENCES public.meeting_summaries(id) ON DELETE CASCADE;


--
-- Name: member_wiki_experience_sources member_wiki_experience_sources_experience_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_wiki_experience_sources
    ADD CONSTRAINT member_wiki_experience_sources_experience_id_fkey FOREIGN KEY (experience_id) REFERENCES public.member_wiki_experiences(id) ON DELETE CASCADE;


--
-- Name: member_wiki_experience_versions member_wiki_experience_versions_experience_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_wiki_experience_versions
    ADD CONSTRAINT member_wiki_experience_versions_experience_id_fkey FOREIGN KEY (experience_id) REFERENCES public.member_wiki_experiences(id) ON DELETE CASCADE;


--
-- Name: member_wiki_experience_versions member_wiki_experience_versions_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_wiki_experience_versions
    ADD CONSTRAINT member_wiki_experience_versions_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.member_wiki_runs(id) ON DELETE SET NULL;


--
-- Name: member_wiki_processed_sessions member_wiki_processed_sessions_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_wiki_processed_sessions
    ADD CONSTRAINT member_wiki_processed_sessions_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.member_wiki_runs(id) ON DELETE SET NULL;


--
-- Name: org_invites org_invites_inviter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_invites
    ADD CONSTRAINT org_invites_inviter_id_fkey FOREIGN KEY (inviter_id) REFERENCES auth.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: org_invites org_invites_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.org_invites
    ADD CONSTRAINT org_invites_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.orgs(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: prices prices_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prices
    ADD CONSTRAINT prices_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: project_agents_file_versions project_agents_file_versions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_agents_file_versions
    ADD CONSTRAINT project_agents_file_versions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_agents_file_versions project_agents_file_versions_updated_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_agents_file_versions
    ADD CONSTRAINT project_agents_file_versions_updated_by_user_id_fkey FOREIGN KEY (updated_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: project_agents_files project_agents_files_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_agents_files
    ADD CONSTRAINT project_agents_files_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_agents_files project_agents_files_updated_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_agents_files
    ADD CONSTRAINT project_agents_files_updated_by_user_id_fkey FOREIGN KEY (updated_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: project_context_tokens project_context_tokens_key_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_context_tokens
    ADD CONSTRAINT project_context_tokens_key_id_fkey FOREIGN KEY (key_id) REFERENCES public.ai_gateway_keys(id) ON DELETE CASCADE;


--
-- Name: project_context_tokens project_context_tokens_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_context_tokens
    ADD CONSTRAINT project_context_tokens_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_context_tokens project_context_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_context_tokens
    ADD CONSTRAINT project_context_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: project_conversation_record_attempts project_conversation_record_attempts_record_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_conversation_record_attempts
    ADD CONSTRAINT project_conversation_record_attempts_record_id_fkey FOREIGN KEY (record_id) REFERENCES public.project_conversation_records(id) ON DELETE CASCADE;


--
-- Name: project_conversation_records project_conversation_records_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_conversation_records
    ADD CONSTRAINT project_conversation_records_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_conversation_records project_conversation_records_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_conversation_records
    ADD CONSTRAINT project_conversation_records_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: project_conversation_records project_conversation_records_wiki_page_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_conversation_records
    ADD CONSTRAINT project_conversation_records_wiki_page_id_fkey FOREIGN KEY (wiki_page_id) REFERENCES public.project_wiki_pages(id) ON DELETE SET NULL;


--
-- Name: project_creation_requests project_creation_requests_created_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_creation_requests
    ADD CONSTRAINT project_creation_requests_created_project_id_fkey FOREIGN KEY (created_project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: project_creation_requests project_creation_requests_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_creation_requests
    ADD CONSTRAINT project_creation_requests_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: project_creation_requests project_creation_requests_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_creation_requests
    ADD CONSTRAINT project_creation_requests_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.orgs(id) ON DELETE CASCADE;


--
-- Name: project_creation_requests project_creation_requests_requester_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_creation_requests
    ADD CONSTRAINT project_creation_requests_requester_id_fkey FOREIGN KEY (requester_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: project_creation_requests project_creation_requests_reviewed_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_creation_requests
    ADD CONSTRAINT project_creation_requests_reviewed_by_user_id_fkey FOREIGN KEY (reviewed_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: project_department_migrations project_department_migrations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_department_migrations
    ADD CONSTRAINT project_department_migrations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_department_migrations project_department_migrations_requested_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_department_migrations
    ADD CONSTRAINT project_department_migrations_requested_by_user_id_fkey FOREIGN KEY (requested_by_user_id) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: project_department_migrations project_department_migrations_source_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_department_migrations
    ADD CONSTRAINT project_department_migrations_source_department_id_fkey FOREIGN KEY (source_department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: project_department_migrations project_department_migrations_target_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_department_migrations
    ADD CONSTRAINT project_department_migrations_target_department_id_fkey FOREIGN KEY (target_department_id) REFERENCES public.departments(id) ON DELETE SET NULL;


--
-- Name: project_material_documents project_material_documents_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_material_documents
    ADD CONSTRAINT project_material_documents_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: project_material_documents project_material_documents_draft_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_material_documents
    ADD CONSTRAINT project_material_documents_draft_id_fkey FOREIGN KEY (draft_id) REFERENCES public.project_memory_drafts(id) ON DELETE SET NULL;


--
-- Name: project_material_documents project_material_documents_original_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_material_documents
    ADD CONSTRAINT project_material_documents_original_file_id_fkey FOREIGN KEY (original_file_id) REFERENCES public.project_material_intake_files(id) ON DELETE SET NULL;


--
-- Name: project_material_documents project_material_documents_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_material_documents
    ADD CONSTRAINT project_material_documents_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_material_intake_files project_material_intake_files_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_material_intake_files
    ADD CONSTRAINT project_material_intake_files_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE SET NULL;


--
-- Name: project_material_intake_files project_material_intake_files_intake_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_material_intake_files
    ADD CONSTRAINT project_material_intake_files_intake_id_fkey FOREIGN KEY (intake_id) REFERENCES public.project_material_intakes(id) ON DELETE CASCADE;


--
-- Name: project_material_intakes project_material_intakes_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_material_intakes
    ADD CONSTRAINT project_material_intakes_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: project_material_intakes project_material_intakes_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_material_intakes
    ADD CONSTRAINT project_material_intakes_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_material_parse_jobs project_material_parse_jobs_intake_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_material_parse_jobs
    ADD CONSTRAINT project_material_parse_jobs_intake_file_id_fkey FOREIGN KEY (intake_file_id) REFERENCES public.project_material_intake_files(id) ON DELETE CASCADE;


--
-- Name: project_material_parse_jobs project_material_parse_jobs_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_material_parse_jobs
    ADD CONSTRAINT project_material_parse_jobs_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_members project_members_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_members project_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: project_memory_approval_jobs project_memory_approval_jobs_draft_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_memory_approval_jobs
    ADD CONSTRAINT project_memory_approval_jobs_draft_id_fkey FOREIGN KEY (draft_id) REFERENCES public.project_memory_drafts(id) ON DELETE CASCADE;


--
-- Name: project_memory_draft_sources project_memory_draft_sources_draft_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_memory_draft_sources
    ADD CONSTRAINT project_memory_draft_sources_draft_id_fkey FOREIGN KEY (draft_id) REFERENCES public.project_memory_drafts(id) ON DELETE CASCADE;


--
-- Name: project_memory_drafts project_memory_drafts_approved_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_memory_drafts
    ADD CONSTRAINT project_memory_drafts_approved_document_id_fkey FOREIGN KEY (approved_document_id) REFERENCES public.documents(id) ON DELETE SET NULL;


--
-- Name: project_memory_drafts project_memory_drafts_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_memory_drafts
    ADD CONSTRAINT project_memory_drafts_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: project_memory_drafts project_memory_drafts_intake_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_memory_drafts
    ADD CONSTRAINT project_memory_drafts_intake_id_fkey FOREIGN KEY (intake_id) REFERENCES public.project_material_intakes(id) ON DELETE SET NULL;


--
-- Name: project_memory_drafts project_memory_drafts_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_memory_drafts
    ADD CONSTRAINT project_memory_drafts_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_memory_drafts project_memory_drafts_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_memory_drafts
    ADD CONSTRAINT project_memory_drafts_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.project_memory_submissions(id) ON DELETE SET NULL;


--
-- Name: project_memory_reviews project_memory_reviews_draft_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_memory_reviews
    ADD CONSTRAINT project_memory_reviews_draft_id_fkey FOREIGN KEY (draft_id) REFERENCES public.project_memory_drafts(id) ON DELETE CASCADE;


--
-- Name: project_memory_submissions project_memory_submissions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_memory_submissions
    ADD CONSTRAINT project_memory_submissions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_repositories project_repositories_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_repositories
    ADD CONSTRAINT project_repositories_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_wiki_changes project_wiki_changes_page_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_changes
    ADD CONSTRAINT project_wiki_changes_page_id_fkey FOREIGN KEY (page_id) REFERENCES public.project_wiki_pages(id) ON DELETE SET NULL;


--
-- Name: project_wiki_changes project_wiki_changes_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_changes
    ADD CONSTRAINT project_wiki_changes_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_wiki_changes project_wiki_changes_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_changes
    ADD CONSTRAINT project_wiki_changes_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.project_wiki_compile_runs(id) ON DELETE CASCADE;


--
-- Name: project_wiki_compile_runs project_wiki_compile_runs_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_compile_runs
    ADD CONSTRAINT project_wiki_compile_runs_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_wiki_links project_wiki_links_from_page_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_links
    ADD CONSTRAINT project_wiki_links_from_page_id_fkey FOREIGN KEY (from_page_id) REFERENCES public.project_wiki_pages(id) ON DELETE CASCADE;


--
-- Name: project_wiki_links project_wiki_links_to_page_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_links
    ADD CONSTRAINT project_wiki_links_to_page_id_fkey FOREIGN KEY (to_page_id) REFERENCES public.project_wiki_pages(id) ON DELETE CASCADE;


--
-- Name: project_wiki_page_sources project_wiki_page_sources_page_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_page_sources
    ADD CONSTRAINT project_wiki_page_sources_page_id_fkey FOREIGN KEY (page_id) REFERENCES public.project_wiki_pages(id) ON DELETE CASCADE;


--
-- Name: project_wiki_page_versions project_wiki_page_versions_page_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_page_versions
    ADD CONSTRAINT project_wiki_page_versions_page_id_fkey FOREIGN KEY (page_id) REFERENCES public.project_wiki_pages(id) ON DELETE CASCADE;


--
-- Name: project_wiki_pages project_wiki_pages_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_pages
    ADD CONSTRAINT project_wiki_pages_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE SET NULL;


--
-- Name: project_wiki_pages project_wiki_pages_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_pages
    ADD CONSTRAINT project_wiki_pages_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_wiki_processed_sources project_wiki_processed_sources_last_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_processed_sources
    ADD CONSTRAINT project_wiki_processed_sources_last_run_id_fkey FOREIGN KEY (last_run_id) REFERENCES public.project_wiki_compile_runs(id) ON DELETE SET NULL;


--
-- Name: project_wiki_processed_sources project_wiki_processed_sources_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_wiki_processed_sources
    ADD CONSTRAINT project_wiki_processed_sources_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: projects projects_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(id);


--
-- Name: projects projects_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.orgs(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sessions sessions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sessions sessions_project_id_secondary_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_project_id_secondary_fkey FOREIGN KEY (project_id_secondary) REFERENCES public.projects(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: spans spans_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.spans
    ADD CONSTRAINT spans_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: stats stats_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stats
    ADD CONSTRAINT stats_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: subscriptions subscriptions_price_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_price_id_fkey FOREIGN KEY (price_id) REFERENCES public.prices(id);


--
-- Name: subscriptions subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id);


--
-- Name: threads threads_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.threads
    ADD CONSTRAINT threads_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: threads threads_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.threads
    ADD CONSTRAINT threads_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: tools tools_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tools
    ADD CONSTRAINT tools_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: tools tools_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tools
    ADD CONSTRAINT tools_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ttd ttd_llm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ttd
    ADD CONSTRAINT ttd_llm_id_fkey FOREIGN KEY (llm_id) REFERENCES public.llms(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: ttd ttd_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ttd
    ADD CONSTRAINT ttd_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: user_orgs user_orgs_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_orgs
    ADD CONSTRAINT user_orgs_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.orgs(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: user_orgs user_orgs_users_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_orgs
    ADD CONSTRAINT user_orgs_users_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: users users_deactivated_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_deactivated_by_user_id_fkey FOREIGN KEY (deactivated_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: users users_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: iceberg_namespaces iceberg_namespaces_catalog_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.iceberg_namespaces
    ADD CONSTRAINT iceberg_namespaces_catalog_id_fkey FOREIGN KEY (catalog_id) REFERENCES storage.buckets_analytics(id) ON DELETE CASCADE;


--
-- Name: iceberg_tables iceberg_tables_catalog_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.iceberg_tables
    ADD CONSTRAINT iceberg_tables_catalog_id_fkey FOREIGN KEY (catalog_id) REFERENCES storage.buckets_analytics(id) ON DELETE CASCADE;


--
-- Name: iceberg_tables iceberg_tables_namespace_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.iceberg_tables
    ADD CONSTRAINT iceberg_tables_namespace_id_fkey FOREIGN KEY (namespace_id) REFERENCES storage.iceberg_namespaces(id) ON DELETE CASCADE;


--
-- Name: objects objects_bucketId_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.objects
    ADD CONSTRAINT "objects_bucketId_fkey" FOREIGN KEY (bucket_id) REFERENCES storage.buckets(id);


--
-- Name: s3_multipart_uploads s3_multipart_uploads_bucket_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.s3_multipart_uploads
    ADD CONSTRAINT s3_multipart_uploads_bucket_id_fkey FOREIGN KEY (bucket_id) REFERENCES storage.buckets(id);


--
-- Name: s3_multipart_uploads_parts s3_multipart_uploads_parts_bucket_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.s3_multipart_uploads_parts
    ADD CONSTRAINT s3_multipart_uploads_parts_bucket_id_fkey FOREIGN KEY (bucket_id) REFERENCES storage.buckets(id);


--
-- Name: s3_multipart_uploads_parts s3_multipart_uploads_parts_upload_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.s3_multipart_uploads_parts
    ADD CONSTRAINT s3_multipart_uploads_parts_upload_id_fkey FOREIGN KEY (upload_id) REFERENCES storage.s3_multipart_uploads(id) ON DELETE CASCADE;


--
-- Name: vector_indexes vector_indexes_bucket_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: -
--

ALTER TABLE ONLY storage.vector_indexes
    ADD CONSTRAINT vector_indexes_bucket_id_fkey FOREIGN KEY (bucket_id) REFERENCES storage.buckets_vectors(id);


--
-- Name: audit_log_entries; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.audit_log_entries ENABLE ROW LEVEL SECURITY;

--
-- Name: flow_state; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.flow_state ENABLE ROW LEVEL SECURITY;

--
-- Name: identities; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.identities ENABLE ROW LEVEL SECURITY;

--
-- Name: instances; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.instances ENABLE ROW LEVEL SECURITY;

--
-- Name: mfa_amr_claims; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.mfa_amr_claims ENABLE ROW LEVEL SECURITY;

--
-- Name: mfa_challenges; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.mfa_challenges ENABLE ROW LEVEL SECURITY;

--
-- Name: mfa_factors; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.mfa_factors ENABLE ROW LEVEL SECURITY;

--
-- Name: one_time_tokens; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.one_time_tokens ENABLE ROW LEVEL SECURITY;

--
-- Name: refresh_tokens; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.refresh_tokens ENABLE ROW LEVEL SECURITY;

--
-- Name: saml_providers; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.saml_providers ENABLE ROW LEVEL SECURITY;

--
-- Name: saml_relay_states; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.saml_relay_states ENABLE ROW LEVEL SECURITY;

--
-- Name: schema_migrations; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.schema_migrations ENABLE ROW LEVEL SECURITY;

--
-- Name: sessions; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.sessions ENABLE ROW LEVEL SECURITY;

--
-- Name: sso_domains; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.sso_domains ENABLE ROW LEVEL SECURITY;

--
-- Name: sso_providers; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.sso_providers ENABLE ROW LEVEL SECURITY;

--
-- Name: users; Type: ROW SECURITY; Schema: auth; Owner: -
--

ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

--
-- Name: actions MFA for actions; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "MFA for actions" ON public.actions AS RESTRICTIVE TO authenticated USING ((ARRAY[(( SELECT auth.jwt() AS jwt) ->> 'aal'::text)] <@ public.user_aal()));


--
-- Name: agents MFA for agents; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "MFA for agents" ON public.agents AS RESTRICTIVE TO authenticated USING ((ARRAY[(( SELECT auth.jwt() AS jwt) ->> 'aal'::text)] <@ public.user_aal()));


--
-- Name: errors MFA for errors; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "MFA for errors" ON public.errors AS RESTRICTIVE TO authenticated USING ((ARRAY[(( SELECT auth.jwt() AS jwt) ->> 'aal'::text)] <@ public.user_aal()));


--
-- Name: llms MFA for llms; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "MFA for llms" ON public.llms AS RESTRICTIVE TO authenticated USING ((ARRAY[(( SELECT auth.jwt() AS jwt) ->> 'aal'::text)] <@ public.user_aal()));


--
-- Name: orgs MFA for orgs; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "MFA for orgs" ON public.orgs AS RESTRICTIVE TO authenticated USING ((ARRAY[(( SELECT auth.jwt() AS jwt) ->> 'aal'::text)] <@ public.user_aal()));


--
-- Name: projects MFA for projects; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "MFA for projects" ON public.projects AS RESTRICTIVE TO authenticated USING ((ARRAY[(( SELECT auth.jwt() AS jwt) ->> 'aal'::text)] <@ public.user_aal()));


--
-- Name: sessions MFA for sessions; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "MFA for sessions" ON public.sessions AS RESTRICTIVE TO authenticated USING ((ARRAY[(( SELECT auth.jwt() AS jwt) ->> 'aal'::text)] <@ public.user_aal()));


--
-- Name: stats MFA for stats; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "MFA for stats" ON public.stats AS RESTRICTIVE TO authenticated USING ((ARRAY[(( SELECT auth.jwt() AS jwt) ->> 'aal'::text)] <@ public.user_aal()));


--
-- Name: threads MFA for threads; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "MFA for threads" ON public.threads AS RESTRICTIVE TO authenticated USING ((ARRAY[(( SELECT auth.jwt() AS jwt) ->> 'aal'::text)] <@ public.user_aal()));


--
-- Name: tools MFA for tools; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "MFA for tools" ON public.tools AS RESTRICTIVE TO authenticated USING ((ARRAY[(( SELECT auth.jwt() AS jwt) ->> 'aal'::text)] <@ public.user_aal()));


--
-- Name: ttd MFA for ttd; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "MFA for ttd" ON public.ttd AS RESTRICTIVE TO authenticated USING ((ARRAY[( SELECT (auth.jwt() ->> 'aal'::text))] <@ public.user_aal()));


--
-- Name: user_orgs MFA for user_orgs; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "MFA for user_orgs" ON public.user_orgs AS RESTRICTIVE TO authenticated USING ((ARRAY[(( SELECT auth.jwt() AS jwt) ->> 'aal'::text)] <@ public.user_aal()));


--
-- Name: users MFA for users; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "MFA for users" ON public.users AS RESTRICTIVE TO authenticated USING ((ARRAY[(( SELECT auth.jwt() AS jwt) ->> 'aal'::text)] <@ public.user_aal()));


--
-- Name: org_invites Org admins can delete org invites; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Org admins can delete org invites" ON public.org_invites FOR DELETE TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.user_orgs
  WHERE ((user_orgs.org_id = org_invites.org_id) AND (user_orgs.user_id = auth.uid()) AND (user_orgs.role = ANY (ARRAY['admin'::public.org_roles, 'owner'::public.org_roles]))))));


--
-- Name: billing_audit_logs Org admins can view billing audit logs; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Org admins can view billing audit logs" ON public.billing_audit_logs FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.user_orgs
  WHERE ((user_orgs.org_id = billing_audit_logs.org_id) AND (user_orgs.user_id = auth.uid()) AND (user_orgs.role = ANY (ARRAY['admin'::public.org_roles, 'owner'::public.org_roles]))))));


--
-- Name: org_invites Org members can see org invites; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Org members can see org invites" ON public.org_invites FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.user_orgs
  WHERE ((user_orgs.org_id = org_invites.org_id) AND (user_orgs.user_id = auth.uid()) AND (user_orgs.role = ANY (ARRAY['admin'::public.org_roles, 'owner'::public.org_roles]))))));


--
-- Name: billing_periods Org members can view billing periods; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Org members can view billing periods" ON public.billing_periods FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.user_orgs uo
  WHERE ((uo.org_id = billing_periods.org_id) AND (uo.user_id = auth.uid())))));


--
-- Name: user_orgs Owners and Admins can remove users in their orgs; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Owners and Admins can remove users in their orgs" ON public.user_orgs FOR DELETE TO authenticated USING ((public.user_is_org_admin(org_id) AND (role <> 'owner'::public.org_roles)));


--
-- Name: user_orgs Owners and Admins can update users in their orgs; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Owners and Admins can update users in their orgs" ON public.user_orgs FOR UPDATE TO authenticated USING ((public.user_is_org_admin(org_id) AND (EXISTS ( SELECT 1
   FROM public.orgs
  WHERE ((orgs.id = user_orgs.org_id) AND (orgs.prem_status = ANY (ARRAY['pro'::public.prem_status, 'enterprise'::public.prem_status]))))) AND (user_id <> ( SELECT auth.uid() AS uid)) AND (role <> 'owner'::public.org_roles))) WITH CHECK ((public.user_is_org_admin(org_id) AND (EXISTS ( SELECT 1
   FROM public.orgs
  WHERE ((orgs.id = user_orgs.org_id) AND (orgs.prem_status = ANY (ARRAY['pro'::public.prem_status, 'enterprise'::public.prem_status]))))) AND (user_id <> ( SELECT auth.uid() AS uid)) AND (role <> 'owner'::public.org_roles)));


--
-- Name: orgs Owners can delete orgs; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Owners can delete orgs" ON public.orgs FOR DELETE TO authenticated USING (public.user_is_org_owner(id));


--
-- Name: ttd Users can CRUD ttd through org membership; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can CRUD ttd through org membership" ON public.ttd TO authenticated USING ((( SELECT auth.uid() AS uid) IN ( SELECT user_orgs.user_id
   FROM ((public.user_orgs
     JOIN public.projects ON ((user_orgs.org_id = projects.org_id)))
     JOIN public.sessions ON (((projects.id = sessions.project_id) OR (projects.id = sessions.project_id_secondary))))
  WHERE (sessions.id = ttd.session_id)))) WITH CHECK ((( SELECT auth.uid() AS uid) IN ( SELECT user_orgs.user_id
   FROM ((public.user_orgs
     JOIN public.projects ON ((user_orgs.org_id = projects.org_id)))
     JOIN public.sessions ON (((projects.id = sessions.project_id) OR (projects.id = sessions.project_id_secondary))))
  WHERE (sessions.id = ttd.session_id))));


--
-- Name: sessions Users can delete sessions through org membership; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can delete sessions through org membership" ON public.sessions FOR DELETE USING (((project_id IN ( SELECT public.user_projects() AS user_projects)) OR (project_id_secondary IN ( SELECT public.user_projects() AS user_projects))));


--
-- Name: users Users can edit their own row in users; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can edit their own row in users" ON public.users FOR UPDATE TO authenticated USING ((id = ( SELECT auth.uid() AS uid))) WITH CHECK ((id = ( SELECT auth.uid() AS uid)));


--
-- Name: user_orgs Users can leave orgs; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can leave orgs" ON public.user_orgs FOR DELETE TO authenticated USING (((user_id = ( SELECT auth.uid() AS uid)) AND (NOT public.user_is_org_owner(org_id))));


--
-- Name: projects Users can perform CRUD on projects through org membership; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can perform CRUD on projects through org membership" ON public.projects TO authenticated USING ((( SELECT auth.uid() AS uid) IN ( SELECT user_orgs.user_id
   FROM public.user_orgs
  WHERE (user_orgs.org_id = projects.org_id)))) WITH CHECK ((( SELECT auth.uid() AS uid) IN ( SELECT user_orgs.user_id
   FROM public.user_orgs
  WHERE (user_orgs.org_id = projects.org_id))));


--
-- Name: user_orgs Users can see all users in their orgs; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can see all users in their orgs" ON public.user_orgs FOR SELECT TO authenticated USING (public.user_belongs_to_org(org_id));


--
-- Name: org_invites Users can see invitations sent to them; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can see invitations sent to them" ON public.org_invites FOR SELECT TO authenticated USING ((invitee_email IN ( SELECT users.email
   FROM auth.users
  WHERE (users.id = auth.uid())
UNION
 SELECT users.email
   FROM public.users
  WHERE (users.id = auth.uid()))));


--
-- Name: org_invites Users can send invites for their orgs; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can send invites for their orgs" ON public.org_invites FOR INSERT TO authenticated WITH CHECK (((inviter_id = auth.uid()) AND (EXISTS ( SELECT 1
   FROM public.user_orgs
  WHERE ((user_orgs.org_id = org_invites.org_id) AND (user_orgs.user_id = auth.uid()))))));


--
-- Name: actions Users can view actions through org membership; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view actions through org membership" ON public.actions FOR SELECT TO authenticated USING ((( SELECT auth.uid() AS uid) IN ( SELECT user_orgs.user_id
   FROM ((public.user_orgs
     JOIN public.projects ON ((user_orgs.org_id = projects.org_id)))
     JOIN public.sessions ON (((projects.id = sessions.project_id) OR (projects.id = sessions.project_id_secondary))))
  WHERE (sessions.id = actions.session_id))));


--
-- Name: agents Users can view agents through org membership; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view agents through org membership" ON public.agents FOR SELECT TO authenticated USING ((( SELECT auth.uid() AS uid) IN ( SELECT user_orgs.user_id
   FROM ((public.user_orgs
     JOIN public.projects ON ((user_orgs.org_id = projects.org_id)))
     JOIN public.sessions ON (((projects.id = sessions.project_id) OR (projects.id = sessions.project_id_secondary))))
  WHERE (sessions.id = agents.session_id))));


--
-- Name: errors Users can view errors through org membership; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view errors through org membership" ON public.errors FOR SELECT TO authenticated USING ((( SELECT auth.uid() AS uid) IN ( SELECT user_orgs.user_id
   FROM ((public.user_orgs
     JOIN public.projects ON ((user_orgs.org_id = projects.org_id)))
     JOIN public.sessions ON (((projects.id = sessions.project_id) OR (projects.id = sessions.project_id_secondary))))
  WHERE (sessions.id = errors.session_id))));


--
-- Name: llms Users can view llms through org membership; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view llms through org membership" ON public.llms FOR SELECT TO authenticated USING ((( SELECT auth.uid() AS uid) IN ( SELECT user_orgs.user_id
   FROM ((public.user_orgs
     JOIN public.projects ON ((user_orgs.org_id = projects.org_id)))
     JOIN public.sessions ON (((projects.id = sessions.project_id) OR (projects.id = sessions.project_id_secondary))))
  WHERE (sessions.id = llms.session_id))));


--
-- Name: orgs Users can view orgs through org membership; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view orgs through org membership" ON public.orgs FOR SELECT TO authenticated USING (public.user_belongs_to_org(id));


--
-- Name: sessions Users can view sessions through org membership; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view sessions through org membership" ON public.sessions FOR SELECT USING (((project_id IN ( SELECT public.user_projects() AS user_projects)) OR (project_id_secondary IN ( SELECT public.user_projects() AS user_projects))));


--
-- Name: stats Users can view stats through org membership; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view stats through org membership" ON public.stats FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.sessions
  WHERE (sessions.id = stats.session_id))));


--
-- Name: users Users can view their own row in users; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view their own row in users" ON public.users FOR SELECT TO authenticated USING ((id = ( SELECT auth.uid() AS uid)));


--
-- Name: threads Users can view threads through org membership; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view threads through org membership" ON public.threads FOR SELECT TO authenticated USING ((( SELECT auth.uid() AS uid) IN ( SELECT user_orgs.user_id
   FROM ((public.user_orgs
     JOIN public.projects ON ((user_orgs.org_id = projects.org_id)))
     JOIN public.sessions ON (((projects.id = sessions.project_id) OR (projects.id = sessions.project_id_secondary))))
  WHERE (sessions.id = threads.session_id))));


--
-- Name: tools Users can view tools through org membership; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Users can view tools through org membership" ON public.tools FOR SELECT TO authenticated USING ((( SELECT auth.uid() AS uid) IN ( SELECT user_orgs.user_id
   FROM ((public.user_orgs
     JOIN public.projects ON ((user_orgs.org_id = projects.org_id)))
     JOIN public.sessions ON (((projects.id = sessions.project_id) OR (projects.id = sessions.project_id_secondary))))
  WHERE (sessions.id = tools.session_id))));


--
-- Name: actions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.actions ENABLE ROW LEVEL SECURITY;

--
-- Name: agents; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.agents ENABLE ROW LEVEL SECURITY;

--
-- Name: ai_gateway_admissions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.ai_gateway_admissions ENABLE ROW LEVEL SECURITY;

--
-- Name: ai_gateway_key_allowances; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.ai_gateway_key_allowances ENABLE ROW LEVEL SECURITY;

--
-- Name: ai_gateway_key_projects; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.ai_gateway_key_projects ENABLE ROW LEVEL SECURITY;

--
-- Name: ai_gateway_key_requests; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.ai_gateway_key_requests ENABLE ROW LEVEL SECURITY;

--
-- Name: billing_audit_logs; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.billing_audit_logs ENABLE ROW LEVEL SECURITY;

--
-- Name: billing_periods; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.billing_periods ENABLE ROW LEVEL SECURITY;

--
-- Name: customers; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.customers ENABLE ROW LEVEL SECURITY;

--
-- Name: developer_errors; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.developer_errors ENABLE ROW LEVEL SECURITY;

--
-- Name: errors; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.errors ENABLE ROW LEVEL SECURITY;

--
-- Name: llm_credential_refs; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.llm_credential_refs ENABLE ROW LEVEL SECURITY;

--
-- Name: llm_gateway_instances; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.llm_gateway_instances ENABLE ROW LEVEL SECURITY;

--
-- Name: llm_key_operations; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.llm_key_operations ENABLE ROW LEVEL SECURITY;

--
-- Name: llm_member_rollout; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.llm_member_rollout ENABLE ROW LEVEL SECURITY;

--
-- Name: llms; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.llms ENABLE ROW LEVEL SECURITY;

--
-- Name: org_invites; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.org_invites ENABLE ROW LEVEL SECURITY;

--
-- Name: orgs; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.orgs ENABLE ROW LEVEL SECURITY;

--
-- Name: prices; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.prices ENABLE ROW LEVEL SECURITY;

--
-- Name: products; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;

--
-- Name: project_agents_file_versions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.project_agents_file_versions ENABLE ROW LEVEL SECURITY;

--
-- Name: project_agents_files; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.project_agents_files ENABLE ROW LEVEL SECURITY;

--
-- Name: project_context_tokens; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.project_context_tokens ENABLE ROW LEVEL SECURITY;

--
-- Name: project_conversation_record_attempts; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.project_conversation_record_attempts ENABLE ROW LEVEL SECURITY;

--
-- Name: project_conversation_records; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.project_conversation_records ENABLE ROW LEVEL SECURITY;

--
-- Name: projects; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

--
-- Name: sessions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;

--
-- Name: stats; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.stats ENABLE ROW LEVEL SECURITY;

--
-- Name: subscriptions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

--
-- Name: threads; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.threads ENABLE ROW LEVEL SECURITY;

--
-- Name: tools; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.tools ENABLE ROW LEVEL SECURITY;

--
-- Name: ttd; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.ttd ENABLE ROW LEVEL SECURITY;

--
-- Name: user_orgs; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_orgs ENABLE ROW LEVEL SECURITY;

--
-- Name: users; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

--
-- Name: webhook_events; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.webhook_events ENABLE ROW LEVEL SECURITY;

--
-- Name: messages; Type: ROW SECURITY; Schema: realtime; Owner: -
--

ALTER TABLE realtime.messages ENABLE ROW LEVEL SECURITY;

--
-- Name: objects Give users access to own blobs related to their sessions; Type: POLICY; Schema: storage; Owner: -
--

CREATE POLICY "Give users access to own blobs related to their sessions" ON storage.objects FOR SELECT TO authenticated USING (((bucket_id = 'blobs'::text) AND (( SELECT auth.uid() AS uid) IN ( SELECT user_orgs.user_id
   FROM ((public.user_orgs
     JOIN public.projects ON ((user_orgs.org_id = projects.org_id)))
     JOIN public.sessions ON (((projects.id = sessions.project_id) OR (projects.id = sessions.project_id_secondary))))
  WHERE (sessions.id = ((storage.foldername(projects.name))[1])::uuid)))));


--
-- Name: objects Give users access to own images related to their sessions; Type: POLICY; Schema: storage; Owner: -
--

CREATE POLICY "Give users access to own images related to their sessions" ON storage.objects FOR SELECT TO authenticated USING (((bucket_id = 'screenshots'::text) AND (( SELECT auth.uid() AS uid) IN ( SELECT user_orgs.user_id
   FROM ((public.user_orgs
     JOIN public.projects ON ((user_orgs.org_id = projects.org_id)))
     JOIN public.sessions ON (((projects.id = sessions.project_id) OR (projects.id = sessions.project_id_secondary))))
  WHERE (sessions.id = ((storage.foldername(projects.name))[1])::uuid)))));


--
-- Name: buckets; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.buckets ENABLE ROW LEVEL SECURITY;

--
-- Name: buckets_analytics; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.buckets_analytics ENABLE ROW LEVEL SECURITY;

--
-- Name: buckets_vectors; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.buckets_vectors ENABLE ROW LEVEL SECURITY;

--
-- Name: iceberg_namespaces; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.iceberg_namespaces ENABLE ROW LEVEL SECURITY;

--
-- Name: iceberg_tables; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.iceberg_tables ENABLE ROW LEVEL SECURITY;

--
-- Name: migrations; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.migrations ENABLE ROW LEVEL SECURITY;

--
-- Name: objects; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

--
-- Name: s3_multipart_uploads; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.s3_multipart_uploads ENABLE ROW LEVEL SECURITY;

--
-- Name: s3_multipart_uploads_parts; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.s3_multipart_uploads_parts ENABLE ROW LEVEL SECURITY;

--
-- Name: vector_indexes; Type: ROW SECURITY; Schema: storage; Owner: -
--

ALTER TABLE storage.vector_indexes ENABLE ROW LEVEL SECURITY;

--
-- Name: supabase_realtime; Type: PUBLICATION; Schema: -; Owner: -
--

CREATE PUBLICATION supabase_realtime WITH (publish = 'insert, update, delete, truncate');


--
-- Name: issue_graphql_placeholder; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER issue_graphql_placeholder ON sql_drop
         WHEN TAG IN ('DROP EXTENSION')
   EXECUTE FUNCTION extensions.set_graphql_placeholder();


--
-- Name: issue_pg_cron_access; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER issue_pg_cron_access ON ddl_command_end
         WHEN TAG IN ('CREATE EXTENSION')
   EXECUTE FUNCTION extensions.grant_pg_cron_access();


--
-- Name: issue_pg_graphql_access; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER issue_pg_graphql_access ON ddl_command_end
         WHEN TAG IN ('CREATE FUNCTION')
   EXECUTE FUNCTION extensions.grant_pg_graphql_access();


--
-- Name: issue_pg_net_access; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER issue_pg_net_access ON ddl_command_end
         WHEN TAG IN ('CREATE EXTENSION')
   EXECUTE FUNCTION extensions.grant_pg_net_access();


--
-- Name: pgrst_ddl_watch; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER pgrst_ddl_watch ON ddl_command_end
   EXECUTE FUNCTION extensions.pgrst_ddl_watch();


--
-- Name: pgrst_drop_watch; Type: EVENT TRIGGER; Schema: -; Owner: -
--

CREATE EVENT TRIGGER pgrst_drop_watch ON sql_drop
   EXECUTE FUNCTION extensions.pgrst_drop_watch();


--
-- PostgreSQL database dump complete
--
