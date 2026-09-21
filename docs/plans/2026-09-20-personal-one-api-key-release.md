# Phase 6 — one-user/one-API-key release plan

## Authorization and scope

- Authorization: explicit user authorization in the 2026-09-20 task thread.
- Scope: promote the archived personal LLM key-management candidate into the authoritative source, validate the one-user/one-key lifecycle, and release through a reversible production change.
- Production transport: SSH alias `smartbrain-prod` (read-only inventory first).
- Production application: existing API and dashboard services only; no employee model traffic changes until the release gates pass.
- Isolated validation: Compose project `smartbrain-llm-pilot` under `/srv/smartbrain-llm-pilot`; never treat it as production.
- Forbidden in this release: GPT-6 real requests, reuse of the failed G1-R3 real-upstream authorization, project-key rebinding, Monitor revival, or deletion of historical key mappings.

## Phase 1 — candidate promotion and local regression

- Source: the 16-file candidate in `.artifacts/gateway-management-20260915-r1`.
- Promote only the candidate backend, migration, dashboard API/UI, and tests; preserve unrelated working-tree changes.
- Verify source hashes against `source-manifest-final.json`.
- Run Python unit tests, targeted route tests, TypeScript tests/typecheck, and `py_compile`.
- Confirm one active credential per user, server-owned credential mapping, idempotent create, pending-operation recovery, cross-user denial, and revoke/remove history retention.

## Phase 2 — isolated PostgreSQL and HTTP gate

- Use only the named isolated test database and gateway replacement.
- Apply the candidate migration there, run the PostgreSQL and HTTP route suites, and verify RLS, quota reservation, idempotency, SIGKILL recovery, and disabled/ban boundaries.
- No production DDL, Key mutation, model request, or service restart.

## Phase 3 — production read-only inventory and release preparation

- Resolve the exact production API/frontend containers, image IDs, mounted source hashes, active routes, and backup/rollback state.
- Build immutable API/frontend artifacts from the promoted source.
- Prepare a migration and rollout manifest with pre-change hashes, health checks, and an explicit rollback command.

## Phase 4 — controlled production release

- Take the required backup/maintenance locks and apply only the one-user/one-key migration.
- Deploy API and dashboard artifacts, verify health and authenticated key-management flows, and run a narrow gray check.
- Stop immediately on migration, auth, quota, route, or health failure; restore the prior artifacts and database state according to the manifest.
- Do not claim release success until the post-change read-only inventory and user-facing checks match the manifest.

## Acceptance criteria

1. Each active user has at most one active personal API key; duplicate create is idempotent or rejected without issuing a second secret.
2. Key ownership is derived server-side; cross-user list/revoke/use attempts are denied.
3. Revoke/remove persists before native gateway mutation; uncertain operations remain visible and recoverable.
4. Disabled/banned users cannot self-manage keys; authorized system-admin path remains separate.
5. Historical mappings and records remain readable after revoke/remove.
6. Production API/frontend health and rollback checks pass; no unrelated service or traffic changes occur.

## Risks and blockers

- The candidate is archived rather than currently present in the authoritative source; promotion must be reviewed by hash before any deployment.
- Production migration and release require a fresh read-only inventory because the 2026-09-15 candidate was explicitly marked `production_release=false`.
- Real upstream qualification remains separate: G1 stays incomplete and no real model request is authorized by this release plan.
