#!/usr/bin/env bash
set -Eeuo pipefail

: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${SUPABASE_DB_PASSWORD:?SUPABASE_DB_PASSWORD is required}"

PSQL_ARGS=(--username "$POSTGRES_USER" --dbname "$POSTGRES_DB")
if [[ "${SMARTBRAIN_ROLE_BOOTSTRAP_REMOTE:-false}" == true ]]; then
  : "${POSTGRES_HOST:?POSTGRES_HOST is required for a remote bootstrap}"
  PSQL_ARGS+=(--host "$POSTGRES_HOST" --port "${POSTGRES_PORT:-5432}")
  export PGPASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}"
  export PGSSLMODE="${POSTGRES_SSLMODE:-require}"
fi

ROLE_SQL="/opt/smartbrain/postgres/supabase-roles.sql"
if [[ ! -r "$ROLE_SQL" ]]; then
  ROLE_SQL="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/supabase-roles.sql"
fi

psql "${PSQL_ARGS[@]}" \
  --set=ON_ERROR_STOP=1 \
  --file="$ROLE_SQL"

if [[ "${SMARTBRAIN_ROLE_BOOTSTRAP_REMOTE:-false}" != true ]]; then
  : "${PGDATA:?PGDATA is required for the local init completion marker}"
  touch "$PGDATA/.smartbrain-init-complete"
  chmod 0600 "$PGDATA/.smartbrain-init-complete"
fi
