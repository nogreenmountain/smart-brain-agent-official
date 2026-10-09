\set ON_ERROR_STOP on
\getenv supabase_db_password SUPABASE_DB_PASSWORD
\getenv database_name POSTGRES_DB

CREATE SCHEMA IF NOT EXISTS extensions;

-- This file is intentionally psql-specific. Role creation uses \gexec so the
-- script is idempotent, while :'supabase_db_password' keeps the runtime secret
-- out of source control and quotes it as a SQL literal.
SELECT 'CREATE ROLE anon NOLOGIN INHERIT'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') \gexec
SELECT 'CREATE ROLE authenticated NOLOGIN INHERIT'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') \gexec
SELECT 'CREATE ROLE service_role NOLOGIN INHERIT BYPASSRLS'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') \gexec
SELECT 'CREATE ROLE authenticator LOGIN NOINHERIT'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticator') \gexec
SELECT 'CREATE ROLE supabase_auth_admin LOGIN NOINHERIT CREATEROLE NOREPLICATION'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'supabase_auth_admin') \gexec
SELECT 'CREATE ROLE supabase_storage_admin LOGIN NOINHERIT CREATEROLE NOREPLICATION'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'supabase_storage_admin') \gexec
SELECT 'CREATE ROLE supabase_admin LOGIN SUPERUSER INHERIT CREATEDB CREATEROLE REPLICATION BYPASSRLS'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'supabase_admin') \gexec

ALTER ROLE anon NOLOGIN INHERIT;
ALTER ROLE authenticated NOLOGIN INHERIT;
ALTER ROLE service_role NOLOGIN INHERIT BYPASSRLS;
ALTER ROLE authenticator LOGIN NOINHERIT PASSWORD :'supabase_db_password';
ALTER ROLE supabase_auth_admin LOGIN NOINHERIT CREATEROLE NOREPLICATION
  PASSWORD :'supabase_db_password';
ALTER ROLE supabase_storage_admin LOGIN NOINHERIT CREATEROLE NOREPLICATION
  PASSWORD :'supabase_db_password';
ALTER ROLE supabase_admin LOGIN SUPERUSER INHERIT CREATEDB CREATEROLE
  REPLICATION BYPASSRLS;

GRANT anon, authenticated, service_role TO authenticator;
GRANT authenticator TO supabase_storage_admin;
GRANT CONNECT, CREATE, TEMPORARY ON DATABASE :"database_name"
  TO supabase_auth_admin, supabase_storage_admin;
GRANT USAGE ON SCHEMA public, extensions
  TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT ALL ON TABLES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT ALL ON FUNCTIONS TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT ALL ON SEQUENCES TO anon, authenticated, service_role;
ALTER ROLE supabase_auth_admin SET search_path = auth;
ALTER ROLE supabase_storage_admin SET search_path = storage;
ALTER ROLE anon SET statement_timeout = '3s';
ALTER ROLE authenticated SET statement_timeout = '8s';

-- pg_dump --no-owner deliberately makes restored objects belong to the target
-- administrator. Re-home only the two Supabase-owned schemas after restore so
-- GoTrue and Storage API can continue to run their own migrations.
SELECT 'ALTER SCHEMA auth OWNER TO supabase_auth_admin'
WHERE EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'auth') \gexec
SELECT 'ALTER SCHEMA storage OWNER TO supabase_storage_admin'
WHERE EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'storage') \gexec

SELECT format(
  'ALTER %s %I.%I OWNER TO %I',
  CASE c.relkind
    WHEN 'S' THEN 'SEQUENCE'
    WHEN 'v' THEN 'VIEW'
    WHEN 'm' THEN 'MATERIALIZED VIEW'
    WHEN 'f' THEN 'FOREIGN TABLE'
    ELSE 'TABLE'
  END,
  n.nspname,
  c.relname,
  CASE n.nspname
    WHEN 'auth' THEN 'supabase_auth_admin'
    ELSE 'supabase_storage_admin'
  END
)
FROM pg_class AS c
JOIN pg_namespace AS n ON n.oid = c.relnamespace
WHERE n.nspname IN ('auth', 'storage')
  AND c.relkind IN ('r', 'p', 'S', 'v', 'm', 'f')
ORDER BY n.nspname, c.relname \gexec

SELECT format(
  'ALTER %s %I.%I(%s) OWNER TO %I',
  CASE p.prokind
    WHEN 'p' THEN 'PROCEDURE'
    WHEN 'a' THEN 'AGGREGATE'
    ELSE 'FUNCTION'
  END,
  n.nspname,
  p.proname,
  pg_get_function_identity_arguments(p.oid),
  CASE n.nspname
    WHEN 'auth' THEN 'supabase_auth_admin'
    ELSE 'supabase_storage_admin'
  END
)
FROM pg_proc AS p
JOIN pg_namespace AS n ON n.oid = p.pronamespace
WHERE n.nspname IN ('auth', 'storage')
  AND p.prokind IN ('f', 'p', 'a', 'w')
ORDER BY n.nspname, p.proname, p.oid \gexec

SELECT format(
  'ALTER TYPE %I.%I OWNER TO %I',
  n.nspname,
  t.typname,
  CASE n.nspname
    WHEN 'auth' THEN 'supabase_auth_admin'
    ELSE 'supabase_storage_admin'
  END
)
FROM pg_type AS t
JOIN pg_namespace AS n ON n.oid = t.typnamespace
WHERE n.nspname IN ('auth', 'storage')
  AND t.typrelid = 0
  AND t.typtype IN ('d', 'e', 'm', 'r')
ORDER BY n.nspname, t.typname \gexec

SELECT format(
  'GRANT ALL ON SCHEMA %I TO %I',
  nspname,
  CASE nspname
    WHEN 'auth' THEN 'supabase_auth_admin'
    ELSE 'supabase_storage_admin'
  END
)
FROM pg_namespace
WHERE nspname IN ('auth', 'storage') \gexec

SELECT format(
  'GRANT ALL ON ALL TABLES IN SCHEMA %I TO %I',
  nspname,
  CASE nspname
    WHEN 'auth' THEN 'supabase_auth_admin'
    ELSE 'supabase_storage_admin'
  END
)
FROM pg_namespace
WHERE nspname IN ('auth', 'storage') \gexec

SELECT format(
  'GRANT ALL ON ALL SEQUENCES IN SCHEMA %I TO %I',
  nspname,
  CASE nspname
    WHEN 'auth' THEN 'supabase_auth_admin'
    ELSE 'supabase_storage_admin'
  END
)
FROM pg_namespace
WHERE nspname IN ('auth', 'storage') \gexec

SELECT format(
  'GRANT ALL ON ALL ROUTINES IN SCHEMA %I TO %I',
  nspname,
  CASE nspname
    WHEN 'auth' THEN 'supabase_auth_admin'
    ELSE 'supabase_storage_admin'
  END
)
FROM pg_namespace
WHERE nspname IN ('auth', 'storage') \gexec

DO $$
DECLARE
  required_count integer;
BEGIN
  SELECT count(*)
    INTO required_count
    FROM pg_roles
   WHERE rolname IN (
     'anon', 'authenticated', 'service_role', 'authenticator',
     'supabase_admin', 'supabase_auth_admin', 'supabase_storage_admin'
   );

  IF required_count <> 7
     OR NOT EXISTS (
       SELECT 1 FROM pg_roles
        WHERE rolname = 'anon' AND NOT rolcanlogin AND rolinherit
     )
     OR NOT EXISTS (
       SELECT 1 FROM pg_roles
        WHERE rolname = 'authenticated' AND NOT rolcanlogin AND rolinherit
     )
     OR NOT EXISTS (
       SELECT 1 FROM pg_roles
        WHERE rolname = 'service_role' AND NOT rolcanlogin AND rolinherit AND rolbypassrls
     )
     OR NOT EXISTS (
       SELECT 1 FROM pg_roles
        WHERE rolname = 'authenticator' AND rolcanlogin AND NOT rolinherit
     )
     OR NOT EXISTS (
       SELECT 1 FROM pg_roles
        WHERE rolname = 'supabase_auth_admin' AND rolcanlogin AND rolcreaterole
     )
     OR NOT EXISTS (
       SELECT 1 FROM pg_roles
        WHERE rolname = 'supabase_storage_admin' AND rolcanlogin AND rolcreaterole
     )
     OR NOT EXISTS (
       SELECT 1 FROM pg_roles
        WHERE rolname = 'supabase_admin' AND rolcanlogin AND rolsuper
          AND rolcreatedb AND rolcreaterole AND rolreplication AND rolbypassrls
     )
     OR NOT pg_has_role('authenticator', 'anon', 'MEMBER')
     OR NOT pg_has_role('authenticator', 'authenticated', 'MEMBER')
     OR NOT pg_has_role('authenticator', 'service_role', 'MEMBER')
     OR NOT pg_has_role('supabase_storage_admin', 'authenticator', 'MEMBER')
     OR NOT has_database_privilege('supabase_auth_admin', current_database(), 'CREATE')
     OR NOT has_database_privilege('supabase_storage_admin', current_database(), 'CREATE') THEN
    RAISE EXCEPTION 'Supabase role contract is incomplete';
  END IF;
END
$$;

SELECT 'supabase_role_contract_ok';
